"""HU-010 — cancellation e-mail event and slot release at the service layer
(spec 010 amended 2026-10-13)."""

import re
import sqlite3
import urllib.error
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from consultorio.persistence import appointments_repository as repository
from consultorio.persistence.appointments_repository import Appointment
from consultorio.services import appointment_service as booking
from consultorio.services import automation_service as automation
from consultorio.services import email_service as email

SERVICE_KEY = "nutrition"
SLOT = "08:00"
WEBHOOK_URL = "http://n8n.local/webhook/booking"
TIMEOUT = 3.0

PALETTE = {
    "#789B8A",
    "#B8D8CE",
    "#F7F3EA",
    "#D99A7A",
    "#E8D5B5",
    "#30454B",
}


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
    return f"appointment.cancellation_email:{appointment_id}:v1"


def _cancellation_posts(post: mock.MagicMock) -> list[mock.call]:
    return [
        call
        for call in post.call_args_list
        if call[0][1].get("event_type") == "appointment.cancellation_email"
    ]


def _count_events(event_id: str, database_path: Path) -> int:
    connection = sqlite3.connect(str(database_path))
    try:
        return connection.execute(
            "SELECT COUNT(*) FROM automation_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()[0]
    finally:
        connection.close()


def test_tc_010_001_cancelar_2xx_sent_un_post_y_payload_completo(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    posts = _cancellation_posts(post)
    assert len(posts) == 1
    url, payload, timeout, auth_header = posts[0][0]
    assert url == WEBHOOK_URL
    assert timeout == TIMEOUT
    assert auth_header == ""
    assert payload["event_id"] == _event_id(created.id)
    assert payload["recipient"]["to"] == "ana@correo.com"
    assert payload["recipient"]["patient_name"] == "Ana Pérez"
    assert set(payload["message"].keys()) == {"subject", "text", "html"}
    assert payload["message"]["subject"].startswith("Cita cancelada")
    assert payload["appointment"]["id"] == created.id
    assert payload["appointment"]["status"] == "cancelled"
    event = email.events_repository.get_by_event_id(
        _event_id(created.id), database_path
    )
    assert event is not None
    assert event.status == "sent"
    assert event.detail is None
    assert event.sent_at is not None


def test_tc_010_002_mensaje_completo_legible_y_paleta(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    cancelled = Appointment(
        id=created.id,
        document_type=created.document_type,
        document_number=created.document_number,
        patient_name=created.patient_name,
        email=created.email,
        phone=created.phone,
        service=created.service,
        date=created.date,
        time=created.time,
        status="cancelled",
        created_at=created.created_at,
    )
    message = email.build_cancellation_message(cancelled)

    expected_date_label = email.format_spanish_date(booking_date)
    assert message["subject"].startswith("Cita cancelada —")
    assert "Psiconutrición" in message["subject"]
    assert expected_date_label in message["subject"]
    for part in (message["text"], message["html"]):
        assert "Psiconutrición" in part
        assert booking_date not in part
        assert expected_date_label in part
        assert SLOT in part
        assert "Cancelada" in part
        assert f"#{created.id}" in part
        assert "Tu cita ha sido cancelada" in part
    hexes = set(re.findall(r"#[0-9A-Fa-f]{6}", message["html"]))
    assert hexes and hexes.issubset(PALETTE)
    assert "<img" not in message["html"].lower()
    assert "<link" not in message["html"].lower()
    assert "@import" not in message["html"]
    assert "http://" not in message["html"]
    assert "https://" not in message["html"]
    for forbidden in ("1234567890", "3001234567"):
        assert forbidden not in message["text"]
        assert forbidden not in message["html"]


def test_tc_010_003_url_vacia_skipped_sin_post(database_path: Path) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        result = booking.cancel_appointment(created.id, database_path)
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    assert len(_cancellation_posts(post)) == 0
    event = email.events_repository.get_by_event_id(
        _event_id(created.id), database_path
    )
    assert event is not None
    assert event.status == "skipped"
    assert event.detail == "Envío de correo no configurado."


def test_tc_010_004_urlerror_failed_cancellation_intacta(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(
        automation,
        "_post_webhook",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    event = email.events_repository.get_by_event_id(
        _event_id(created.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Servicio de automatización no disponible."


def test_tc_010_005_timeout_failed_cancellation_intacta(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", side_effect=TimeoutError):
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    event = email.events_repository.get_by_event_id(
        _event_id(created.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Tiempo de espera agotado (timeout)."


def test_tc_010_006_reproceso_already_cancelled_un_evento_un_post(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        first = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
        second = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(first, Appointment)
    assert second == booking.ALREADY_CANCELLED
    assert len(_cancellation_posts(post)) == 1
    assert _count_events(_event_id(created.id), database_path) == 1


def test_tc_010_007_email_invalido_failed_sin_post(database_path: Path) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    connection = sqlite3.connect(str(database_path))
    try:
        connection.execute(
            "UPDATE appointments SET email = '' WHERE id = ?", (created.id,)
        )
        connection.commit()
    finally:
        connection.close()
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    assert len(_cancellation_posts(post)) == 0
    event = email.events_repository.get_by_event_id(
        _event_id(created.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == (
        "Dirección de correo del paciente ausente o no válida."
    )


def test_tc_010_008_datos_incompletos_failed_sin_post(
    database_path: Path,
) -> None:
    incomplete = Appointment(
        id=1,
        document_type="CC",
        document_number="1234567890",
        patient_name="Ana Pérez",
        email="ana@correo.com",
        phone="3001234567",
        service="",
        date="",
        time="",
        status="cancelled",
        created_at="2026-10-10 10:00:00",
    )
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        email.send_cancellation(
            incomplete, str(database_path), WEBHOOK_URL, TIMEOUT
        )
    assert len(_cancellation_posts(post)) == 0
    event = email.events_repository.get_by_event_id(
        _event_id(incomplete.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Datos de la cita incompletos."


def test_tc_010_009_aislamiento_repositorio_caido_cancelacion_ok(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(
        email.events_repository,
        "insert_event",
        side_effect=RuntimeError("db down"),
    ):
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"


def test_tc_010_010_payload_allowlist_event_id_determinista(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    cancelled = Appointment(
        id=created.id,
        document_type=created.document_type,
        document_number=created.document_number,
        patient_name=created.patient_name,
        email=created.email,
        phone=created.phone,
        service=created.service,
        date=created.date,
        time=created.time,
        status="cancelled",
        created_at=created.created_at,
    )
    event = email.build_cancellation_event(cancelled)
    assert set(event.keys()) == {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "recipient",
        "message",
        "appointment",
    }
    assert event["event_id"] == _event_id(created.id)
    assert event["event_type"] == "appointment.cancellation_email"
    assert event["event_version"] == 1
    assert set(event["recipient"].keys()) == {"to", "patient_name"}
    assert set(event["message"].keys()) == {"subject", "text", "html"}
    assert event["appointment"]["status"] == "cancelled"
    forbidden = {
        "document_type",
        "document_number",
        "phone",
        "created_at",
    }
    assert forbidden.isdisjoint(event.keys())
    assert forbidden.isdisjoint(event["appointment"].keys())


def test_tc_010_011_cancelar_libera_el_horario(database_path: Path) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    assert repository.is_slot_taken(SERVICE_KEY, booking_date, SLOT, database_path)
    result = booking.cancel_appointment(created.id, database_path)
    assert isinstance(result, Appointment)
    assert not repository.is_slot_taken(
        SERVICE_KEY, booking_date, SLOT, database_path
    )
    hours = dict(
        booking.get_hours_with_status(SERVICE_KEY, booking_date, database_path)
    )
    assert hours[SLOT] is True


def test_tc_010_012_slot_confirmado_sigue_dando_slot_taken(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    booking.create_booking(_booking_data(booking_date), database_path)
    result = booking.create_booking(_booking_data(booking_date), database_path)
    assert result == booking.SLOT_TAKEN
    connection = sqlite3.connect(str(database_path))
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM appointments"
        ).fetchone()[0]
    finally:
        connection.close()
    assert count == 1
