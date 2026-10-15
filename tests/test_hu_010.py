"""HU-010 — Notificar la cancelación de una cita (Spec 010, enmienda 2026-10-13).

TC-010-014: migración del esquema de appointments (UNIQUE inline → índice
único parcial) con respaldo, conservación de datos, idempotencia y aborto.
TC-010-013/015/016/017: re-reserva, HTTP, espejo+config y regresión funcional.
"""

import sqlite3
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import pytest

from consultorio.config import Config
from consultorio.content import appointment_content as content
from consultorio.content import automation_content
from consultorio.content import email_content
from consultorio.persistence.database import (
    PARTIAL_INDEX_NAME,
    get_connection,
    init_db,
)
from consultorio.services import appointment_service as booking
from consultorio.services import automation_service as automation

from tests import expected_content as expected

LEGACY_SCHEMA = """
CREATE TABLE appointments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type   TEXT NOT NULL,
    document_number TEXT NOT NULL UNIQUE,
    patient_name    TEXT NOT NULL,
    email           TEXT NOT NULL,
    phone           TEXT NOT NULL,
    service         TEXT NOT NULL,
    date            TEXT NOT NULL,
    time            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'confirmed',
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE (service, date, time)
)
"""

LEGACY_SCHEMA_WITH_DUPLICATES = """
CREATE TABLE appointments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type   TEXT NOT NULL,
    document_number TEXT NOT NULL UNIQUE,
    patient_name    TEXT NOT NULL,
    email           TEXT NOT NULL,
    phone           TEXT NOT NULL,
    service         TEXT NOT NULL,
    date            TEXT NOT NULL,
    time            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'confirmed',
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
)
"""

ROW_NUTRITION = (
    "CC",
    "111111111",
    "Ana Pérez",
    "ana@correo.com",
    "3001111111",
    "nutrition",
    "2026-11-02",
    "08:00",
    "confirmed",
)
ROW_PSYCHOLOGY = (
    "CC",
    "222222222",
    "Luis Gómez",
    "luis@correo.com",
    "3002222222",
    "psychology_integral",
    "2026-11-02",
    "10:00",
    "confirmed",
)
ROW_CANCELLED = (
    "CC",
    "333333333",
    "María Ruiz",
    "maria@correo.com",
    "3003333333",
    "nutrition",
    "2026-11-03",
    "09:00",
    "cancelled",
)
DUPLICATE_ACTIVE = (
    "CC",
    "444444444",
    "Pedro Días",
    "pedro@correo.com",
    "3004444444",
    "nutrition",
    "2026-11-02",
    "08:00",
    "confirmed",
)


def _create_legacy_db(path: Path, schema: str, rows: list[tuple]) -> None:
    connection = sqlite3.connect(str(path))
    try:
        connection.execute(schema)
        connection.executemany(
            """
            INSERT INTO appointments (
                document_type, document_number, patient_name, email, phone,
                service, date, time, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.commit()
    finally:
        connection.close()


def test_tc_010_014_migracion_indice_parcial_respaldo_idempotente_y_aborto(
    tmp_path,
) -> None:
    path = tmp_path / "legacy.db"
    _create_legacy_db(
        path, LEGACY_SCHEMA, [ROW_NUTRITION, ROW_PSYCHOLOGY, ROW_CANCELLED]
    )

    init_db(path)

    with get_connection(path) as connection:
        table_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table'"
            " AND name = 'appointments'"
        ).fetchone()["sql"]
        assert "UNIQUE" not in table_sql.upper()
        index = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'index' AND name = ?",
            (PARTIAL_INDEX_NAME,),
        ).fetchone()
        assert index is not None
        assert "status <> 'cancelled'" in index["sql"]
        rows = connection.execute(
            "SELECT id, service, time, status FROM appointments ORDER BY id"
        ).fetchall()
    assert [(row["id"], row["service"], row["time"], row["status"]) for row in rows] == [
        (1, "nutrition", "08:00", "confirmed"),
        (2, "psychology_integral", "10:00", "confirmed"),
        (3, "nutrition", "09:00", "cancelled"),
    ]
    backups = list(tmp_path.glob("legacy.db.bak-*"))
    assert len(backups) == 1

    # Second run: the partial index already exists → no-op, no extra backup.
    init_db(path)
    assert len(list(tmp_path.glob("legacy.db.bak-*"))) == 1
    with get_connection(path) as connection:
        total = connection.execute(
            "SELECT COUNT(*) AS total FROM appointments"
        ).fetchone()["total"]
    assert total == 3

    # Abort: active duplicates among non-cancelled rows must fail loudly and
    # leave the legacy data untouched (constitución #5).
    dup_path = tmp_path / "dup.db"
    _create_legacy_db(
        dup_path, LEGACY_SCHEMA_WITH_DUPLICATES, [ROW_NUTRITION, DUPLICATE_ACTIVE]
    )
    with pytest.raises(RuntimeError, match="migration aborted"):
        init_db(dup_path)
    with get_connection(dup_path) as connection:
        table_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table'"
            " AND name = 'appointments'"
        ).fetchone()["sql"]
        total = connection.execute(
            "SELECT COUNT(*) AS total FROM appointments"
        ).fetchone()["total"]
    assert total == 2
    assert "UNIQUE" in table_sql.upper()


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


def _database_path(app) -> Path:
    with app.app_context():
        return Path(app.config["DATABASE_PATH"])


def test_tc_010_013_tras_cancelar_se_puede_re_reservar(
    database_path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    cancelled = booking.cancel_appointment(created.id, database_path)
    assert isinstance(cancelled, booking.Appointment)
    assert cancelled.status == "cancelled"

    rebooked = booking.create_booking(_booking_data(booking_date), database_path)
    assert isinstance(rebooked, booking.Appointment)
    assert rebooked.id != created.id
    assert rebooked.status == "confirmed"

    original = booking.repository.get_appointment_by_id(created.id, database_path)
    assert original is not None
    assert original.status == "cancelled"
    connection = sqlite3.connect(str(database_path))
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM appointments"
        ).fetchone()[0]
    finally:
        connection.close()
    assert count == 2


def test_tc_010_015_http_horarios_disponibilidad_y_re_reserva(
    app, client
) -> None:
    booking_date = _future_weekday()
    response = client.post("/citas", data=_booking_data(booking_date))
    assert response.status_code == 303
    cita_id = int(response.headers["Location"].rstrip("/").split("/")[-1])

    cancelled = booking.cancel_appointment(cita_id, _database_path(app))
    assert isinstance(cancelled, booking.Appointment)
    assert cancelled.status == "cancelled"

    horarios = client.get(
        f"/citas/horarios?service={SERVICE_KEY}&date={booking_date}"
    )
    assert horarios.status_code == 200
    payload = horarios.get_json()
    assert SLOT in payload["available"]
    assert SLOT not in payload["occupied"]

    month = booking_date[:7]
    disponibilidad = client.get(
        f"/citas/disponibilidad?service={SERVICE_KEY}&month={month}"
    )
    assert disponibilidad.status_code == 200
    assert booking_date in disponibilidad.get_json()["days"]

    rebooked = client.post("/citas", data=_booking_data(booking_date))
    assert rebooked.status_code == 303
    connection = sqlite3.connect(str(_database_path(app)))
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM appointments"
        ).fetchone()[0]
    finally:
        connection.close()
    assert count == 2


def test_tc_010_016_espejo_literal_y_config_sin_variables_nuevas() -> None:
    assert (
        expected.STATUS_CANCELLED
        == content.STATUS_CANCELLED
        == "cancelled"
    )
    assert (
        expected.STATUS_CANCELLED_LABEL
        == content.STATUS_CANCELLED_LABEL
        == "Cancelada"
    )
    assert (
        expected.CANCELLATION_EMAIL_SUBJECT_TEMPLATE
        == email_content.CANCELLATION_EMAIL_SUBJECT_TEMPLATE
    )
    assert (
        expected.CANCELLATION_EMAIL_BODY_HEADER
        == email_content.CANCELLATION_EMAIL_BODY_HEADER
    )
    assert (
        expected.CANCELLATION_EMAIL_FOOTER
        == email_content.CANCELLATION_EMAIL_FOOTER
    )
    assert (
        expected.DETAIL_CANCELLATION_NOT_CONFIGURED
        == email_content.DETAIL_CANCELLATION_NOT_CONFIGURED
    )
    automation_attrs = {
        name for name in dir(Config) if name.startswith("AUTOMATION_")
    }
    assert automation_attrs == {
        "AUTOMATION_WEBHOOK_URL",
        "AUTOMATION_TIMEOUT_SECONDS",
        "AUTOMATION_WEBHOOK_AUTH_HEADER",
    }


def test_tc_010_017_regresion_funcional_y_constitucion_1(
    database_path,
) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        appointment = booking.create_booking(
            _booking_data(booking_date), database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(appointment, booking.Appointment)
    assert appointment.status == "confirmed"

    hours = dict(
        booking.get_hours_with_status(SERVICE_KEY, booking_date, database_path)
    )
    assert hours[SLOT] is False

    conflict = booking.create_booking(
        _booking_data(booking_date), database_path, WEBHOOK_URL, TIMEOUT
    )
    assert conflict == booking.SLOT_TAKEN

    confirmed_posts = [
        call
        for call in post.call_args_list
        if call[0][1].get("event_type") == automation_content.EVENT_TYPE
    ]
    email_posts = [
        call
        for call in post.call_args_list
        if call[0][1].get("event_type") == "appointment.confirmation_email"
    ]
    assert len(confirmed_posts) == 1
    confirmed_payload = confirmed_posts[0][0][1]
    assert set(confirmed_payload.keys()) == {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "appointment",
    }
    assert len(email_posts) == 1
    email_payload = email_posts[0][0][1]
    assert email_payload["message"]["subject"].startswith(
        "Confirmación de tu cita —"
    )
    assert set(email_payload["recipient"].keys()) == {"to", "patient_name"}
    for event_type, event_id in (
        (automation_content.EVENT_TYPE, f"appointment.confirmed:{appointment.id}:v1"),
        (
            "appointment.confirmation_email",
            f"appointment.confirmation_email:{appointment.id}:v1",
        ),
    ):
        event = booking.email_service.events_repository.get_by_event_id(
            event_id, database_path
        )
        assert event is not None
        assert event.event_type == event_type
        assert event.status == "sent"

    import ast

    stdlib_by_module = {
        "consultorio/services/email_service.py": {"re", "urllib", "datetime"},
        "consultorio/services/appointment_service.py": {
            "re",
            "sqlite3",
            "datetime",
            "pathlib",
        },
        "consultorio/persistence/appointments_repository.py": {
            "sqlite3",
            "dataclasses",
            "pathlib",
        },
        "consultorio/persistence/database.py": {
            "shutil",
            "sqlite3",
            "datetime",
            "pathlib",
        },
    }
    for relative_path, stdlib_allowed in stdlib_by_module.items():
        source = Path(relative_path).read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    root = alias.name.split(".")[0]
                    assert root in stdlib_allowed or root.startswith(
                        "consultorio"
                    ), f"{relative_path}: {root}"
            elif isinstance(node, ast.ImportFrom):
                root = (node.module or "").split(".")[0]
                assert root in stdlib_allowed or root.startswith(
                    "consultorio"
                ), f"{relative_path}: {root}"
