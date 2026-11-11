"""HU-010 — Notificar la cancelación de una cita (Spec 010, enmienda 2026-10-13).

T10: the remaining Spec 010 criteria run against the isolated PostgreSQL
schema of the ``database`` fixture.

TC-010-014 (the legacy SQLite schema migration) was relocated to
``tests/test_rollback_sqlite.py``: it verifies the SQLite rollback route and is
NOT part of the PostgreSQL parity suite (Spec 019 plan D9, RF-28).

TC-010-013/015/016/017: re-reserva, HTTP, espejo+config y regresión funcional.
"""

from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from consultorio.config import Config
from consultorio.content import appointment_content as content
from consultorio.content import automation_content
from consultorio.content import email_content
from consultorio.services import appointment_service as booking
from consultorio.services import automation_service as automation

from tests import expected_content as expected

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


def _appointment_count(database) -> int:
    with database.connection() as connection:
        row = connection.execute(
            "SELECT COUNT(*) AS total FROM appointments"
        ).fetchone()
    return int(row["total"])


def test_tc_010_013_tras_cancelar_se_puede_re_reservar(
    database,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database)
    cancelled = booking.cancel_appointment(created.id, database)
    assert isinstance(cancelled, booking.Appointment)
    assert cancelled.status == "cancelled"

    rebooked = booking.create_booking(_booking_data(booking_date), database)
    assert isinstance(rebooked, booking.Appointment)
    assert rebooked.id != created.id
    assert rebooked.status == "confirmed"

    original = booking.repository.get_appointment_by_id(created.id, database)
    assert original is not None
    assert original.status == "cancelled"
    assert _appointment_count(database) == 2


def test_tc_010_015_http_horarios_disponibilidad_y_re_reserva(
    client, database
) -> None:
    booking_date = _future_weekday()
    response = client.post("/citas", data=_booking_data(booking_date))
    assert response.status_code == 303
    cita_id = int(response.headers["Location"].rstrip("/").split("/")[-1])

    cancelled = booking.cancel_appointment(cita_id, database)
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
    assert _appointment_count(database) == 2


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
    database,
) -> None:
    booking_date = _future_weekday()
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        appointment = booking.create_booking(
            _booking_data(booking_date), database, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(appointment, booking.Appointment)
    assert appointment.status == "confirmed"

    hours = dict(
        booking.get_hours_with_status(SERVICE_KEY, booking_date, database)
    )
    assert hours[SLOT] is False

    conflict = booking.create_booking(
        _booking_data(booking_date), database, WEBHOOK_URL, TIMEOUT
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
            event_id, database
        )
        assert event is not None
        assert event.event_type == event_type
        assert event.status == "sent"

    import ast

    stdlib_by_module = {
        "consultorio/services/email_service.py": {"re", "urllib", "datetime"},
        "consultorio/services/appointment_service.py": {
            "re",
            "datetime",
            "pathlib",
        },
        "consultorio/persistence/appointments_repository.py": {
            "sqlite3",
            "dataclasses",
            "pathlib",
            # HU-019 T5 (plan D8/D13): one SQL source runs on PostgreSQL and
            # the SQLite rollback route. ``contextlib`` provides the connection
            # scope and ``typing`` the row-mapping/iterator annotations. The
            # driver itself is not imported at module level.
            "contextlib",
            "typing",
        },
        "consultorio/persistence/database.py": {
            "shutil",
            "sqlite3",
            "datetime",
            "pathlib",
            # HU-019 T3 (plan D3): request-scoped reuse, per-instance
            # BoundedSemaphore/threading.Lock and context managers. ``flask``
            # is the project's existing core dependency (flask.g), not a new
            # or alternative persistence dependency.
            "threading",
            "contextlib",
            "dataclasses",
            "typing",
            "flask",
            # HU-019 T2/T3: the approved PostgreSQL driver (D1), imported
            # lazily inside the connection factory.
            "psycopg",
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
