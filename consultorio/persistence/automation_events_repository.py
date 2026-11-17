"""Data access for automation events; no business rules live here (HU-007).

Spec 019 (T5/T18, plan D8/D13): the SQL uses ``%s`` placeholders on PostgreSQL,
which is the only persistence engine. The public names and return contracts are
unchanged; the last parameter accepts a ``Database`` or a ``DatabaseTarget``.
"""

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator, Mapping

from consultorio.persistence.database import Database, DatabaseTarget

DatabaseResource = Database | DatabaseTarget

# UTC expression for ``sent_at`` (plan D7, RF-30).
_SENT_AT_EXPRESSION = (
    "to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS')"
)


@dataclass(frozen=True)
class AutomationEvent:
    id: int
    event_id: str
    event_type: str
    event_version: int
    appointment_id: int
    status: str
    detail: str | None
    created_at: str
    sent_at: str | None


def _to_event(row: Mapping[str, Any]) -> AutomationEvent:
    return AutomationEvent(
        id=row["id"],
        event_id=row["event_id"],
        event_type=row["event_type"],
        event_version=row["event_version"],
        appointment_id=row["appointment_id"],
        status=row["status"],
        detail=row["detail"],
        created_at=row["created_at"],
        sent_at=row["sent_at"],
    )


def _database_for(resource: DatabaseResource) -> tuple[Database, bool]:
    """Return ``(database, owned)`` for a migrated resource.

    ``owned`` is ``True`` only when this repository created the ``Database``
    from a ``DatabaseTarget``. Such a temporary instance has no owner that will
    call ``close_request()`` at app-context teardown, so ``_scope`` closes it
    itself. A ``Database`` supplied by the caller is never closed here.
    """
    if isinstance(resource, Database):
        return resource, False
    return Database(resource), True


@contextmanager
def _scope(resource: DatabaseResource, *, write: bool) -> Iterator[Any]:
    """Yield a connection from the ``Database`` facade.

    When the repository created the ``Database`` from a ``DatabaseTarget``, it
    closes that temporary instance with ``close_request()`` on every exit path,
    including exceptions. A ``Database`` supplied by the caller is left
    untouched (its owner/teardown closes it).
    """
    database, owned = _database_for(resource)
    try:
        database.ensure_schema()
        manager = database.transaction() if write else database.connection()
        with manager as connection:
            yield connection
    finally:
        if owned:
            database.close_request()


def _run(
    connection: Any,
    query: str,
    params: tuple[object, ...] = (),
) -> Any:
    return connection.execute(query, params)


def _is_unique_violation(error: BaseException) -> bool:
    """True only for the engine's unique-id violation on ``insert_event``.

    Exactly ``psycopg.errors.UniqueViolation`` (imported lazily). Other errors
    are not translated or silenced.
    """
    try:
        from psycopg import errors as pg_errors
    except ImportError:  # pragma: no cover - depends on local libpq
        return False
    return isinstance(error, pg_errors.UniqueViolation)


def insert_event(
    event_id: str,
    event_type: str,
    event_version: int,
    appointment_id: int,
    database: DatabaseResource,
) -> bool:
    """Register a pending event; False when event_id already exists (RF-5)."""
    try:
        with _scope(database, write=True) as connection:
            _run(
                connection,
                """
                INSERT INTO automation_events (
                    event_id, event_type, event_version, appointment_id, status
                ) VALUES (%s, %s, %s, %s, 'pending')
                """,
                (event_id, event_type, event_version, appointment_id),
            )
    except Exception as error:
        if _is_unique_violation(error):
            return False
        raise
    return True


def get_by_event_id(
    event_id: str, database: DatabaseResource
) -> AutomationEvent | None:
    with _scope(database, write=False) as connection:
        row = _run(
            connection,
            "SELECT * FROM automation_events WHERE event_id = %s",
            (event_id,),
        ).fetchone()
    return _to_event(row) if row is not None else None


def mark_sent(event_id: str, database: DatabaseResource) -> None:
    with _scope(database, write=True) as connection:
        _run(
            connection,
            f"""
            UPDATE automation_events
            SET status = 'sent', detail = NULL,
                sent_at = {_SENT_AT_EXPRESSION}
            WHERE event_id = %s
            """,
            (event_id,),
        )


def mark_skipped(
    event_id: str, detail: str, database: DatabaseResource
) -> None:
    with _scope(database, write=True) as connection:
        _run(
            connection,
            """
            UPDATE automation_events SET status = 'skipped', detail = %s
            WHERE event_id = %s
            """,
            (detail, event_id),
        )


def mark_failed(
    event_id: str, detail: str, database: DatabaseResource
) -> None:
    with _scope(database, write=True) as connection:
        _run(
            connection,
            """
            UPDATE automation_events SET status = 'failed', detail = %s
            WHERE event_id = %s
            """,
            (detail, event_id),
        )


def claim_failed_event(
    event_id: str,
    database: DatabaseResource,
    permanent_pattern: str | None = None,
    retryable_pattern: str | None = None,
) -> bool:
    """
    Atomically move an event from 'failed' to 'pending' for reprocessing.
    Only applies to 'appointment.cancelled' events.
    Returns True if the event was claimed, False otherwise.

    D-010-01 (DP-02): when both `LIKE` patterns are supplied, a `failed` event
    whose persisted `detail` is a PERMANENT HTTP rejection (4xx except 429) is
    excluded inside this same atomic `UPDATE` (no prior `SELECT`). The patterns
    are derived from the content literal and passed by the service, so the
    retryability policy does not live in the persistence layer. 5xx, 429,
    timeout, `URLError` and `NULL` details stay claimable. Omitting the patterns
    keeps the previous behaviour (claim any `failed` event).
    """
    query = """
        UPDATE automation_events
        SET status = 'pending', detail = NULL
        WHERE event_id = %s
          AND status = 'failed'
          AND event_type = 'appointment.cancelled'
    """
    params: list[object] = [event_id]
    if permanent_pattern is not None and retryable_pattern is not None:
        query += """
          AND (
            detail IS NULL
            OR detail NOT LIKE %s
            OR detail LIKE %s
          )
        """
        params.extend([permanent_pattern, retryable_pattern])

    with _scope(database, write=True) as connection:
        cursor = _run(connection, query, tuple(params))
        return cursor.rowcount == 1
