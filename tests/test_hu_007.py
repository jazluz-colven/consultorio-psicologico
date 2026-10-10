"""HU-007 — schema, config and functional regression for the automation event."""

import sqlite3
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from consultorio.config import Config, _parse_timeout_seconds
from consultorio.services import automation_service as automation
from consultorio.services import appointment_service as booking
from consultorio.services.appointment_service import SLOT_TAKEN

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


def test_tc_007_010_esquema_unique_y_dedup(database_path: Path) -> None:
    connection = sqlite3.connect(str(database_path))
    try:
        sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE name = 'automation_events'"
        ).fetchone()[0]
        assert "UNIQUE" in sql
        assert "event_id" in sql
    finally:
        connection.close()
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", return_value=200):
        appointment = booking.create_booking(
            _booking_data(booking_date),
            database_path,
            WEBHOOK_URL,
            3.0,
        )
        automation.on_appointment_confirmed(
            appointment, database_path, WEBHOOK_URL, 3.0
        )
    connection = sqlite3.connect(str(database_path))
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM automation_events WHERE event_id = ?",
            (f"appointment.confirmed:{appointment.id}:v1",),
        ).fetchone()[0]
    finally:
        connection.close()
    assert count == 1


def test_tc_007_011_config_defaults_y_parse_defensivo() -> None:
    assert Config.AUTOMATION_WEBHOOK_URL == ""
    assert Config.AUTOMATION_TIMEOUT_SECONDS == 3.0
    assert _parse_timeout_seconds("no-numerico") == 3.0
    assert _parse_timeout_seconds("") == 3.0
    assert _parse_timeout_seconds("-1") == 3.0
    assert _parse_timeout_seconds("5") == 5.0


def test_tc_007_012_regresion_agendamiento_con_y_sin_webhook(client, app, tmp_path) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", return_value=200):
        response = client.post("/citas", data=_booking_data(booking_date))
    assert response.status_code == 303
    cita_id = int(response.headers["Location"].rstrip("/").split("/")[-1])

    horarios = client.get(f"/citas/horarios?service={SERVICE_KEY}&date={booking_date}")
    assert horarios.status_code == 200
    assert SLOT in horarios.get_json()["occupied"]
    assert SLOT not in horarios.get_json()["available"]

    month = booking_date[:7]
    disponibilidad = client.get(
        f"/citas/disponibilidad?service={SERVICE_KEY}&month={month}"
    )
    assert disponibilidad.status_code == 200

    confirmada = client.get(f"/citas/confirmada/{cita_id}")
    assert confirmada.status_code == 200

    app.config["AUTOMATION_WEBHOOK_URL"] = ""
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        retry = client.post("/citas", data=_booking_data(booking_date))
        second = booking.create_booking(
            _booking_data(booking_date, "08:30"), Path(app.config["DATABASE_PATH"])
        )
    assert retry.status_code == 200
    assert second != SLOT_TAKEN
    assert post.call_count == 0
