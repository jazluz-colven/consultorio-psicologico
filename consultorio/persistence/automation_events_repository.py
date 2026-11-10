"""Data access for automation events; no business rules live here (HU-007).

Spec 019 (T5, plan D8/D13): the SQL uses ``%s`` placeholders and the same
minimal SQLite adapter as the appointments repository, so there is a single
statement set for PostgreSQL and the temporary SQLite rollback route. The
public names and return contracts are unchanged; the last parameter accepts a
``Database``/``DatabaseTarget`` or, transitionally, a legacy ``database_path``.
"""

import sqlite3
from contextlib import contextmanager
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterator, Mapping

from consultorio.persistence.database import (
    Database,
    DatabaseTarget,
    get_connection,
)

DatabaseResource = Database | DatabaseTarget | str | Path

# UTC expression for ``sent_at`` (plan D7, RF-30). PostgreSQL keeps the
# approved ``to_char`` expression; SQLite rollback uses ``datetime('now')``,
# which is UTC and produces the same ``YYYY-MM-DD HH:MM:SS`` format. Only this
# expression differs by dialect; the rest of the statement is shared.
_SENT_AT_EXPRESSION = {
    "postgres": "to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS')",
    "sqlite": "datetime('now')",
}


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


def _database_for(resource: DatabaseResource) -> tuple[Database | None, bool]:
    """Return ``(database, owned)`` for a migrated resource.

    ``owned`` is ``True`` only when this repository created the ``Database``
    from a ``DatabaseTarget``. Such a temporary instance has no owner that will
    call ``close_request()`` at app-context teardown, so ``_scope`` closes it
    itself. A ``Database`` supplied by the caller is never closed here.
    """
    if isinstance(resource, Database):
        return resource, False
    if isinstance(resource, DatabaseTarget):
        return Database(resource), True
    return None, False


def _backend_of(resource: DatabaseResource) -> str:
    if isinstance(resource, Database):
        return resource.target.backend
    if isinstance(resource, DatabaseTarget):
        return resource.backend
    return "sqlite"


def _adapt_sqlite_sql(query: str) -> str:
    """Minimal rollback adapter (plan D8): ``%s`` -> ``?`` only.

    The statements are controlled by this module: literals never contain ``?``
    and ``%`` only appears in the ``%s`` placeholders, so a plain replacement is
    safe. This is deliberately not a general SQL translator.
    """
    return query.replace("%s", "?")


@contextmanager
def _scope(
    resource: DatabaseResource, *, write: bool
) -> Iterator[tuple[Any, str]]:
    """Yield ``(connection, backend)`` for either persistence resource.

    When the repository created the ``Database`` from a ``DatabaseTarget``, it
    closes that temporary instance with ``close_request()`` on every exit path,
    including exceptions. A ``Database`` supplied by the caller is left
    untouched (its owner/teardown closes it).
    """
    database, owned = _database_for(resource)
    if database is not None:
        try:
            database.ensure_schema()
            backend = database.target.backend
            manager = database.transaction() if write else database.connection()
            with manager as connection:
                yield connection, backend
        finally:
            if owned:
                database.close_request()
        return
    with get_connection(resource) as connection:
        yield connection, "sqlite"


def _run(
    connection: Any,
    backend: str,
    query: str,
    params: tuple[object, ...] = (),
) -> Any:
    if backend == "sqlite":
        query = _adapt_sqlite_sql(query)
    return connection.execute(query, params)


def _is_unique_violation(error: BaseException, backend: str) -> bool:
    """True only for the engine's unique-id violation on ``insert_event``.

    PostgreSQL: exactly ``psycopg.errors.UniqueViolation`` (imported lazily so
    the SQLite route never needs the driver). SQLite keeps the historical
    ``sqlite3.IntegrityError``. Other errors are not translated or silenced.
    """
    if backend == "sqlite":
        return isinstance(error, sqlite3.IntegrityError)
    if backend == "postgres":
        try:
            from psycopg import errors as pg_errors
        except ImportError:  # pragma: no cover - depends on local libpq
            return False
        return isinstance(error, pg_errors.UniqueViolation)
    return False


def insert_event(
    event_id: str,
    event_type: str,
    event_version: int,
    appointment_id: int,
    database: DatabaseResource,
) -> bool:
    """Register a pending event; False when event_id already exists (RF-5)."""
    backend = _backend_of(database)
    try:
        with _scope(database, write=True) as (connection, conn_backend):
            _run(
                connection,
                conn_backend,
                """
                INSERT INTO automation_events (
                    event_id, event_type, event_version, appointment_id, status
                ) VALUES (%s, %s, %s, %s, 'pending')
                """,
                (event_id, event_type, event_version, appointment_id),
            )
    except Exception as error:
        if _is_unique_violation(error, backend):
            return False
        raise
    return True


def get_by_event_id(
    event_id: str, database: DatabaseResource
) -> AutomationEvent | None:
    with _scope(database, write=False) as (connection, backend):
        row = _run(
            connection,
            backend,
            "SELECT * FROM automation_events WHERE event_id = %s",
            (event_id,),
        ).fetchone()
    return _to_event(row) if row is not None else None


def mark_sent(event_id: str, database: DatabaseResource) -> None:
    with _scope(database, write=True) as (connection, backend):
        _run(
            connection,
            backend,
            f"""
            UPDATE automation_events
            SET status = 'sent', detail = NULL,
                sent_at = {_SENT_AT_EXPRESSION[backend]}
            WHERE event_id = %s
            """,
            (event_id,),
        )


def mark_skipped(
    event_id: str, detail: str, database: DatabaseResource
) -> None:
    with _scope(database, write=True) as (connection, backend):
        _run(
            connection,
            backend,
            """
            UPDATE automation_events SET status = 'skipped', detail = %s
            WHERE event_id = %s
            """,
            (detail, event_id),
        )


def mark_failed(
    event_id: str, detail: str, database: DatabaseResource
) -> None:
    with _scope(database, write=True) as (connection, backend):
        _run(
            connection,
            backend,
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

    with _scope(database, write=True) as (connection, backend):
        cursor = _run(connection, backend, query, tuple(params))
        return cursor.rowcount == 1
