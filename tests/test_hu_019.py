"""Spec 019 (T5/T8/T12) integrity, concurrency, dedup and contractual literal.

* TC-019-011 — ``MSG_PERSISTENCE_UNAVAILABLE`` equals the approved literal and
  its mirror, without changing other Spec 004/005 literals (RF-20; RNF-5).
* TC-019-013 — direct duplicate insert in an active slot fails at the engine;
  after cancelling, the slot can be booked again; a confirmed slot remains
  blocked (RF-10, RF-11).
* TC-019-014 — eight real threads behind a ``threading.Barrier`` book the same
  ``service + date + time`` against PostgreSQL: exactly one persisted booking,
  seven ``SLOT_TAKEN`` results, no unhandled exception and no extra rows
  (RF-14; CL-8).
* TC-019-015 — event deduplication: the second ``insert_event`` returns
  ``False``, only one row exists and the stored event is not reset (no second
  send) (RF-12).

The SQLite test keeps the adapted repositories compatible with the temporary
rollback route (both the legacy ``database_path`` and the ``Database``
facade), without duplicating the whole existing suite. It is evidence of T5,
not of PostgreSQL parity.
"""

import threading
import time
from dataclasses import replace
from pathlib import Path

import psycopg
import psycopg.errors as pg_errors
import pytest

from consultorio.content import appointment_content
from consultorio.persistence import appointments_repository as appointments
from consultorio.persistence import automation_events_repository as events
from consultorio.persistence.appointments_repository import Appointment
from consultorio.persistence.database import (
    Database,
    DatabaseTarget,
    init_db,
)
from consultorio.services import appointment_service as booking
from tests import expected_content

VALID_DATA = {
    "document_type": "CC",
    "document_number": "1234567890",
    "patient_name": "Paciente de prueba",
    "email": "paciente@ejemplo.test",
    "phone": "3001234567",
    "service": "nutrition",
    "date": "2026-11-10",
    "time": "08:00",
}


@pytest.fixture()
def pg_database(pg_target: DatabaseTarget) -> Database:
    database = Database(pg_target)
    database.ensure_schema()
    return database


def _count(database: Database, table: str) -> int:
    with database.connection() as connection:
        row = connection.execute(
            f"SELECT count(*) AS total FROM {table}"
        ).fetchone()
    return int(row["total"])


def _direct_insert(database: Database, data: dict[str, str]) -> None:
    with database.transaction() as connection:
        connection.execute(
            """
            INSERT INTO appointments (
                document_type, document_number, patient_name, email, phone,
                service, date, time, status
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'confirmed')
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
        )


# ---------------------------------------------------------------------------
# TC-019-013 — slot integrity at the persistence point
# ---------------------------------------------------------------------------


def test_tc_019_013_slot_integrity_and_cancelled_release(
    pg_database: Database,
) -> None:
    created = appointments.insert_appointment(VALID_DATA, pg_database)

    # Direct duplicate in an active slot fails at the engine (partial index).
    with pytest.raises(pg_errors.UniqueViolation):
        _direct_insert(pg_database, VALID_DATA)
    assert _count(pg_database, "appointments") == 1

    # The confirmed slot remains blocked through the repository too.
    with pytest.raises(pg_errors.UniqueViolation):
        appointments.insert_appointment(VALID_DATA, pg_database)
    assert _count(pg_database, "appointments") == 1

    # Cancelling releases the combination, which can be booked again.
    cancelled = appointments.update_appointment_status(
        created.id, "cancelled", pg_database
    )
    assert cancelled is not None and cancelled.status == "cancelled"
    rebooked = appointments.insert_appointment(VALID_DATA, pg_database)
    assert rebooked.id != created.id
    assert appointments.is_slot_taken(
        "nutrition", "2026-11-10", "08:00", pg_database
    )
    assert _count(pg_database, "appointments") == 2


# ---------------------------------------------------------------------------
# TC-019-014 — eight concurrent bookings on the same slot (RF-14; CL-8)
# ---------------------------------------------------------------------------


def test_tc_019_014_eight_threads_one_booking_seven_slot_taken(
    database: Database,
    pg_target: DatabaseTarget,
    pg_schema: tuple[str, str],
) -> None:
    """RF-14/CL-8 with real PostgreSQL connections and a real ``Barrier``.

    Eight threads call ``create_booking()`` with the same ``service + date +
    time``. The partial unique index is the only arbiter: exactly one row is
    persisted and the other seven callers receive ``SLOT_TAKEN``. No thread may
    escape with an unhandled exception.

    Automation and e-mail are left disabled (empty webhook URL), so the winner
    produces the two real ``skipped`` event rows and the test uses no mock at
    all. Finally the isolated schema is dropped with the same statement the
    fixture executes, proving the cleanup path works; the fixture repeats it
    idempotently as a safety net.
    """
    concurrent_database = Database(
        replace(
            pg_target,
            max_connections=8,
            acquire_timeout=10.0,
        )
    )
    # The schema is created once, before the race, so the Barrier synchronises
    # the bookings themselves and not the bootstrap.
    concurrent_database.ensure_schema()

    data = {**VALID_DATA, "time": "10:00"}
    barrier = threading.Barrier(8)
    lock = threading.Lock()
    results: list[object] = []
    errors: list[BaseException] = []

    def worker() -> None:
        barrier.wait(timeout=10)
        try:
            result = booking.create_booking(data, concurrent_database)
        except BaseException as error:  # noqa: BLE001 - asserted below
            with lock:
                errors.append(error)
        else:
            with lock:
                results.append(result)

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert all(not thread.is_alive() for thread in threads)
    assert errors == []
    assert len(results) == 8
    assert sum(result == booking.SLOT_TAKEN for result in results) == 7
    winners = [result for result in results if isinstance(result, Appointment)]
    assert len(winners) == 1
    winner = winners[0]

    # Exactly one appointment row and no orphan event rows from losing races.
    assert _count(database, "appointments") == 1
    assert appointments.get_appointment_by_id(winner.id, database) == winner
    assert appointments.list_booked_times(
        data["service"], data["date"], database
    ) == [data["time"]]
    with database.connection() as connection:
        event_rows = connection.execute(
            "SELECT appointment_id, status FROM automation_events ORDER BY id"
        ).fetchall()
    assert len(event_rows) == 2  # confirmed event + confirmation e-mail
    assert {row["appointment_id"] for row in event_rows} == {winner.id}
    assert {row["status"] for row in event_rows} == {"skipped"}

    # The isolated schema is removed and no table survives the cleanup.
    from psycopg import sql

    url, schema = pg_schema
    with psycopg.connect(url, connect_timeout=5, autocommit=True) as connection:
        connection.execute(
            sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                sql.Identifier(schema)
            )
        )
    with psycopg.connect(url, connect_timeout=5, autocommit=True) as connection:
        remaining = connection.execute(
            "SELECT 1 FROM information_schema.schemata WHERE schema_name = %s",
            (schema,),
        ).fetchone()
    assert remaining is None


# ---------------------------------------------------------------------------
# TC-019-015 — event deduplication
# ---------------------------------------------------------------------------


def test_tc_019_015_event_dedup_single_row_without_second_send(
    pg_database: Database,
) -> None:
    appointment = appointments.insert_appointment(VALID_DATA, pg_database)
    event_id = f"appointment.cancelled:{appointment.id}:v1"

    assert (
        events.insert_event(
            event_id, "appointment.cancelled", 1, appointment.id, pg_database
        )
        is True
    )
    # The caller sees ``False`` and therefore does not perform a second send.
    assert (
        events.insert_event(
            event_id, "appointment.cancelled", 1, appointment.id, pg_database
        )
        is False
    )
    assert _count(pg_database, "automation_events") == 1

    events.mark_sent(event_id, pg_database)
    assert (
        events.insert_event(
            event_id, "appointment.cancelled", 1, appointment.id, pg_database
        )
        is False
    )
    stored = events.get_by_event_id(event_id, pg_database)
    assert stored is not None
    assert stored.status == "sent"
    assert _count(pg_database, "automation_events") == 1


# ---------------------------------------------------------------------------
# TC-019-011 — coordinated contractual literal (Spec 019 RF-20 / RNF-5)
# ---------------------------------------------------------------------------


def test_tc_019_011_persistence_unavailable_literal_and_unchanged_mirror() -> None:
    """TC-019-011 — Spec 019 RF-20; RNF-5; D12/T8.

    The literal is fixed by the coordinated Specs 004/005 amendment approved
    on 2026-11-08. This test pins the exact value, its mirror in
    ``tests/expected_content.py`` and the existing Spec 004/005 literals that
    must not change.
    """
    approved_literal = (
        "No pudimos completar tu solicitud en este momento. "
        "Inténtalo de nuevo en unos minutos."
    )

    assert appointment_content.MSG_PERSISTENCE_UNAVAILABLE == approved_literal
    assert expected_content.MSG_PERSISTENCE_UNAVAILABLE == approved_literal
    assert (
        appointment_content.MSG_PERSISTENCE_UNAVAILABLE
        == expected_content.MSG_PERSISTENCE_UNAVAILABLE
    )

    # The new literal must not be confused with the busy-slot message.
    assert (
        appointment_content.MSG_PERSISTENCE_UNAVAILABLE
        != appointment_content.MSG_SLOT_TAKEN
    )

    # Existing Spec 004/005 literals remain untouched (RNF-5).
    unchanged_hu_004 = {
        "MSG_REQUIRED_SERVICE": "Selecciona un servicio.",
        "MSG_INVALID_SERVICE": "Selecciona un servicio válido.",
        "MSG_REQUIRED_DATE": "Selecciona una fecha.",
        "MSG_INVALID_DATE": (
            "Selecciona una fecha válida de lunes a viernes, no anterior a hoy."
        ),
        "MSG_REQUIRED_TIME": "Selecciona una hora.",
        "MSG_INVALID_TIME": "Selecciona una hora válida.",
        "MSG_SLOT_TAKEN": (
            "Ese horario ya no está disponible. Selecciona otro horario."
        ),
        "MSG_NO_HOURS": "No hay horarios disponibles para esta fecha.",
        "MSG_INVALID_PARAMS": "Parámetros inválidos.",
        "MSG_SELECT_DATE_HINT": (
            "Selecciona una fecha para ver las horas disponibles."
        ),
    }
    for name, literal in unchanged_hu_004.items():
        assert getattr(appointment_content, name) == literal, name
        assert getattr(expected_content, name) == literal, name

    unchanged_hu_005 = {
        "MSG_OCCUPIED_HOUR": "Ocupado",
        "MSG_CHECKING_HOURS": "Consultando disponibilidad…",
        "CALENDAR_LEGEND_FREE": "Con horarios disponibles",
        "CALENDAR_LEGEND_FULL": "Sin horarios disponibles",
        "DAY_LABEL_NO_HOURS": ", sin horarios disponibles",
    }
    for name, literal in unchanged_hu_005.items():
        assert getattr(appointment_content, name) == literal, name
        assert getattr(expected_content, name) == literal, name


# ---------------------------------------------------------------------------
# SQLite rollback compatibility of the adapted repositories
# ---------------------------------------------------------------------------


def test_sqlite_rollback_route_keeps_repository_contract(
    tmp_path: Path,
) -> None:
    path = tmp_path / "rollback.db"
    init_db(path)

    # Legacy ``database_path`` (still used by the services until T6).
    legacy = appointments.insert_appointment(VALID_DATA, path)
    assert legacy.id >= 1
    assert (
        events.insert_event(
            "legacy-event", "appointment.confirmed", 1, legacy.id, path
        )
        is True
    )
    assert (
        events.insert_event(
            "legacy-event", "appointment.confirmed", 1, legacy.id, path
        )
        is False
    )
    events.mark_sent("legacy-event", path)
    legacy_event = events.get_by_event_id("legacy-event", path)
    assert legacy_event is not None
    assert legacy_event.status == "sent"
    assert legacy_event.sent_at is not None

    # Temporary ``Database`` facade over SQLite (same SQL and adapter).
    database = Database(
        DatabaseTarget(backend="sqlite", sqlite_path=path)
    )
    other = {**VALID_DATA, "time": "09:00"}
    created = appointments.insert_appointment(other, database)
    assert created.id != legacy.id
    assert (
        events.insert_event(
            "facade-event", "appointment.confirmed", 1, created.id, database
        )
        is True
    )
    events.mark_sent("facade-event", database)
    facade_event = events.get_by_event_id("facade-event", database)
    assert facade_event is not None
    assert facade_event.status == "sent"
    assert facade_event.sent_at is not None


# ---------------------------------------------------------------------------
# T5 review regression — temporary Database created from DatabaseTarget
# ---------------------------------------------------------------------------


def _application_connection_count(dsn: str) -> int:
    """Count open ``Database`` connections, excluding the observer's own."""
    with psycopg.connect(dsn, autocommit=True, connect_timeout=5) as connection:
        row = connection.execute(
            """
            SELECT count(*) AS total
              FROM pg_stat_activity
             WHERE datname = current_database()
               AND application_name = 'consultorio-web'
               AND pid <> pg_backend_pid()
            """
        ).fetchone()
    return int(row[0])


def _wait_until_connections_at_most(
    dsn: str, maximum: int, timeout: float = 2.0
) -> int:
    """Wait briefly for a closed connection to disappear from the server."""
    deadline = time.monotonic() + timeout
    while True:
        count = _application_connection_count(dsn)
        if count <= maximum or time.monotonic() >= deadline:
            return count
        time.sleep(0.05)


def test_t5_target_scope_closes_connection_in_app_context(
    app: object, pg_target: DatabaseTarget
) -> None:
    """``DatabaseTarget`` inside ``app.app_context()`` leaves no connection.

    The repository creates a temporary ``Database`` for the target. Inside a
    Flask app context ``Database`` keeps its connection in ``flask.g`` until
    ``close_request()``; because the app does not own that temporary instance,
    its teardown never closes it. The regression observes PostgreSQL
    ``pg_stat_activity`` (public server state, not private attributes) after a
    successful write, after an exception, and after a read.
    """
    with app.app_context():
        baseline = _application_connection_count(pg_target.dsn)

        created = appointments.insert_appointment(VALID_DATA, pg_target)
        after_write = _wait_until_connections_at_most(
            pg_target.dsn, baseline
        )
        assert after_write <= baseline

        # Exception path: a duplicate active slot aborts the transaction.
        with pytest.raises(pg_errors.UniqueViolation):
            appointments.insert_appointment(VALID_DATA, pg_target)
        after_error = _wait_until_connections_at_most(
            pg_target.dsn, baseline
        )
        assert after_error <= baseline

        fetched = appointments.get_appointment_by_id(created.id, pg_target)
        after_read = _wait_until_connections_at_most(pg_target.dsn, baseline)
        assert after_read <= baseline

        event_id = f"appointment.confirmed:{created.id}:target-scope"
        assert (
            events.insert_event(
                event_id, "appointment.confirmed", 1, created.id, pg_target
            )
            is True
        )
        after_event_write = _wait_until_connections_at_most(
            pg_target.dsn, baseline
        )
        assert after_event_write <= baseline

        stored_event = events.get_by_event_id(event_id, pg_target)
        after_event_read = _wait_until_connections_at_most(
            pg_target.dsn, baseline
        )
        assert after_event_read <= baseline

    assert fetched == created
    assert stored_event is not None
    assert stored_event.status == "pending"
