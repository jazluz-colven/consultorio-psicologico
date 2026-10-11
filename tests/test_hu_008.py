"""HU-008 — registration, config, mirror, stdlib and regression (spec 008)."""

import sqlite3
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from consultorio.config import Config
from consultorio.content import email_content
from consultorio.services import automation_service as automation
from consultorio.services import appointment_service as booking
from consultorio.services import email_service as email
from tests import expected_content

SERVICE_KEY = "nutrition"
SLOT = "08:00"
WEBHOOK_URL = "http://n8n.local/webhook/booking"


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


def _events_of_type(database_path: Path, event_type: str) -> list[sqlite3.Row]:
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    try:
        return connection.execute(
            "SELECT * FROM automation_events WHERE event_type = ? ORDER BY id",
            (event_type,),
        ).fetchall()
    finally:
        connection.close()


def _count_event_id(database_path: Path, event_id: str) -> int:
    connection = sqlite3.connect(str(database_path))
    try:
        return connection.execute(
            "SELECT COUNT(*) FROM automation_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()[0]
    finally:
        connection.close()


def test_tc_008_011_dos_eventos_por_reserva_y_dedup(database_path: Path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        appointment = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            3.0,
        )
        # reprocess the same reservation: no duplicated events nor POSTs
        automation.on_appointment_confirmed(
            appointment, database_path, WEBHOOK_URL, 3.0
        )
        email.send_confirmation(appointment, str(database_path), WEBHOOK_URL, 3.0)
    confirmed = _events_of_type(database_path, "appointment.confirmed")
    email_events = _events_of_type(
        database_path, "appointment.confirmation_email"
    )
    assert len(confirmed) == 1
    assert len(email_events) == 1
    assert _count_event_id(
        database_path, f"appointment.confirmation_email:{appointment.id}:v1"
    ) == 1
    assert len(confirmed) + len(email_events) == 2  # two rows, two event_ids
    event_types_posted = [
        call[0][1].get("event_type") for call in post.call_args_list
    ]
    assert event_types_posted.count("appointment.confirmed") == 1
    assert event_types_posted.count("appointment.confirmation_email") == 1
    row = email_events[0]
    assert row["appointment_id"] == appointment.id
    assert row["status"] == "sent"
    assert row["detail"] is None


def test_tc_008_012_config_sin_smtp_y_defaults_intactos() -> None:
    smtp_settings = [
        name for name in dir(Config) if name.startswith("SMTP_")
    ]
    assert smtp_settings == []
    assert Config.AUTOMATION_WEBHOOK_URL == ""
    assert Config.AUTOMATION_TIMEOUT_SECONDS == 3.0
    assert Config.AUTOMATION_WEBHOOK_AUTH_HEADER == ""


def test_tc_008_013_espejo_de_literales() -> None:
    assert expected_content.EMAIL_SUBJECT_TEMPLATE == (
        email_content.EMAIL_SUBJECT_TEMPLATE
    )
    assert expected_content.EMAIL_SENDER_NAME == email_content.EMAIL_SENDER_NAME
    assert expected_content.EMAIL_BODY_HEADER == email_content.EMAIL_BODY_HEADER
    assert expected_content.EMAIL_LABEL_SERVICE == email_content.EMAIL_LABEL_SERVICE
    assert expected_content.EMAIL_LABEL_DATE == email_content.EMAIL_LABEL_DATE
    assert expected_content.EMAIL_LABEL_TIME == email_content.EMAIL_LABEL_TIME
    assert expected_content.EMAIL_LABEL_STATUS == email_content.EMAIL_LABEL_STATUS
    assert expected_content.EMAIL_LABEL_REFERENCE == (
        email_content.EMAIL_LABEL_REFERENCE
    )
    assert expected_content.EMAIL_FOOTER == email_content.EMAIL_FOOTER
    assert expected_content.MSG_APPOINTMENT_INCOMPLETE == (
        email_content.MSG_APPOINTMENT_INCOMPLETE
    )
    assert expected_content.DETAIL_EMAIL_NOT_CONFIGURED == (
        email_content.DETAIL_EMAIL_NOT_CONFIGURED
    )
    assert expected_content.DETAIL_INVALID_RECIPIENT == (
        email_content.DETAIL_INVALID_RECIPIENT
    )
    from consultorio.content.appointment_content import STATUS_PENDING_LABEL

    assert STATUS_PENDING_LABEL == "Pendiente"


def test_tc_008_014_constitucion_1_stdlib_only() -> None:
    source = Path("consultorio/services/email_service.py").read_text(
        encoding="utf-8"
    )
    assert "smtplib" not in source
    assert "import requests" not in source
    assert "from requests" not in source
    assert "import aiosmtplib" not in source
    assert "automation_service._post_webhook" in source
    import ast

    tree = ast.parse(source)
    stdlib_allowed = {"re", "urllib", "datetime"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                root = alias.name.split(".")[0]
                assert root in stdlib_allowed or root.startswith("consultorio")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            assert root in stdlib_allowed or root.startswith("consultorio")


def test_tc_008_015_http_end_to_end_303_y_evento_sent(client, app) -> None:
    booking_date = _future_weekday()
    app.config["AUTOMATION_WEBHOOK_URL"] = WEBHOOK_URL
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        response = client.post("/citas", data=_booking_data(booking_date))
    assert response.status_code == 303
    cita_id = int(response.headers["Location"].rstrip("/").split("/")[-1])

    confirmada = client.get(f"/citas/confirmada/{cita_id}")
    assert confirmada.status_code == 200

    email_posts = [
        call
        for call in post.call_args_list
        if call[0][1].get("event_type") == "appointment.confirmation_email"
    ]
    assert len(email_posts) == 1
    payload = email_posts[0][0][1]
    assert payload["recipient"]["to"] == "ana@correo.com"
    assert payload["appointment"]["id"] == cita_id
    assert payload["message"]["subject"].startswith("Confirmación de tu cita —")

    database_path = Path(app.config["DATABASE_PATH"])
    event = email.events_repository.get_by_event_id(
        f"appointment.confirmation_email:{cita_id}:v1", database_path
    )
    assert event is not None
    assert event.status == "sent"
    assert event.sent_at is not None


def test_tc_008_016_regresion_funcional_y_email_invalido(client, app, tmp_path) -> None:
    booking_date = _future_weekday()

    # HU-004: required-field validation still renders 200 with errors
    invalid = client.post("/citas", data={"service": ""})
    assert invalid.status_code == 200

    # HU-005/006: availability + double booking still hold
    with mock.patch.object(automation, "_post_webhook", return_value=200):
        first = client.post("/citas", data=_booking_data(booking_date))
    assert first.status_code == 303
    hora = client.get(
        f"/citas/horarios?service={SERVICE_KEY}&date={booking_date}"
    )
    assert hora.status_code == 200
    assert SLOT in hora.get_json()["occupied"]
    month = booking_date[:7]
    disponibilidad = client.get(
        f"/citas/disponibilidad?service={SERVICE_KEY}&month={month}"
    )
    assert disponibilidad.status_code == 200

    # HU-007: appointment.confirmed contract intact (no personal data)
    database_path = Path(app.config["DATABASE_PATH"])
    confirmed_rows = _events_of_type(database_path, "appointment.confirmed")
    assert len(confirmed_rows) == 1
    confirmed = automation.build_event(
        booking.repository.get_appointment_by_id(
            confirmed_rows[0]["appointment_id"], database_path
        )
    )
    assert set(confirmed.keys()) == {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "appointment",
    }
    assert "patient_name" not in confirmed
    assert "email" not in confirmed

    # HU-008: invalid e-mail → form 200 and zero new confirmation e-mail events
    app.config["AUTOMATION_WEBHOOK_URL"] = WEBHOOK_URL
    database_path = Path(app.config["DATABASE_PATH"])
    before = len(_events_of_type(database_path, "appointment.confirmation_email"))
    bad = _booking_data(booking_date, "08:30")
    bad["email"] = "no-es-un-correo"
    with mock.patch.object(automation, "_post_webhook", return_value=200):
        response = client.post("/citas", data=bad)
    assert response.status_code == 200
    after = len(_events_of_type(database_path, "appointment.confirmation_email"))
    assert after == before
