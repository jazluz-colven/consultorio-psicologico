"""HU-007 — automation events at the service layer (spec 007)."""

import urllib.error
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import pytest

from consultorio.services import automation_service as automation
from consultorio.services import appointment_service as booking

SERVICE_KEY = "nutrition"
SLOT = "08:00"
WEBHOOK_URL = "http://n8n.local/webhook/booking"
TIMEOUT = 3.0


def _future_weekday() -> str:
    candidate = date.today()
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


def _booking_data(booking_date: str, time: str = SLOT) -> dict[str, str]:
    return {
        "service": SERVICE_KEY,
        "date": booking_date,
        "time": time,
        "document_type": "CC",
        "document_number": "1234567890",
        "patient_name": "Ana Pérez",
        "email": "ana@correo.com",
        "phone": "3001234567",
    }


def _event_id(appointment_id: int) -> str:
    return f"appointment.confirmed:{appointment_id}:v1"


def test_tc_007_001_payload_permitido_sin_datos_personales(database_path: Path) -> None:
    booking_date = _future_weekday()
    appointment = booking.create_booking(
        _booking_data(booking_date), database_path
    )
    assert appointment.status == "pending"
    event = automation.build_event(appointment)
    assert set(event.keys()) == {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "appointment",
    }
    assert event["event_id"] == _event_id(appointment.id)
    assert event["event_type"] == "appointment.confirmed"
    assert event["event_version"] == 1
    assert set(event["appointment"].keys()) == {
        "id",
        "service",
        "date",
        "time",
        "status",
    }
    assert event["appointment"]["service"] == SERVICE_KEY
    assert event["appointment"]["date"] == booking_date
    assert event["appointment"]["time"] == SLOT
    forbidden = {
        "patient_name",
        "email",
        "phone",
        "document_type",
        "document_number",
        "created_at",
    }
    assert forbidden.isdisjoint(event.keys())
    assert forbidden.isdisjoint(event["appointment"].keys())


def test_tc_007_002_respuesta_2xx_marca_sent_y_un_post(database_path: Path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        appointment = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            TIMEOUT,
        )
    assert post.call_count == 1
    url, payload, timeout = post.call_args[0]
    assert url == WEBHOOK_URL
    assert timeout == TIMEOUT
    assert payload["event_id"] == _event_id(appointment.id)
    assert payload["appointment"]["id"] == appointment.id
    event = automation.events_repository.get_by_event_id(
        _event_id(appointment.id), database_path
    )
    assert event is not None
    assert event.status == "sent"
    assert event.detail is None
    assert event.sent_at is not None


def test_tc_007_003_url_no_configurada_skipped_sin_post(database_path: Path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        appointment = booking.create_booking(
            _booking_data(booking_date), database_path
        )
    assert post.call_count == 0
    event = automation.events_repository.get_by_event_id(
        _event_id(appointment.id), database_path
    )
    assert event is not None
    assert event.status == "skipped"
    assert event.detail == "Automatización no configurada."


def test_tc_007_004_urlerror_marca_failed_y_cita_intacta(database_path: Path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(
        automation,
        "_post_webhook",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        appointment = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            TIMEOUT,
        )
    assert appointment.status == "pending"
    event = automation.events_repository.get_by_event_id(
        _event_id(appointment.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Servicio de automatización no disponible."


def test_tc_007_005_timeout_marca_failed_y_cita_intacta(database_path: Path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(
        automation, "_post_webhook", side_effect=TimeoutError
    ):
        appointment = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            TIMEOUT,
        )
    assert appointment.status == "pending"
    event = automation.events_repository.get_by_event_id(
        _event_id(appointment.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Tiempo de espera agotado (timeout)."


def test_tc_007_006_respuesta_500_marca_failed(database_path: Path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", return_value=500):
        appointment = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            TIMEOUT,
        )
    event = automation.events_repository.get_by_event_id(
        _event_id(appointment.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Respuesta no válida del servicio (HTTP 500)."


def test_tc_007_007_reproceso_sin_duplicados(database_path: Path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        appointment = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            TIMEOUT,
        )
        automation.on_appointment_confirmed(
            appointment, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert post.call_count == 1
    import sqlite3

    connection = sqlite3.connect(str(database_path))
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM automation_events WHERE event_id = ?",
            (_event_id(appointment.id),),
        ).fetchone()[0]
    finally:
        connection.close()
    assert count == 1


def test_tc_007_008_fallo_de_registro_no_invalida_la_reserva(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(
        automation.events_repository,
        "insert_event",
        side_effect=RuntimeError("disk failure"),
    ):
        result = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            TIMEOUT,
        )
    assert result != "slot_taken"
    assert result.status == "pending"


def test_tc_007_009_timeout_a_nivel_urllib(database_path: Path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(
        automation.urllib.request,
        "urlopen",
        side_effect=TimeoutError("timed out"),
    ):
        result = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            0.01,
        )
    assert result.status == "pending"
    event = automation.events_repository.get_by_event_id(
        _event_id(result.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Tiempo de espera agotado (timeout)."
