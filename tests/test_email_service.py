"""HU-008 — confirmation e-mail event at the service layer (spec 008)."""

import re
import urllib.error
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

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
    return f"appointment.confirmation_email:{appointment_id}:v1"


def _email_posts(post: mock.MagicMock) -> list[mock.call]:
    """POSTs of the confirmation e-mail event only (D15: two events exist)."""
    return [
        call
        for call in post.call_args_list
        if call[0][1].get("event_type") == "appointment.confirmation_email"
    ]


def test_tc_008_001_mensaje_completo_legible_y_paleta(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    appointment = booking.create_booking(
        _booking_data(booking_date), database_path
    )
    message = email.build_confirmation_message(appointment)

    expected_date_label = email.format_spanish_date(booking_date)
    assert message["subject"].startswith("Confirmación de tu cita —")
    assert "Psiconutrición" in message["subject"]
    assert expected_date_label in message["subject"]
    for part in (message["text"], message["html"]):
        assert "Psiconutrición" in part
        assert booking_date not in part  # ISO date is not the readable label
        assert expected_date_label in part
        assert SLOT in part
        assert "Pendiente" in part
        assert f"#{appointment.id}" in part
        assert "Guarda este correo como comprobante" in part
    # HTML: only the 6 palette hexes, no <img>, no external CSS, no remote URL
    hexes = set(re.findall(r"#[0-9A-Fa-f]{6}", message["html"]))
    assert hexes and hexes.issubset(PALETTE)
    assert "<img" not in message["html"].lower()
    assert "<link" not in message["html"].lower()
    assert "@import" not in message["html"]
    assert "http://" not in message["html"]
    assert "https://" not in message["html"]
    # no extra personal data in the message (minimization)
    for forbidden in ("1234567890", "3001234567"):
        assert forbidden not in message["text"]
        assert forbidden not in message["html"]


def test_tc_008_002_2xx_marca_sent_y_un_post_del_tipo(database_path: Path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        appointment = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            TIMEOUT,
        )
    posts = _email_posts(post)
    assert len(posts) == 1
    url, payload, timeout, auth_header = posts[0][0]
    assert url == WEBHOOK_URL
    assert timeout == TIMEOUT
    assert auth_header == ""
    assert payload["event_id"] == _event_id(appointment.id)
    assert payload["event_type"] == "appointment.confirmation_email"
    assert payload["recipient"]["to"] == "ana@correo.com"
    assert payload["recipient"]["patient_name"] == "Ana Pérez"
    assert set(payload["message"].keys()) == {"subject", "text", "html"}
    assert payload["appointment"]["id"] == appointment.id
    event = email.events_repository.get_by_event_id(
        _event_id(appointment.id), database_path
    )
    assert event is not None
    assert event.status == "sent"
    assert event.detail is None
    assert event.sent_at is not None


def test_tc_008_003_url_vacia_skipped_sin_post(database_path: Path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        appointment = booking.create_booking(
            _booking_data(booking_date), database_path
        )
    assert len(_email_posts(post)) == 0
    event = email.events_repository.get_by_event_id(
        _event_id(appointment.id), database_path
    )
    assert event is not None
    assert event.status == "skipped"
    assert event.detail == "Envío de correo no configurado."
    assert appointment.status == "pending"


def test_tc_008_004_urlerror_failed_sin_excepcion(database_path: Path) -> None:
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
    event = email.events_repository.get_by_event_id(
        _event_id(appointment.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Servicio de automatización no disponible."


def test_tc_008_005_timeout_failed_cita_intacta(database_path: Path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", side_effect=TimeoutError):
        appointment = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            TIMEOUT,
        )
    assert appointment.status == "pending"
    event = email.events_repository.get_by_event_id(
        _event_id(appointment.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Tiempo de espera agotado (timeout)."


def test_tc_008_006_reproceso_un_evento_un_post(database_path: Path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        appointment = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            TIMEOUT,
        )
        email.send_confirmation(
            appointment, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert len(_email_posts(post)) == 1
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


def test_tc_008_007_aislamiento_repositorio_caido_reserva_ok(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(
        email.events_repository,
        "insert_event",
        side_effect=RuntimeError("db down"),
    ):
        appointment = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            TIMEOUT,
        )
    assert isinstance(appointment, Appointment)
    assert appointment.status == "pending"


def test_tc_008_008_datos_incompletos_failed_sin_post(database_path: Path) -> None:
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
        status="pending",
        created_at="2026-10-10 10:00:00",
    )
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        email.send_confirmation(
            incomplete, str(database_path), WEBHOOK_URL, TIMEOUT
        )
    assert len(_email_posts(post)) == 0
    event = email.events_repository.get_by_event_id(
        _event_id(incomplete.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Datos de la cita incompletos."


def test_tc_008_009_email_invalido_failed_sin_post(database_path: Path) -> None:
    booking_date = _future_weekday()
    for index, bad_email in enumerate(("", "sin-arroba", "a@b"), start=1):
        appointment = Appointment(
            id=index,
            document_type="CC",
            document_number="1234567890",
            patient_name="Ana Pérez",
            email=bad_email,
            phone="3001234567",
            service=SERVICE_KEY,
            date=booking_date,
            time=SLOT,
            status="pending",
            created_at="2026-10-10 10:00:00",
        )
        with mock.patch.object(
            automation, "_post_webhook", return_value=200
        ) as post:
            email.send_confirmation(
                appointment, str(database_path), WEBHOOK_URL, TIMEOUT
            )
        assert len(_email_posts(post)) == 0
        event = email.events_repository.get_by_event_id(
            _event_id(appointment.id), database_path
        )
        assert event is not None
        assert event.status == "failed"
        assert event.detail == (
            "Dirección de correo del paciente ausente o no válida."
        )
        # the same deterministic event_id cannot be registered twice
        assert not email.events_repository.insert_event(
            _event_id(appointment.id), email.EVENT_TYPE, 1, appointment.id,
            str(database_path),
        )


def test_tc_008_010_payload_allowlist_event_id_determinista(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    appointment = booking.create_booking(
        _booking_data(booking_date), database_path
    )
    event = email.build_event(appointment)
    assert set(event.keys()) == {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "recipient",
        "message",
        "appointment",
    }
    assert event["event_id"] == _event_id(appointment.id)
    assert event["event_type"] == "appointment.confirmation_email"
    assert event["event_version"] == 1
    assert set(event["recipient"].keys()) == {"to", "patient_name"}
    assert set(event["message"].keys()) == {"subject", "text", "html"}
    forbidden = {
        "document_type",
        "document_number",
        "phone",
        "created_at",
    }
    assert forbidden.isdisjoint(event.keys())
    assert forbidden.isdisjoint(event["appointment"].keys())
