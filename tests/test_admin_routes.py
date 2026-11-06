"""HU-018 admin routes — T3 (spec 018).

Covers the token guard (TC-018-001), the detail view with its mandatory
summary and both forms (TC-018-002), the missing reference (TC-018-003), the
delegated cancellation (TC-018-004) and the RF-7 submit guard (TC-018-013).

The token is a fixed test value in a local ``TempConfig``; the real token only
lives in the environment (spec 018 RNF).
"""

import re
from datetime import date, timedelta
from pathlib import Path

import pytest

from consultorio import create_app
from consultorio.config import Config, TestConfig
from consultorio.content import admin_content as ac
from consultorio.content.appointment_content import (
    BOOKING_HOURS,
    STATUS_CANCELLED,
    STATUS_CANCELLED_LABEL,
    STATUS_CONFIRMED_LABEL,
)
from consultorio.content.services_catalog import SERVICES_CATALOG
from consultorio.persistence import appointments_repository as repository
from consultorio.persistence.appointments_repository import Appointment
from consultorio.services.email_service import format_spanish_date

TOKEN = "test-admin-token"
SERVICE_KEY = "nutrition"
SERVICE_NAME = str(SERVICES_CATALOG[SERVICE_KEY]["name"])
DOCUMENT_NUMBER = "1234567890"
PATIENT_NAME = "Paciente de prueba"
PATIENT_EMAIL = "paciente@ejemplo.test"
PATIENT_PHONE = "3001234567"
MISSING_ID = 999999
ADMIN_JS = Config.STATIC_DIR / "js" / "admin.js"


def _future_weekday() -> str:
    candidate = date.today()
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


def _database_path(app) -> Path:
    return Path(app.config["DATABASE_PATH"])


def _insert_appointment(app, slot: str = "09:00") -> Appointment:
    data = {
        "document_type": "CC",
        "document_number": DOCUMENT_NUMBER,
        "patient_name": PATIENT_NAME,
        "email": PATIENT_EMAIL,
        "phone": PATIENT_PHONE,
        "service": SERVICE_KEY,
        "date": _future_weekday(),
        "time": slot,
    }
    return repository.insert_appointment(data, _database_path(app))


def _assert_denied(response, forbidden: tuple[str, ...]) -> None:
    assert response.status_code == 403
    html = response.get_data(as_text=True)
    assert ac.ADMIN_ACCESS_DENIED in html
    assert response.headers["Cache-Control"] == "no-store"
    assert response.headers["Referrer-Policy"] == "no-referrer"
    for value in forbidden:
        assert value not in html, value


@pytest.fixture()
def admin_app(tmp_path: Path):
    class TempConfig(TestConfig):
        DATABASE_PATH: Path = tmp_path / "admin.db"
        CONSULTORIO_ADMIN_TOKEN: str = TOKEN

    application = create_app(TempConfig)
    application.config.update(TESTING=True)
    yield application


@pytest.fixture()
def admin_client(admin_app):
    return admin_app.test_client()


def test_tc_018_001_token_ausente_incorrecto_none_no_ascii_y_config_vacia(
    admin_app, admin_client, tmp_path: Path
) -> None:
    created = _insert_appointment(admin_app)
    detail_path = f"/admin/citas/{created.id}"
    cancel_path = f"/admin/citas/{created.id}/cancelar"
    forbidden = (
        PATIENT_NAME,
        PATIENT_EMAIL,
        PATIENT_PHONE,
        DOCUMENT_NUMBER,
        SERVICE_NAME,
        created.time,
        format_spanish_date(created.date),
    )

    denied_cases = (
        ("get", {"path": detail_path}),
        ("get", {"path": detail_path, "headers": {"X-Admin-Token": "wrong"}}),
        ("get", {"path": detail_path, "query_string": {"token": ""}}),
        ("get", {"path": detail_path, "query_string": {"token": "wrong"}}),
        ("get", {"path": detail_path, "query_string": {"token": "ñ"}}),
        ("post", {"path": cancel_path}),
        ("post", {"path": cancel_path, "headers": {"X-Admin-Token": "wrong"}}),
        ("post", {"path": cancel_path, "data": {"admin_token": ""}}),
        ("post", {"path": cancel_path, "data": {"admin_token": "wrong"}}),
        ("post", {"path": cancel_path, "data": {"admin_token": "ñ"}}),
        # D2: ?token= is accepted on GET only; a POST ignores it.
        ("post", {"path": cancel_path, "query_string": {"token": TOKEN}}),
    )
    for method, kwargs in denied_cases:
        _assert_denied(getattr(admin_client, method)(**kwargs), forbidden)

    # An empty configured token disables the surface, even with the right text.
    class EmptyTokenConfig(TestConfig):
        DATABASE_PATH: Path = tmp_path / "empty.db"
        CONSULTORIO_ADMIN_TOKEN: str = ""

    empty_app = create_app(EmptyTokenConfig)
    empty_client = empty_app.test_client()
    _assert_denied(
        empty_client.get(detail_path, headers={"X-Admin-Token": TOKEN}),
        forbidden,
    )
    _assert_denied(
        empty_client.post(cancel_path, data={"admin_token": TOKEN}),
        forbidden,
    )

    # No cancellation happened while rejecting every request.
    current = repository.get_appointment_by_id(
        created.id, _database_path(admin_app)
    )
    assert current is not None
    assert current.status == "confirmed"


def test_tc_018_002_get_detalle_con_token_resumen_formularios_y_cancelada(
    admin_app, admin_client
) -> None:
    created = _insert_appointment(admin_app)
    path = f"/admin/citas/{created.id}"

    for response in (
        admin_client.get(path, headers={"X-Admin-Token": TOKEN}),
        admin_client.get(path, query_string={"token": TOKEN}),
    ):
        assert response.status_code == 200
        html = response.get_data(as_text=True)

        # Mandatory summary (RF-2).
        assert PATIENT_NAME in html
        assert SERVICE_NAME in html
        assert format_spanish_date(created.date) in html
        assert created.time in html
        assert STATUS_CONFIRMED_LABEL in html
        assert ac.ADMIN_LABEL_PATIENT in html
        assert ac.ADMIN_LABEL_SUMMARY in html

        # Both forms with their contractual copy and hidden token.
        assert "admin__cancel-form" in html
        assert "admin__reschedule-form" in html
        assert ac.ADMIN_CANCEL_NOTICE in html
        assert ac.ADMIN_CANCEL_BUTTON in html
        assert ac.ADMIN_RESCHEDULE_NOTICE in html
        assert ac.ADMIN_RESCHEDULE_BUTTON in html
        hidden = re.search(
            r'<input(?=[^>]*\btype="hidden")'
            r'(?=[^>]*\bname="admin_token")[^>]*>',
            html,
        )
        assert hidden is not None
        assert f'value="{TOKEN}"' in hidden.group(0)

        # The reschedule form is fed by the real catalog and the 14 hours.
        for item in SERVICES_CATALOG.values():
            assert str(item["name"]) in html
        for hour in BOOKING_HOURS:
            assert f'value="{hour}"' in html

        date_input = re.search(r'<input[^>]*\btype="date"[^>]*>', html)
        assert date_input is not None
        assert 'name="date"' in date_input.group(0)

        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["Referrer-Policy"] == "no-referrer"

    # A cancelled appointment keeps the summary but loses the operative forms.
    repository.update_appointment_status(
        created.id, STATUS_CANCELLED, _database_path(admin_app)
    )
    cancelled = admin_client.get(path, headers={"X-Admin-Token": TOKEN})
    assert cancelled.status_code == 200
    html = cancelled.get_data(as_text=True)
    assert STATUS_CANCELLED_LABEL in html
    assert STATUS_CONFIRMED_LABEL not in html
    assert "admin__form" not in html
    assert ac.ADMIN_CANCEL_BUTTON not in html
    assert ac.ADMIN_RESCHEDULE_BUTTON not in html


def test_tc_018_003_cita_inexistente_404(admin_app, admin_client) -> None:
    responses = (
        admin_client.get(
            f"/admin/citas/{MISSING_ID}", headers={"X-Admin-Token": TOKEN}
        ),
        admin_client.post(
            f"/admin/citas/{MISSING_ID}/cancelar",
            data={"admin_token": TOKEN},
        ),
    )

    for response in responses:
        assert response.status_code == 404
        html = response.get_data(as_text=True)
        assert ac.ADMIN_APPOINTMENT_NOT_FOUND in html
        assert ac.ADMIN_ACCESS_DENIED not in html
        assert response.headers["Cache-Control"] == "no-store"
        assert response.headers["Referrer-Policy"] == "no-referrer"


def test_tc_018_004_post_cancelar_con_cabecera_y_con_campo_oculto(
    admin_app, admin_client
) -> None:
    with_header = _insert_appointment(admin_app, "08:00")
    with_field = _insert_appointment(admin_app, "08:30")

    header_response = admin_client.post(
        f"/admin/citas/{with_header.id}/cancelar",
        headers={"X-Admin-Token": TOKEN},
    )
    assert header_response.status_code == 200
    header_html = header_response.get_data(as_text=True)
    assert ac.ADMIN_CANCEL_SUCCESS in header_html
    assert ac.ADMIN_MSG_ALREADY_CANCELLED not in header_html
    assert header_response.headers["Cache-Control"] == "no-store"
    assert header_response.headers["Referrer-Policy"] == "no-referrer"

    field_response = admin_client.post(
        f"/admin/citas/{with_field.id}/cancelar",
        data={"admin_token": TOKEN},
    )
    assert field_response.status_code == 200
    field_html = field_response.get_data(as_text=True)
    assert ac.ADMIN_CANCEL_SUCCESS in field_html
    assert ac.ADMIN_MSG_ALREADY_CANCELLED not in field_html

    for appointment in (with_header, with_field):
        current = repository.get_appointment_by_id(
            appointment.id, _database_path(admin_app)
        )
        assert current is not None
        assert current.status == STATUS_CANCELLED

    # Re-posting a cancelled appointment is a safe conflict, not a new cancel.
    repeat = admin_client.post(
        f"/admin/citas/{with_header.id}/cancelar",
        data={"admin_token": TOKEN},
    )
    assert repeat.status_code == 200
    repeat_html = repeat.get_data(as_text=True)
    assert ac.ADMIN_MSG_ALREADY_CANCELLED in repeat_html
    assert ac.ADMIN_CANCEL_SUCCESS not in repeat_html


def test_tc_018_013_guard_rf_7_en_html_y_admin_js(admin_app, admin_client) -> None:
    created = _insert_appointment(admin_app)
    response = admin_client.get(
        f"/admin/citas/{created.id}", headers={"X-Admin-Token": TOKEN}
    )
    assert response.status_code == 200
    html = response.get_data(as_text=True)

    assert re.search(r'<script[^>]+src="[^"]*js/admin\.js"', html) is not None

    for form_class in ("admin__cancel-form", "admin__reschedule-form"):
        form = re.search(
            rf'<form[^>]*class="[^"]*{form_class}[^"]*"[^>]*>', html
        )
        assert form is not None
        assert "admin__form" in form.group(0)

    buttons = re.findall(
        r'<button[^>]*class="[^"]*admin__submit[^"]*"[^>]*>', html
    )
    assert len(buttons) == 2
    for button in buttons:
        assert "disabled" not in button
        assert "aria-busy" not in button

    js = ADMIN_JS.read_text(encoding="utf-8")
    assert 'querySelectorAll(".admin__form")' in js
    assert re.search(
        r'if\s*\(\s*submitting\s*\)\s*\{[^}]*event\.preventDefault\(\)',
        js,
        re.S,
    )
    assert "button.disabled = true" in js
    assert 'form.setAttribute("aria-busy", "true")' in js
    assert "initAdminForms" in js
    assert "import " not in js
    assert "import(" not in js
    assert "require(" not in js
