"""HU-017 web routes — T5: verification form and summary (spec 017).

Covers TC-017-001 (RF-1, RF-2: uniform GET, indistinguishable failure, no
appointment data), TC-017-002 (RF-3: summary without changes) and the route
part of TC-017-003 (RF-4: 3-hour window). The appointments are inserted
directly through the repository with a start time computed from
``datetime.now()`` so the window is deterministic without depending on the
office schedule.
"""

import re
import sqlite3
import urllib.error
from datetime import date, datetime, timedelta
from pathlib import Path
from unittest import mock

import pytest

from consultorio.content import appointment_content
from consultorio.content import cancellation_content as cc
from consultorio.content.services_catalog import SERVICES_CATALOG
from consultorio.persistence import appointments_repository as repository
from consultorio.persistence.appointments_repository import Appointment
from consultorio.services import automation_service as automation
from consultorio.services.email_service import format_spanish_date

SERVICE_KEY = "nutrition"
SERVICE_NAME = str(SERVICES_CATALOG[SERVICE_KEY]["name"])
DOCUMENT_NUMBER = "1234567890"
WRONG_DOCUMENT = "9999999999"
PATIENT_NAME = "Paciente de prueba"
PATIENT_EMAIL = "paciente@ejemplo.test"
PATIENT_PHONE = "3001234567"
MISSING_ID = 999999
BOOKING_SLOT = "09:00"
WEBHOOK_URL = "http://n8n.local/webhook/booking"
CANCELLATION_EMAIL_EVENT_TYPE = "appointment.cancellation_email"


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


def _cancel_in_database(app, appointment_id: int) -> Appointment:
    """Mark an existing appointment as cancelled through the repository."""
    updated = repository.update_appointment_status(
        appointment_id,
        appointment_content.STATUS_CANCELLED,
        _database_path(app),
    )
    assert updated is not None
    return updated


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


def _future_weekday(days_ahead: int = 2) -> str:
    """A bookable weekday (>= today) far enough away for the 3-hour window.

    Computed from ``date.today()`` and never from a fixed calendar date, so the
    test does not depend on the clock and the booking rules accept it.
    """
    candidate = date.today() + timedelta(days=days_ahead)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


def _insert_appointment_on(
    app, booking_date: str, slot: str = BOOKING_SLOT
) -> Appointment:
    """Insert a confirmed appointment on a concrete weekday and slot."""
    data = {
        "document_type": "CC",
        "document_number": DOCUMENT_NUMBER,
        "patient_name": PATIENT_NAME,
        "email": PATIENT_EMAIL,
        "phone": PATIENT_PHONE,
        "service": SERVICE_KEY,
        "date": booking_date,
        "time": slot,
    }
    return repository.insert_appointment(data, _database_path(app))


def _cancellation_email_event_id(cita_id: int) -> str:
    return f"{CANCELLATION_EMAIL_EVENT_TYPE}:{cita_id}:v1"


def _count_events(app, event_id: str) -> int:
    connection = sqlite3.connect(str(_database_path(app)))
    try:
        return connection.execute(
            "SELECT COUNT(*) FROM automation_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()[0]
    finally:
        connection.close()


def _event_status(app, event_id: str) -> str | None:
    connection = sqlite3.connect(str(_database_path(app)))
    try:
        row = connection.execute(
            "SELECT status FROM automation_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()
    finally:
        connection.close()
    return row[0] if row is not None else None


def _cancellation_posts(post: mock.MagicMock) -> list[mock.call]:
    """Webhook POSTs for the cancellation e-mail (same filter as HU-010)."""
    return [
        call
        for call in post.call_args_list
        if call[0][1].get("event_type") == CANCELLATION_EMAIL_EVENT_TYPE
    ]


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


# --- T6: execution (POST .../confirmar) and success (GET .../exito) ----------


def test_tc_017_004_flujo_completo_cancela_libera_horario_y_permite_rereserva(
    app, client
) -> None:
    """RF-5, RF-6, RF-7: verification -> summary -> confirmation -> success;
    the row becomes `cancelled`, the slot is free and the re-booking returns
    303 (TC-017-004)."""
    booking_date = _future_weekday()
    created = _insert_appointment_on(app, booking_date)

    # (1) verification -> (2) summary, still read-only.
    summary = client.post(
        f"/citas/cancelar/{created.id}",
        data={"document_number": DOCUMENT_NUMBER},
    )
    assert summary.status_code == 200
    assert cc.CANCEL_CONFIRM_BUTTON in summary.get_data(as_text=True)
    assert _current(app, created.id).status == appointment_content.STATUS_CONFIRMED

    # Before cancelling, the slot is occupied.
    before_hours = client.get(
        "/citas/horarios",
        query_string={"service": SERVICE_KEY, "date": booking_date},
    )
    assert before_hours.status_code == 200
    assert BOOKING_SLOT in before_hours.get_json()["occupied"]
    assert BOOKING_SLOT not in before_hours.get_json()["available"]

    # (3) execution -> 303 PRG to the success screen.
    confirmation = client.post(
        f"/citas/cancelar/{created.id}/confirmar",
        data={"document_number": DOCUMENT_NUMBER},
    )
    assert confirmation.status_code == 303
    assert confirmation.headers["Location"].endswith(
        f"/citas/cancelar/{created.id}/exito"
    )

    # (4) success screen with the contractual copy, data and reference.
    success = client.get(f"/citas/cancelar/{created.id}/exito")
    assert success.status_code == 200
    html = success.get_data(as_text=True)
    for literal in (
        cc.CANCEL_SUCCESS_TITLE,
        cc.CANCEL_SUCCESS_MESSAGE,
        appointment_content.STATUS_CANCELLED_LABEL,
        cc.LABEL_SERVICE,
        cc.LABEL_DATE,
        cc.LABEL_TIME,
        cc.LABEL_STATUS,
        cc.LABEL_REFERENCE,
        SERVICE_NAME,
        format_spanish_date(created.date),
        created.time,
        f"#{created.id}",
    ):
        assert literal in html, literal
    # D12: the success screen never exposes personal data.
    for forbidden in (PATIENT_NAME, PATIENT_EMAIL, PATIENT_PHONE, DOCUMENT_NUMBER):
        assert forbidden not in html, forbidden

    assert _current(app, created.id).status == appointment_content.STATUS_CANCELLED

    # RF-6: the slot is free again and can be booked once more (303).
    after_hours = client.get(
        "/citas/horarios",
        query_string={"service": SERVICE_KEY, "date": booking_date},
    )
    assert after_hours.status_code == 200
    assert BOOKING_SLOT in after_hours.get_json()["available"]
    assert BOOKING_SLOT not in after_hours.get_json()["occupied"]

    rebooking = client.post(
        "/citas",
        data={
            "service": SERVICE_KEY,
            "date": booking_date,
            "time": BOOKING_SLOT,
            "document_type": "CC",
            "document_number": "5555555555",
            "patient_name": "Otro Paciente",
            "email": "otro@ejemplo.test",
            "phone": "3005555555",
        },
    )
    assert rebooking.status_code == 303


def test_tc_017_004_exito_sin_cancelacion_redirige_a_verificacion(app, client) -> None:
    """D2: the success URL only renders after a cancellation; otherwise it
    redirects (303) to the verification step."""
    created = _insert_appointment_on(app, _future_weekday())

    confirmed = client.get(f"/citas/cancelar/{created.id}/exito")
    assert confirmed.status_code == 303
    assert confirmed.headers["Location"].endswith(f"/citas/cancelar/{created.id}")

    missing = client.get(f"/citas/cancelar/{MISSING_ID}/exito")
    assert missing.status_code == 303
    assert missing.headers["Location"].endswith(f"/citas/cancelar/{MISSING_ID}")


def test_tc_017_004_confirmar_too_soon_no_cambia_nada(app, client) -> None:
    """RF-4: inside the 3-hour window the confirmation maps to the restriction
    literal and writes nothing."""
    created = _insert_appointment(app, 2)
    before = _current(app, created.id)

    response = client.post(
        f"/citas/cancelar/{created.id}/confirmar",
        data={"document_number": DOCUMENT_NUMBER},
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert cc.MSG_NOTICE_PERIOD in html
    assert cc.MSG_VERIFICATION_FAILED not in html
    assert _current(app, created.id) == before


def test_tc_017_004_confirmar_documento_incorrecto_no_cambia_nada(app, client) -> None:
    """RF-1/RF-2: a wrong document on the confirmation maps to FAILED with no
    appointment data and no change."""
    created = _insert_appointment_on(app, _future_weekday())
    before = _current(app, created.id)

    response = client.post(
        f"/citas/cancelar/{created.id}/confirmar",
        data={"document_number": WRONG_DOCUMENT},
    )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert cc.MSG_VERIFICATION_FAILED in html
    assert cc.MSG_ALREADY_CANCELLED not in html
    assert SERVICE_NAME not in html
    assert format_spanish_date(created.date) not in html
    assert _current(app, created.id) == before


def test_tc_017_004_confirmar_referencia_inexistente_failed(app, client) -> None:
    """Plan D7: APPOINTMENT_NOT_FOUND/unknown reference on confirmation maps to
    the same FAILED literal with 200."""
    response = client.post(
        f"/citas/cancelar/{MISSING_ID}/confirmar",
        data={"document_number": DOCUMENT_NUMBER},
    )

    assert response.status_code == 200
    assert cc.MSG_VERIFICATION_FAILED in response.get_data(as_text=True)


def test_tc_017_005_primera_cancelacion_exactamente_un_evento(app, client) -> None:
    """RF-8: the first cancellation from the site emits exactly one
    `appointment.cancellation_email` event (and one POST)."""
    app.config["AUTOMATION_WEBHOOK_URL"] = WEBHOOK_URL
    created = _insert_appointment_on(app, _future_weekday())
    event_id = _cancellation_email_event_id(created.id)

    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        response = client.post(
            f"/citas/cancelar/{created.id}/confirmar",
            data={"document_number": DOCUMENT_NUMBER},
        )

    assert response.status_code == 303
    assert len(_cancellation_posts(post)) == 1
    assert _count_events(app, event_id) == 1
    assert _event_status(app, event_id) == "sent"
    assert _current(app, created.id).status == appointment_content.STATUS_CANCELLED


def test_tc_017_005_webhook_caido_evento_failed_y_cancelacion_intacta(
    app, client
) -> None:
    """RF-8 / Spec 010 contract: a down webhook leaves the event `failed` but
    the cancellation is committed and the 303 is still produced."""
    app.config["AUTOMATION_WEBHOOK_URL"] = WEBHOOK_URL
    created = _insert_appointment_on(app, _future_weekday())
    event_id = _cancellation_email_event_id(created.id)

    with mock.patch.object(
        automation,
        "_post_webhook",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        response = client.post(
            f"/citas/cancelar/{created.id}/confirmar",
            data={"document_number": DOCUMENT_NUMBER},
        )

    assert response.status_code == 303
    assert response.headers["Location"].endswith(
        f"/citas/cancelar/{created.id}/exito"
    )
    assert _current(app, created.id).status == appointment_content.STATUS_CANCELLED
    assert _count_events(app, event_id) == 1
    assert _event_status(app, event_id) == "failed"


def test_tc_017_006_reenvio_muestra_ya_cancelada_un_evento_cero_posts(
    app, client
) -> None:
    """RF-9/RF-8: resending the confirmation answers «Esta cita ya fue
    cancelada.», keeps exactly one event row and adds 0 POSTs."""
    app.config["AUTOMATION_WEBHOOK_URL"] = WEBHOOK_URL
    created = _insert_appointment_on(app, _future_weekday())
    event_id = _cancellation_email_event_id(created.id)

    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        first = client.post(
            f"/citas/cancelar/{created.id}/confirmar",
            data={"document_number": DOCUMENT_NUMBER},
        )
        assert first.status_code == 303
        posts_after_first = post.call_count

        second = client.post(
            f"/citas/cancelar/{created.id}/confirmar",
            data={"document_number": DOCUMENT_NUMBER},
        )

    assert second.status_code == 200
    assert cc.MSG_ALREADY_CANCELLED in second.get_data(as_text=True)
    assert post.call_count == posts_after_first  # 0 additional POSTs
    assert len(_cancellation_posts(post)) == 1
    assert _count_events(app, event_id) == 1
    assert _event_status(app, event_id) == "sent"
    assert _current(app, created.id).status == appointment_content.STATUS_CANCELLED


# --- TC-017-008 (RF-11, RF-12): real status and cancel button ----------------
# The confirmed-appointment page shows the status read from the database and
# only offers the cancellation entry point for `confirmed` appointments.


def test_tc_017_008_cita_confirmada_muestra_estado_y_boton_cancelar(
    app, client
) -> None:
    """RF-12: a confirmed appointment shows «Confirmada» and a «Cancelar cita»
    link to the verification step."""
    created = _insert_appointment(app, 6)

    response = client.get(f"/citas/confirmada/{created.id}")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert appointment_content.STATUS_CONFIRMED_LABEL in html
    assert appointment_content.STATUS_CANCELLED_LABEL not in html
    assert cc.CANCEL_BUTTON_LABEL in html
    assert f'href="/citas/cancelar/{created.id}"' in html
    link = re.search(
        rf'<a[^>]*href="/citas/cancelar/{created.id}"[^>]*>(.*?)</a>',
        html,
        re.DOTALL,
    )
    assert link is not None
    assert cc.CANCEL_BUTTON_LABEL in link.group(1)


def test_tc_017_008_cita_cancelada_muestra_estado_sin_boton(app, client) -> None:
    """RF-11: a cancelled appointment shows «Cancelada» (200, not 404) and no
    cancellation button."""
    created = _insert_appointment(app, 6)
    _cancel_in_database(app, created.id)

    response = client.get(f"/citas/confirmada/{created.id}")

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert appointment_content.STATUS_CANCELLED_LABEL in html
    assert appointment_content.STATUS_CONFIRMED_LABEL not in html
    assert cc.CANCEL_BUTTON_LABEL not in html
    assert f'/citas/cancelar/{created.id}"' not in html


def test_tc_017_008_id_desconocido_404(client) -> None:
    """The unknown-id behaviour stays a 404 (regression guard)."""
    response = client.get(f"/citas/confirmada/{MISSING_ID}")

    assert response.status_code == 404
