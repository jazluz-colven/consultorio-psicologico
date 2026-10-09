"""HU-006 — double-booking protection at the service layer (spec 006)."""

import sqlite3
import threading
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import pytest

from consultorio.services import appointment_service as service
from consultorio.services.appointment_service import SLOT_TAKEN

SERVICE_A = "nutrition"
SERVICE_B = "psychology_integral"
SLOT = "08:00"


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


def _count_rows(database_path: Path) -> int:
    connection = sqlite3.connect(str(database_path))
    try:
        return connection.execute("SELECT COUNT(*) FROM appointments").fetchone()[0]
    finally:
        connection.close()


def test_tc_006_001_horario_libre_registra_una_fila(database_path: Path) -> None:
    booking_date = _future_weekday()
    appointment = service.create_booking(
        _booking_data(SERVICE_A, booking_date, SLOT), database_path
    )
    assert appointment.status == "pending"
    assert appointment.service == SERVICE_A
    assert appointment.date == booking_date
    assert appointment.time == SLOT
    assert _count_rows(database_path) == 1


def test_tc_006_002_reintento_identico_rechazado_sin_filas(database_path: Path) -> None:
    booking_date = _future_weekday()
    data = _booking_data(SERVICE_A, booking_date, SLOT)
    first = service.create_booking(data, database_path)
    result = service.create_booking(dict(data), database_path)
    assert result == SLOT_TAKEN
    assert _count_rows(database_path) == 1
    original = service.repository.get_appointment_by_id(first.id, database_path)
    assert original is not None
    assert (original.service, original.date, original.time) == (
        SERVICE_A,
        booking_date,
        SLOT,
    )


def test_tc_006_003_ocho_hilos_concurrentes_una_sola_cita(database_path: Path) -> None:
    booking_date = _future_weekday()
    workers = 8
    barrier = threading.Barrier(workers)
    results: list[object] = []
    lock = threading.Lock()

    def book() -> None:
        barrier.wait(timeout=10)
        outcome = service.create_booking(
            _booking_data(SERVICE_A, booking_date, SLOT), database_path
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
    assert _count_rows(database_path) == 1


def test_tc_006_004_misma_fecha_hora_en_servicio_distinto_valido(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    first = service.create_booking(
        _booking_data(SERVICE_A, booking_date, SLOT), database_path
    )
    second = service.create_booking(
        _booking_data(SERVICE_B, booking_date, SLOT), database_path
    )
    assert first is not SLOT_TAKEN and second is not SLOT_TAKEN
    assert first.id != second.id
    assert _count_rows(database_path) == 2


def test_tc_006_005_integrity_y_locked_a_slot_taken_resto_se_propaga(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    data = _booking_data(SERVICE_A, booking_date, SLOT)

    with mock.patch.object(
        service.repository,
        "insert_appointment",
        side_effect=sqlite3.IntegrityError(
            "UNIQUE constraint failed: appointments.service, appointments.date, "
            "appointments.time"
        ),
    ):
        assert service.create_booking(data, database_path) == SLOT_TAKEN

    with mock.patch.object(
        service.repository,
        "insert_appointment",
        side_effect=sqlite3.OperationalError("database is locked"),
    ):
        assert service.create_booking(data, database_path) == SLOT_TAKEN

    with mock.patch.object(
        service.repository, "insert_appointment", side_effect=ValueError("boom")
    ):
        with pytest.raises(ValueError):
            service.create_booking(data, database_path)

    assert _count_rows(database_path) == 0
