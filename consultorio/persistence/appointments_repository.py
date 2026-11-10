"""Data access for appointments; no business rules live here.

Spec 019 (T5, plan D8/D13): the SQL is written in the PostgreSQL dialect
(``%s`` placeholders, ``INSERT ... RETURNING id``, ``rowcount`` and named row
access). The same statements run on the SQLite rollback route through a
minimal, project-controlled adapter that replaces ``%s`` with ``?``; there is
no general SQL translator and no duplicated second query set.

The public function names and return contracts are unchanged. The last
parameter accepts a ``Database``/``DatabaseTarget`` (the target of the
migration) or, transitionally, a legacy ``database_path`` while the services
and the rest of the suite are migrated in T6/T10 (plan D13).
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


@dataclass(frozen=True)
class Appointment:
    id: int
    document_type: str
    document_number: str
    patient_name: str
    email: str
    phone: str
    service: str
    date: str
    time: str
    status: str
    created_at: str


def _to_appointment(row: Mapping[str, Any]) -> Appointment:
    return Appointment(
        id=row["id"],
        document_type=row["document_type"],
        document_number=row["document_number"],
        patient_name=row["patient_name"],
        email=row["email"],
        phone=row["phone"],
        service=row["service"],
        date=row["date"],
        time=row["time"],
        status=row["status"],
        created_at=row["created_at"],
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

    ``Database``/``DatabaseTarget`` use the facade (lazy schema, request-scoped
    connection, one commit or full rollback). A legacy path keeps the original
    ``get_connection`` behaviour for the SQLite rollback route.

    When the repository created the ``Database`` from a ``DatabaseTarget``, it
    closes that temporary instance with ``close_request()`` on every exit path,
    including exceptions. Inside a Flask app context ``connection()`` and
    ``transaction()`` keep the connection for app-context teardown, which would
    otherwise never run for an instance the app does not own. A ``Database``
    supplied by the caller is left untouched (its owner/teardown closes it).
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


def _fetch_appointment(
    connection: Any, backend: str, appointment_id: int
) -> Appointment | None:
    row = _run(
        connection,
        backend,
        "SELECT * FROM appointments WHERE id = %s",
        (appointment_id,),
    ).fetchone()
    return _to_appointment(row) if row is not None else None


def insert_appointment(
    data: dict[str, str], database: DatabaseResource
) -> Appointment:
    with _scope(database, write=True) as (connection, backend):
        row = _run(
            connection,
            backend,
            """
            INSERT INTO appointments (
                document_type, document_number, patient_name, email, phone,
                service, date, time, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'confirmed')
            RETURNING id
            """,
            (
                data["document_type"],
                data["document_number"],
                data["patient_name"],
                data["email"],
                data["phone"],
                data["service"],
                data["date"],
                data["time"],
            ),
        ).fetchone()
        appointment_id = int(row["id"])
        created = _fetch_appointment(connection, backend, appointment_id)
    if created is None:  # pragma: no cover - defensive
        raise RuntimeError("Appointment inserted but not found.")
    return created


def get_appointment_by_id(
    appointment_id: int, database: DatabaseResource
) -> Appointment | None:
    with _scope(database, write=False) as (connection, backend):
        return _fetch_appointment(connection, backend, appointment_id)


def is_slot_taken(
    service: str, date: str, time: str, database: DatabaseResource
) -> bool:
    with _scope(database, write=False) as (connection, backend):
        row = _run(
            connection,
            backend,
            """
            SELECT 1 FROM appointments
            WHERE service = %s AND date = %s AND time = %s
              AND status <> 'cancelled'
            """,
            (service, date, time),
        ).fetchone()
    return row is not None


def list_booked_times(
    service: str, date: str, database: DatabaseResource
) -> list[str]:
    with _scope(database, write=False) as (connection, backend):
        rows = _run(
            connection,
            backend,
            """
            SELECT time FROM appointments
            WHERE service = %s AND date = %s AND status <> 'cancelled'
            ORDER BY time
            """,
            (service, date),
        ).fetchall()
    return [row["time"] for row in rows]


def list_booked_times_by_date(
    service: str,
    date_from: str,
    date_to: str,
    database: DatabaseResource,
) -> dict[str, list[str]]:
    with _scope(database, write=False) as (connection, backend):
        rows = _run(
            connection,
            backend,
            """
            SELECT date, time FROM appointments
            WHERE service = %s AND date >= %s AND date <= %s
              AND status <> 'cancelled'
            ORDER BY date, time
            """,
            (service, date_from, date_to),
        ).fetchall()
    booked: dict[str, list[str]] = {}
    for row in rows:
        booked.setdefault(row["date"], []).append(row["time"])
    return booked


def update_appointment_status(
    appointment_id: int, new_status: str, database: DatabaseResource
) -> Appointment | None:
    """Atomically move an appointment out of 'confirmed' (HU-010).

    Returns the updated appointment, or None when the row does not exist or is
    not 'confirmed' (already cancelled or unknown id) — RF-4/CL-1/CL-4.
    """
    with _scope(database, write=True) as (connection, backend):
        cursor = _run(
            connection,
            backend,
            """
            UPDATE appointments SET status = %s
            WHERE id = %s AND status = 'confirmed'
            """,
            (new_status, appointment_id),
        )
        if cursor.rowcount == 0:
            connection.rollback()
            return None
    return get_appointment_by_id(appointment_id, database)


def update_appointment_status_with_pending_event(
    appointment_id: int,
    new_status: str,
    event_id: str,
    event_type: str,
    event_version: int,
    database: DatabaseResource,
) -> Appointment | None:
    """Cancel the appointment and register its pending automation event in the
    SAME connection/transaction (spec 010 RF-11/RF-12, F2-D11; plan D5).

    «Sin traza local, sin cancelación confirmada»: the status transition and
    the `pending` event row are committed together, or not at all.

    Returns the updated appointment, or None when the row does not exist or is
    not 'confirmed' (no event is registered in that case). If the event INSERT
    fails, the whole transaction is rolled back — the appointment is NOT
    cancelled — and the error propagates (RF-12).
    """
    with _scope(database, write=True) as (connection, backend):
        cursor = _run(
            connection,
            backend,
            """
            UPDATE appointments SET status = %s
            WHERE id = %s AND status = 'confirmed'
            """,
            (new_status, appointment_id),
        )
        if cursor.rowcount == 0:
            # inexistente o ya cancelada: rollback y sin registro de evento
            connection.rollback()
            return None
        _run(
            connection,
            backend,
            """
            INSERT INTO automation_events (
                event_id, event_type, event_version, appointment_id, status
            ) VALUES (%s, %s, %s, %s, 'pending')
            """,
            (event_id, event_type, event_version, appointment_id),
        )
        # Commit conjunto al salir del contexto: o ambas confirmadas o ninguna.
        # Un fallo del INSERT revierte TODO y propaga (RF-12); la publicación
        # (POST) ocurre después del commit, fuera de esta transacción (RF-11).
    return get_appointment_by_id(appointment_id, database)
