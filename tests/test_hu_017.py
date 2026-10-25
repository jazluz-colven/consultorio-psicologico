"""HU-017 web routes — T5: verification form and summary (spec 017).

Covers TC-017-001 (RF-1, RF-2: uniform GET, indistinguishable failure, no
appointment data), TC-017-002 (RF-3: summary without changes) and the route
part of TC-017-003 (RF-4: 3-hour window). The appointments are inserted
directly through the repository with a start time computed from
``datetime.now()`` so the window is deterministic without depending on the
office schedule.
"""

import re
from datetime import datetime, timedelta
from pathlib import Path

import pytest

from consultorio.content import appointment_content
from consultorio.content import cancellation_content as cc
from consultorio.content.services_catalog import SERVICES_CATALOG
from consultorio.persistence import appointments_repository as repository
from consultorio.persistence.appointments_repository import Appointment
from consultorio.services.email_service import format_spanish_date

SERVICE_KEY = "nutrition"
SERVICE_NAME = str(SERVICES_CATALOG[SERVICE_KEY]["name"])
DOCUMENT_NUMBER = "1234567890"
WRONG_DOCUMENT = "9999999999"
PATIENT_NAME = "Paciente de prueba"
PATIENT_EMAIL = "paciente@ejemplo.test"
PATIENT_PHONE = "3001234567"
MISSING_ID = 999999


def _database_path(app) -> Path:
    return Path(app.config["DATABASE_PATH"])


def _insert_appointment(app, hours_from_now: int) -> Appointment:
    """Insert a confirmed appointment starting ``hours_from_now`` from now."""
    start = datetime.now() + timedelta(hours=hours_from_now)
    data = {
        "document_type": "CC",
        "document_number": DOCUMENT_NUMBER,
        "patient_name": PATIENT_NAME,
        "email": PATIENT_EMAIL,
        "phone": PATIENT_PHONE,
        "service": SERVICE_KEY,
        "date": start.date().isoformat(),
        "time": start.strftime("%H:%M"),
    }
    return repository.insert_appointment(data, _database_path(app))


def _current(app, appointment_id: int) -> Appointment:
    current = repository.get_appointment_by_id(appointment_id, _database_path(app))
    assert current is not None
    return current


def _article(html: str, cita_id: int) -> str:
    """Extract the cancellation card and normalise only its own reference."""
    match = re.search(
        r'<article class="cancellation">.*?</article>', html, re.DOTALL
    )
    assert match is not None
    return (
        match.group(0)
        .replace(f"/citas/cancelar/{cita_id}", "/citas/cancelar/ID")
        .replace(f"#{cita_id}", "#ID")
    )


# --- TC-017-001 (RF-1, RF-2) -------------------------------------------------


def test_tc_017_001_get_verificacion_es_uniforme_exista_o_no_la_cita(
    app, client
) -> None:
    created = _insert_appointment(app, 6)

    existing = client.get(f"/citas/cancelar/{created.id}")
    missing = client.get(f"/citas/cancelar/{MISSING_ID}")

    assert existing.status_code == 200
    assert missing.status_code == 200

    for html in (
        existing.get_data(as_text=True),
        missing.get_data(as_text=True),
    ):
        assert cc.CANCEL_PAGE_TITLE in html
        assert cc.CANCEL_NOTICE in html
        assert cc.LABEL_REFERENCE in html
        assert cc.LABEL_DOCUMENT_NUMBER in html
        assert cc.CANCEL_BUTTON_LABEL in html
        assert 'name="document_number"' in html

    assert _article(
        existing.get_data(as_text=True), created.id
    ) == _article(missing.get_data(as_text=True), MISSING_ID)

    # A non-numeric reference is a malformed URL: Flask's <int> converter
    # answers 404 without disclosing anything (plan D4, Q-E).
    assert client.get("/citas/cancelar/no-numerico").status_code == 404


def test_tc_017_001_post_inexistente_y_documento_incorrecto_mismo_literal_sin_datos(
    app, client
) -> None:
    created = _insert_appointment(app, 6)
    before = _current(app, created.id)

    responses = (
        client.post(
            f"/citas/cancelar/{MISSING_ID}",
            data={"document_number": DOCUMENT_NUMBER},
        ),
        client.post(
            f"/citas/cancelar/{created.id}",
            data={"document_number": WRONG_DOCUMENT},
        ),
    )

    for response in responses:
        assert response.status_code == 200
        html = response.get_data(as_text=True)
        assert cc.MSG_VERIFICATION_FAILED in html
        assert cc.MSG_ALREADY_CANCELLED not in html
        assert cc.MSG_NOTICE_PERIOD not in html
        for forbidden in (
            PATIENT_NAME,
            PATIENT_EMAIL,
            PATIENT_PHONE,
            DOCUMENT_NUMBER,
            SERVICE_NAME,
            created.date,
            created.time,
        ):
            assert forbidden not in html, forbidden

    # RF-1/RF-2: verification performs no change at all.
    assert _current(app, created.id) == before


def test_tc_017_001_documento_vacio_o_con_formato_invalido_no_cambia_nada(
    app, client
) -> None:
    created = _insert_appointment(app, 6)
    before = _current(app, created.id)

    cases = (
        ("", appointment_content.MSG_REQUIRED_DOC_NUMBER),
        ("12AB", appointment_content.MSG_INVALID_DOC_NUMBER),
        ("123", appointment_content.MSG_INVALID_DOC_NUMBER),
    )
    for document, message in cases:
        response = client.post(
            f"/citas/cancelar/{created.id}",
            data={"document_number": document},
        )
        assert response.status_code == 200, document
        html = response.get_data(as_text=True)
        assert message in html, document
        assert cc.MSG_VERIFICATION_FAILED not in html, document

    assert _current(app, created.id) == before


# --- TC-017-002 (RF-3) -------------------------------------------------------


def test_tc_017_002_post_correcto_renderiza_resumen_sin_cambios(
    app, client
) -> None:
    created = _insert_appointment(app, 6)
    before = _current(app, created.id)
    formatted_date = format_spanish_date(created.date)

    response = client.post(
        f"/citas/cancelar/{created.id}",
        data={"document_number": DOCUMENT_NUMBER},
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    for literal in (
        cc.CANCEL_PAGE_TITLE,
        cc.LABEL_REFERENCE,
        cc.LABEL_SERVICE,
        cc.LABEL_DATE,
        cc.LABEL_TIME,
        cc.LABEL_STATUS,
        SERVICE_NAME,
        formatted_date,
        created.time,
        appointment_content.STATUS_CONFIRMED_LABEL,
        f"#{created.id}",
        cc.CANCEL_CONFIRM_BUTTON,
        cc.CANCEL_BACK_BUTTON,
    ):
        assert literal in html, literal

    # The weekday is part of the legible date (plan D11).
    assert formatted_date.split(",")[0] in html
    assert f'action="/citas/cancelar/{created.id}/confirmar"' in html
    assert f'href="/citas/confirmada/{created.id}"' in html
    hidden = re.search(
        r'<input(?=[^>]*\btype="hidden")(?=[^>]*\bname="document_number")[^>]*>',
        html,
    )
    assert hidden is not None
    assert f'value="{DOCUMENT_NUMBER}"' in hidden.group(0)

    # RF-3: the summary is still read-only.
    assert _current(app, created.id) == before


# --- TC-017-003, route part (RF-4) ------------------------------------------


def test_tc_017_003_cita_a_dos_horas_muestra_restriccion_sin_cambios(
    app, client
) -> None:
    created = _insert_appointment(app, 2)
    before = _current(app, created.id)

    response = client.post(
        f"/citas/cancelar/{created.id}",
        data={"document_number": DOCUMENT_NUMBER},
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert cc.MSG_NOTICE_PERIOD in html
    assert cc.MSG_VERIFICATION_FAILED not in html
    assert SERVICE_NAME not in html
    assert format_spanish_date(created.date) not in html
    assert _current(app, created.id) == before


def test_tc_017_003_cita_a_seis_horas_muestra_resumen_sin_cambios(
    app, client
) -> None:
    created = _insert_appointment(app, 6)
    before = _current(app, created.id)

    response = client.post(
        f"/citas/cancelar/{created.id}",
        data={"document_number": DOCUMENT_NUMBER},
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert cc.MSG_NOTICE_PERIOD not in html
    assert SERVICE_NAME in html
    assert format_spanish_date(created.date) in html
    assert _current(app, created.id) == before
