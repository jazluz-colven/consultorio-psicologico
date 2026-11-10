"""PostgreSQL persistence repositories (Spec 019, T5).

Covers, against a real PostgreSQL server and an isolated throwaway schema:

* TC-019-006 — appointments repository: ``INSERT ... RETURNING id``, ``%s``
  placeholders, ``rowcount``, availability excludes ``cancelled`` and the
  partial unique index blocks duplicate active slots (RF-4, RF-6, RF-10,
  RF-11, RF-14; CL-8).
* TC-019-007 — automation events repository: ``UNIQUE(event_id)``, duplicate
  ``insert_event`` returns ``False`` with a single row, ``mark_sent`` writes
  UTC and ``claim_failed_event`` keeps its atomic transition/``rowcount``
  (RF-7, RF-12, RF-30).
* TC-019-017 — ``created_at``/``sent_at`` are UTC ``YYYY-MM-DD HH:MM:SS`` with
  no conversion to ``America/Bogota`` (RF-30).
* TC-019-008 — the booking service maps only the slot ``UniqueViolation`` to
  ``SLOT_TAKEN``; an outage is ``PersistenceUnavailable`` and 8 concurrent
  bookings produce exactly one row and seven ``SLOT_TAKEN`` (D6, RF-8/RF-14).
* TC-019-009 — Spec 010 atomicity (T7, D5, RF-8/RF-13): the status transition
  and the ``pending`` event share one connection and one commit; a REAL
  ``INSERT`` failure (duplicate ``UNIQUE(event_id)``) rolls both back; the
  business event and the e-mail are published only after the commit.

``TEST_DATABASE_URL`` is mandatory: without PostgreSQL these tests fail with
instructions instead of skipping (plan D9/CL-10). The ``pg_schema``/
``pg_target`` fixtures isolate each test and never touch ``public``.
"""

import threading
from dataclasses import replace
from datetime import datetime, timedelta, timezone
from unittest import mock
from zoneinfo import ZoneInfo

import psycopg.errors as pg_errors
import pytest

from consultorio.errors import PersistenceUnavailable
from consultorio.persistence import appointments_repository as appointments
from consultorio.persistence import automation_events_repository as events
from consultorio.persistence.appointments_repository import Appointment
from consultorio.persistence.database import (
    Database,
    DatabaseTarget,
    _default_connect,
)
from consultorio.services import appointment_service as booking
from consultorio.services import automation_service, email_service

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
UTC_FORMAT = "%Y-%m-%d %H:%M:%S"


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


def _parse_utc(value: str) -> datetime:
    return datetime.strptime(value, UTC_FORMAT).replace(tzinfo=timezone.utc)


def _cancel_event_id(appointment_id: int) -> str:
    return f"appointment.cancelled:{appointment_id}:v1"


# ---------------------------------------------------------------------------
# TC-019-006 — appointments repository on PostgreSQL
# ---------------------------------------------------------------------------


def test_tc_019_006_appointments_repository_contract(
    pg_database: Database,
) -> None:
    created = appointments.insert_appointment(VALID_DATA, pg_database)

    assert isinstance(created, Appointment)
    assert created.id >= 1  # real ``RETURNING id``, not ``lastrowid``
    assert created.status == "confirmed"
    assert created.created_at

    fetched = appointments.get_appointment_by_id(created.id, pg_database)
    assert fetched == created

    # Availability excludes cancelled rows: the active slot is taken.
    assert appointments.is_slot_taken(
        "nutrition", "2026-11-10", "08:00", pg_database
    )
    assert appointments.list_booked_times(
        "nutrition", "2026-11-10", pg_database
    ) == ["08:00"]
    assert appointments.list_booked_times_by_date(
        "nutrition", "2026-11-10", "2026-11-10", pg_database
    ) == {"2026-11-10": ["08:00"]}

    # The partial unique index rejects a second active row at the engine.
    with pytest.raises(pg_errors.UniqueViolation):
        appointments.insert_appointment(VALID_DATA, pg_database)
    assert _count(pg_database, "appointments") == 1

    # ``rowcount == 0`` path: unknown id leaves no row and returns None.
    assert (
        appointments.update_appointment_status(999999, "cancelled", pg_database)
        is None
    )

    # Cancelling frees the slot; the confirmed slot stays blocked until then.
    cancelled = appointments.update_appointment_status(
        created.id, "cancelled", pg_database
    )
    assert cancelled is not None and cancelled.status == "cancelled"
    assert not appointments.is_slot_taken(
        "nutrition", "2026-11-10", "08:00", pg_database
    )
    assert appointments.list_booked_times(
        "nutrition", "2026-11-10", pg_database
    ) == []

    rebooked = appointments.insert_appointment(VALID_DATA, pg_database)
    assert rebooked.id != created.id
    assert appointments.is_slot_taken(
        "nutrition", "2026-11-10", "08:00", pg_database
    )

    # A second cancellation is a no-op with ``rowcount == 0``.
    assert (
        appointments.update_appointment_status(
            created.id, "cancelled", pg_database
        )
        is None
    )
    assert _count(pg_database, "appointments") == 2


def test_tc_019_006_sql_sent_to_postgres_uses_percent_s_and_returning(
    pg_target: DatabaseTarget,
) -> None:
    """The statements PostgreSQL receives use ``%s`` and ``RETURNING id``."""

    queries: list[tuple[str, tuple[object, ...]]] = []

    class _RecordingConnection:
        def __init__(self, connection: object) -> None:
            self._connection = connection

        def execute(self, query: object, params: tuple[object, ...] = ()):
            queries.append((str(query), params))
            return self._connection.execute(query, params)  # type: ignore[attr-defined]

        def commit(self) -> None:
            self._connection.commit()  # type: ignore[attr-defined]

        def rollback(self) -> None:
            self._connection.rollback()  # type: ignore[attr-defined]

        def close(self) -> None:
            self._connection.close()  # type: ignore[attr-defined]

    def factory(target: DatabaseTarget) -> _RecordingConnection:
        return _RecordingConnection(_default_connect(target))

    database = Database(pg_target, connect_factory=factory)
    appointments.insert_appointment(VALID_DATA, database)

    statement = [
        query
        for query, _params in queries
        if "INSERT INTO appointments" in query
    ]
    assert len(statement) == 1
    assert "%s" in statement[0]
    assert "RETURNING id" in statement[0]
    assert "?" not in statement[0]
    # Every application statement (not just the INSERT) is PostgreSQL-native.
    application = [
        query
        for query, _params in queries
        if "appointments" in query and not query.lstrip().upper().startswith("CREATE")
    ]
    assert application
    assert all("%s" in query for query in application)
    assert all("?" not in query for query in application)


# ---------------------------------------------------------------------------
# TC-019-008 �?" booking service error mapping and concurrency on PostgreSQL
# ---------------------------------------------------------------------------


def test_tc_019_008_booking_service_maps_only_slot_uniqueness(
    pg_database: Database,
) -> None:
    """D6: UniqueViolation(slot) -> SLOT_TAKEN; outage never is a taken slot."""
    appointments.insert_appointment(VALID_DATA, pg_database)

    with mock.patch.object(
        booking.repository, "is_slot_taken", return_value=False
    ):
        assert booking.create_booking(VALID_DATA, pg_database) == booking.SLOT_TAKEN
    assert _count(pg_database, "appointments") == 1

    unavailable = Database(
        replace(
            pg_database.target,
            dsn=(
                "postgresql://consultorio_dev@127.0.0.1:1/consultorio_dev"
                "?sslmode=disable"
            ),
            connect_timeout=1.0,
        )
    )
    with pytest.raises(PersistenceUnavailable) as excinfo:
        booking.create_booking({**VALID_DATA, "time": "09:00"}, unavailable)
    assert str(excinfo.value) != booking.SLOT_TAKEN
    assert _count(pg_database, "appointments") == 1


def test_tc_019_008_eight_threads_create_exactly_one_booking(
    pg_database: Database,
) -> None:
    """The partial unique index keeps one row and seven SLOT_TAKEN results."""
    concurrent_database = Database(
        replace(
            pg_database.target,
            max_connections=8,
            acquire_timeout=10.0,
        )
    )
    data = {**VALID_DATA, "time": "10:00"}
    barrier = threading.Barrier(8)
    lock = threading.Lock()
    results: list[object] = []
    errors: list[BaseException] = []

    def worker() -> None:
        barrier.wait()
        try:
            result = booking.create_booking(data, concurrent_database)
        except BaseException as error:  # pragma: no cover - asserted below
            with lock:
                errors.append(error)
        else:
            with lock:
                results.append(result)

    with mock.patch.object(
        booking.automation_service, "on_appointment_confirmed"
    ), mock.patch.object(booking.email_service, "send_confirmation"):
        threads = [threading.Thread(target=worker) for _ in range(8)]
        for thread in threads:
            thread.start()
        for thread in threads:
            thread.join(timeout=30)

    assert all(not thread.is_alive() for thread in threads)
    assert not errors
    assert len(results) == 8
    assert sum(result == booking.SLOT_TAKEN for result in results) == 7
    assert sum(isinstance(result, Appointment) for result in results) == 1
    assert _count(pg_database, "appointments") == 1


# ---------------------------------------------------------------------------
# TC-019-009 — Spec 010 atomicity: one connection/transaction, real INSERT
# failure rollback and publication only after the commit (T7, D5, RF-8/RF-13)
# ---------------------------------------------------------------------------


def _independent_snapshot(
    database: Database, appointment_id: int
) -> dict[str, object]:
    """Read the appointment and its events from a SEPARATE connection.

    The ``Database`` facade opens a new connection per operation outside a
    Flask app context, so this snapshot is not affected by any open
    transaction of the caller. It is the evidence that the commit really
    happened before the value is observed.
    """
    independent = Database(database.target)
    with independent.connection() as connection:
        appointment_row = connection.execute(
            "SELECT status FROM appointments WHERE id = %s",
            (appointment_id,),
        ).fetchone()
        rows = connection.execute(
            """
            SELECT id, event_id, status FROM automation_events
            WHERE appointment_id = %s
            ORDER BY id
            """,
            (appointment_id,),
        ).fetchall()
    return {
        "status": (
            appointment_row["status"] if appointment_row is not None else None
        ),
        "events": [(row["event_id"], row["status"]) for row in rows],
        "event_ids": [row["id"] for row in rows],
    }


def test_tc_019_009_update_and_event_share_connection_and_single_commit(
    pg_database: Database, pg_target: DatabaseTarget
) -> None:
    """D5/RF-13: the UPDATE and the event INSERT run on one connection/commit.

    A recording connection factory captures which connection executed every
    statement. If the repository opened a second connection for the event, the
    two statements would carry different identifiers and this test would fail.
    """
    appointment = appointments.insert_appointment(VALID_DATA, pg_database)
    event_id = _cancel_event_id(appointment.id)
    log: list[tuple[str, int, str, tuple[object, ...]]] = []

    class _RecordingConnection:
        _counter = 0

        def __init__(self, connection: object) -> None:
            type(self)._counter += 1
            self.connection_id = type(self)._counter
            self._connection = connection

        def execute(self, query: object, params: tuple[object, ...] = ()):
            log.append(
                (
                    "execute",
                    self.connection_id,
                    " ".join(str(query).split()),
                    params,
                )
            )
            return self._connection.execute(query, params)  # type: ignore[attr-defined]

        def commit(self) -> None:
            log.append(("commit", self.connection_id, "", ()))
            self._connection.commit()  # type: ignore[attr-defined]

        def rollback(self) -> None:
            log.append(("rollback", self.connection_id, "", ()))
            self._connection.rollback()  # type: ignore[attr-defined]

        def close(self) -> None:
            self._connection.close()  # type: ignore[attr-defined]

    database = Database(
        pg_target,
        connect_factory=lambda target: _RecordingConnection(
            _default_connect(target)
        ),
    )
    updated = appointments.update_appointment_status_with_pending_event(
        appointment.id,
        "cancelled",
        event_id,
        "appointment.cancelled",
        1,
        database,
    )
    assert updated is not None and updated.status == "cancelled"

    updates = [
        entry
        for entry in log
        if entry[0] == "execute" and "UPDATE appointments SET status" in entry[2]
    ]
    inserts = [
        entry
        for entry in log
        if entry[0] == "execute" and "INSERT INTO automation_events" in entry[2]
    ]
    assert len(updates) == 1
    assert len(inserts) == 1
    writer = updates[0][1]
    # Same connection for the status transition and the pending event.
    assert inserts[0][1] == writer
    writer_commits = [
        entry for entry in log if entry[0] == "commit" and entry[1] == writer
    ]
    # Exactly one commit, after both statements, on the writer connection.
    assert len(writer_commits) == 1
    writer_log = [entry for entry in log if entry[1] == writer]
    assert (
        writer_log.index(updates[0])
        < writer_log.index(inserts[0])
        < writer_log.index(writer_commits[0])
    )
    assert not [entry for entry in log if entry[0] == "rollback"]

    stored = appointments.get_appointment_by_id(appointment.id, pg_database)
    assert stored is not None and stored.status == "cancelled"
    stored_event = events.get_by_event_id(event_id, pg_database)
    assert stored_event is not None and stored_event.status == "pending"


def test_tc_019_009_real_event_insert_failure_rolls_back_cancellation(
    pg_database: Database,
) -> None:
    """RF-8/RF-13: a REAL duplicate ``event_id`` rolls back the transition.

    The failure is produced by the engine, not by a mock: a first event with
    the deterministic cancellation ``event_id`` is inserted, so the INSERT
    inside ``update_appointment_status_with_pending_event()`` violates
    ``UNIQUE(event_id)``. The appointment must stay ``confirmed`` and no
    second (orphan) event row may exist.
    """
    appointment = appointments.insert_appointment(VALID_DATA, pg_database)
    event_id = _cancel_event_id(appointment.id)
    assert (
        events.insert_event(
            event_id, "appointment.cancelled", 1, appointment.id, pg_database
        )
        is True
    )
    preexisting = events.get_by_event_id(event_id, pg_database)
    assert preexisting is not None

    publish = mock.Mock()
    send = mock.Mock()
    with (
        mock.patch.object(
            automation_service, "publish_cancelled_event", publish
        ),
        mock.patch.object(email_service, "send_cancellation", send),
    ):
        with pytest.raises(pg_errors.UniqueViolation) as excinfo:
            booking.cancel_appointment(
                appointment.id,
                pg_database,
                "http://n8n.local/webhook/booking",
                3.0,
            )

    # The engine rejected the event INSERT itself (not an earlier statement).
    constraint = getattr(
        getattr(excinfo.value, "diag", None), "constraint_name", None
    )
    assert constraint == "automation_events_event_id_key"

    # Nothing is published when the transaction never committed.
    publish.assert_not_called()
    send.assert_not_called()

    # An independent connection proves the rollback is durable.
    snapshot = _independent_snapshot(pg_database, appointment.id)
    assert snapshot["status"] == "confirmed"
    assert snapshot["events"] == [(event_id, "pending")]
    assert snapshot["event_ids"] == [preexisting.id]  # no orphan row added


def test_tc_019_009_publication_runs_only_after_commit(
    pg_database: Database,
) -> None:
    """RF-8/RF-13: business event and e-mail are published after the commit.

    Each spy reads the appointment and its events from a SEPARATE connection
    at the exact moment it is invoked. Seeing ``cancelled`` and the visible
    ``pending`` row there is only possible if the single commit already
    happened. The spies never publish, so the row stays ``pending``.
    """
    appointment = appointments.insert_appointment(
        {**VALID_DATA, "time": "09:00"}, pg_database
    )
    event_id = _cancel_event_id(appointment.id)
    snapshots: list[tuple[str, dict[str, object]]] = []

    def publish_spy(cancelled, database, *args, **kwargs) -> None:
        snapshots.append(
            ("publish", _independent_snapshot(database, appointment.id))
        )

    def email_spy(cancelled, database, *args, **kwargs) -> None:
        snapshots.append(
            ("email", _independent_snapshot(database, appointment.id))
        )

    with (
        mock.patch.object(
            automation_service,
            "publish_cancelled_event",
            side_effect=publish_spy,
        ) as publish,
        mock.patch.object(
            email_service, "send_cancellation", side_effect=email_spy
        ) as send,
    ):
        result = booking.cancel_appointment(
            appointment.id,
            pg_database,
            "http://n8n.local/webhook/booking",
            3.0,
        )

    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    publish.assert_called_once()
    send.assert_called_once()
    # Business event first, then the cancellation e-mail (Spec 010 F2-D1).
    assert [name for name, _snapshot in snapshots] == ["publish", "email"]
    for name, snapshot in snapshots:
        assert snapshot["status"] == "cancelled", name
        assert snapshot["events"] == [(event_id, "pending")], name

    final = _independent_snapshot(pg_database, appointment.id)
    assert final["status"] == "cancelled"
    assert final["events"] == [(event_id, "pending")]


# ---------------------------------------------------------------------------
# TC-019-007 — automation events repository on PostgreSQL
# ---------------------------------------------------------------------------


def test_tc_019_007_events_repository_dedup_and_claim(
    pg_database: Database,
) -> None:
    appointment = appointments.insert_appointment(VALID_DATA, pg_database)
    event_id = _cancel_event_id(appointment.id)

    assert (
        events.insert_event(
            event_id,
            "appointment.cancelled",
            1,
            appointment.id,
            pg_database,
        )
        is True
    )
    # Second insert: deduplicated by UNIQUE(event_id), no row, no second send.
    assert (
        events.insert_event(
            event_id,
            "appointment.cancelled",
            1,
            appointment.id,
            pg_database,
        )
        is False
    )
    assert _count(pg_database, "automation_events") == 1

    stored = events.get_by_event_id(event_id, pg_database)
    assert stored is not None
    assert stored.status == "pending"
    assert stored.detail is None
    assert stored.sent_at is None

    events.mark_sent(event_id, pg_database)
    sent = events.get_by_event_id(event_id, pg_database)
    assert sent is not None
    assert sent.status == "sent"
    assert sent.detail is None
    assert sent.sent_at is not None

    # Dedup does not overwrite the existing row (still ``sent``).
    assert (
        events.insert_event(
            event_id,
            "appointment.cancelled",
            1,
            appointment.id,
            pg_database,
        )
        is False
    )
    still_sent = events.get_by_event_id(event_id, pg_database)
    assert still_sent is not None and still_sent.status == "sent"
    assert _count(pg_database, "automation_events") == 1

    # ``claim_failed_event`` uses rowcount for the atomic failed -> pending move.
    failed_id = f"appointment.cancelled:{appointment.id}:retry"
    assert (
        events.insert_event(
            failed_id, "appointment.cancelled", 1, appointment.id, pg_database
        )
        is True
    )
    events.mark_failed(failed_id, "Error inesperado durante la automatización.", pg_database)
    assert events.claim_failed_event(failed_id, pg_database) is True
    claimed = events.get_by_event_id(failed_id, pg_database)
    assert claimed is not None
    assert claimed.status == "pending"
    assert claimed.detail is None
    # Second claim: already pending -> rowcount 0 -> False.
    assert events.claim_failed_event(failed_id, pg_database) is False


def test_tc_019_007_claim_failed_event_retryability_patterns(
    pg_database: Database,
) -> None:
    from consultorio.content import automation_content

    appointment = appointments.insert_appointment(VALID_DATA, pg_database)
    permanent = f"appointment.cancelled:{appointment.id}:permanent"
    retryable = f"appointment.cancelled:{appointment.id}:retryable"
    for event_id in (permanent, retryable):
        assert (
            events.insert_event(
                event_id, "appointment.cancelled", 1, appointment.id, pg_database
            )
            is True
        )
    events.mark_failed(
        permanent,
        automation_content.DETAIL_INVALID_RESPONSE_TEMPLATE.format(
            status_code="400"
        ),
        pg_database,
    )
    events.mark_failed(
        retryable,
        automation_content.DETAIL_INVALID_RESPONSE_TEMPLATE.format(
            status_code="429"
        ),
        pg_database,
    )

    # A permanent 4xx remains excluded by the same atomic UPDATE (rowcount 0).
    assert (
        events.claim_failed_event(
            permanent,
            pg_database,
            permanent_pattern=(
                automation_content.DETAIL_PERMANENT_REJECTION_PATTERN
            ),
            retryable_pattern=(
                automation_content.DETAIL_RETRYABLE_REJECTION_PATTERN
            ),
        )
        is False
    )
    assert (
        events.get_by_event_id(permanent, pg_database).status  # type: ignore[union-attr]
        == "failed"
    )
    # 429 stays retryable (rowcount 1).
    assert (
        events.claim_failed_event(
            retryable,
            pg_database,
            permanent_pattern=(
                automation_content.DETAIL_PERMANENT_REJECTION_PATTERN
            ),
            retryable_pattern=(
                automation_content.DETAIL_RETRYABLE_REJECTION_PATTERN
            ),
        )
        is True
    )


# ---------------------------------------------------------------------------
# TC-019-017 — UTC timestamps with the approved format
# ---------------------------------------------------------------------------


def test_tc_019_017_created_at_and_sent_at_are_utc(
    pg_database: Database,
) -> None:
    before = datetime.now(timezone.utc)
    appointment = appointments.insert_appointment(VALID_DATA, pg_database)
    event_id = _cancel_event_id(appointment.id)
    assert (
        events.insert_event(
            event_id, "appointment.cancelled", 1, appointment.id, pg_database
        )
        is True
    )
    events.mark_sent(event_id, pg_database)
    after = datetime.now(timezone.utc)

    created = appointments.get_appointment_by_id(appointment.id, pg_database)
    event = events.get_by_event_id(event_id, pg_database)
    assert created is not None and event is not None
    assert event.sent_at is not None

    for raw in (created.created_at, event.created_at, event.sent_at):
        # Exactly the approved ``YYYY-MM-DD HH:MM:SS`` format (no offset).
        datetime.strptime(raw, UTC_FORMAT)

    created_at = _parse_utc(event.created_at)
    sent_at = _parse_utc(event.sent_at)
    tolerance = timedelta(seconds=30)
    assert before - tolerance <= created_at <= after + tolerance
    assert before - tolerance <= sent_at <= after + tolerance

    # No conversion to ``America/Bogota``: the stored wall clock is UTC. Compare
    # naive wall clocks because subtracting aware datetimes would compare the
    # same instant and always yield ~0 s.
    bogota_wall_clock = datetime.now(ZoneInfo("America/Bogota")).replace(
        tzinfo=None
    )
    assert abs(
        (created_at.replace(tzinfo=None) - bogota_wall_clock).total_seconds()
    ) > 3600
    assert abs(
        (sent_at.replace(tzinfo=None) - bogota_wall_clock).total_seconds()
    ) > 3600
