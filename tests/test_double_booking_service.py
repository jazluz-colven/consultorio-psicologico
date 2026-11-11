"""HU-006 — double-booking protection at the service layer (spec 006)."""

import threading
from datetime import date, timedelta
from unittest import mock

import psycopg
import psycopg.errors as pg_errors
import pytest

from consultorio.errors import PersistenceUnavailable
from consultorio.persistence.database import PARTIAL_INDEX_NAME
from consultorio.services import appointment_service as service
from consultorio.services.appointment_service import SLOT_TAKEN

SERVICE_A = "nutrition"
SERVICE_B = "psychology_integral"
SLOT = "08:00"


class _SlotUniqueViolation(pg_errors.UniqueViolation):
    """psycopg unique violation carrying the partial-index name in ``diag``."""

    class diag:  # type: ignore[override]
        constraint_name = PARTIAL_INDEX_NAME


def _future_weekday() -> str:
    candidate = date.today()
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


def _booking_data(service_key: str, booking_date: str, time: str) -> dict[str, str]:
    return {
        "service": service_key,
        "date": booking_date,
        "time": time,
        "document_type": "CC",
        "document_number": "1234567890",
        "patient_name": "Ana Pérez",
        "email": "ana@correo.com",
        "phone": "3001234567",
    }


def _count_rows(database) -> int:
    with database.connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total FROM appointments"
        ).fetchone()
    return int(row["total"])


def test_tc_006_001_horario_libre_registra_una_fila(database) -> None:
    booking_date = _future_weekday()
    appointment = service.create_booking(
        _booking_data(SERVICE_A, booking_date, SLOT), database
    )
    assert appointment.status == "confirmed"
    assert appointment.service == SERVICE_A
    assert appointment.date == booking_date
    assert appointment.time == SLOT
    assert _count_rows(database) == 1


def test_tc_006_002_reintento_identico_rechazado_sin_filas(database) -> None:
    booking_date = _future_weekday()
    data = _booking_data(SERVICE_A, booking_date, SLOT)
    first = service.create_booking(data, database)
    result = service.create_booking(dict(data), database)
    assert result == SLOT_TAKEN
    assert _count_rows(database) == 1
    original = service.repository.get_appointment_by_id(first.id, database)
    assert original is not None
    assert (original.service, original.date, original.time) == (
        SERVICE_A,
        booking_date,
        SLOT,
    )


def test_tc_006_003_ocho_hilos_concurrentes_una_sola_cita(database) -> None:
    booking_date = _future_weekday()
    workers = 8
    barrier = threading.Barrier(workers)
    results: list[object] = []
    lock = threading.Lock()

    def book() -> None:
        barrier.wait(timeout=10)
        outcome = service.create_booking(
            _booking_data(SERVICE_A, booking_date, SLOT), database
        )
        with lock:
            results.append(outcome)

    threads = [threading.Thread(target=book) for _ in range(workers)]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    created = [item for item in results if item is not SLOT_TAKEN]
    rejected = [item for item in results if item is SLOT_TAKEN]
    assert len(results) == workers
    assert len(created) == 1
    assert len(rejected) == workers - 1
    assert _count_rows(database) == 1


def test_tc_006_004_misma_fecha_hora_en_servicio_distinto_valido(
    database,
) -> None:
    booking_date = _future_weekday()
    first = service.create_booking(
        _booking_data(SERVICE_A, booking_date, SLOT), database
    )
    second = service.create_booking(
        _booking_data(SERVICE_B, booking_date, SLOT), database
    )
    assert first is not SLOT_TAKEN and second is not SLOT_TAKEN
    assert first.id != second.id
    assert _count_rows(database) == 2


def test_tc_006_005_solo_la_unicidad_del_slot_es_slot_taken(
    database,
) -> None:
    booking_date = _future_weekday()
    data = _booking_data(SERVICE_A, booking_date, SLOT)

    slot_violation = _SlotUniqueViolation("duplicate key value")
    with mock.patch.object(
        service.repository,
        "insert_appointment",
        side_effect=slot_violation,
    ):
        assert service.create_booking(data, database) == SLOT_TAKEN

    with mock.patch.object(
        service.repository,
        "insert_appointment",
        side_effect=psycopg.OperationalError("connection lost"),
    ):
        # A lock/outage is a domain outage, never an occupied slot (HU-019 D6).
        with pytest.raises(PersistenceUnavailable) as excinfo:
            service.create_booking(data, database)
        assert "connection lost" not in str(excinfo.value)
        assert str(excinfo.value) != SLOT_TAKEN

    with mock.patch.object(
        service.repository, "insert_appointment", side_effect=ValueError("boom")
    ):
        with pytest.raises(ValueError):
            service.create_booking(data, database)

    assert _count_rows(database) == 0
