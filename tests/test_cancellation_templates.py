"""Template tests for HU-017 cancellation screens (spec 017, T4).

Covers the contractual copy rendered by ``templates/cancellation/*.html``
(RF-3, RF-7), the RF-10 double-submit guard and the minimal styles added to
``static/css/main.css`` (Serenidad Natural palette, justified paragraphs).
"""

import re
from pathlib import Path

import pytest
from flask import render_template

from consultorio.config import Config
from consultorio.content import appointment_content
from consultorio.content import cancellation_content as cc
from consultorio.services.home_service import get_home_view

TEMPLATES_DIR = Path(Config.TEMPLATES_DIR)
STATIC_DIR = Path(Config.STATIC_DIR)
MAIN_CSS = (STATIC_DIR / "css" / "main.css").read_text(encoding="utf-8")
CANCELLATION_JS = STATIC_DIR / "js" / "cancellation.js"

VERIFY_CONTEXT = {
    "page_title": cc.CANCEL_PAGE_TITLE,
    "notice": cc.CANCEL_NOTICE,
    "label_reference": cc.LABEL_REFERENCE,
    "label_document_number": cc.LABEL_DOCUMENT_NUMBER,
    "button_label": cc.CANCEL_BUTTON_LABEL,
    "cita_id": 42,
}

SUMMARY_CONTEXT = {
    "page_title": cc.CANCEL_PAGE_TITLE,
    "label_reference": cc.LABEL_REFERENCE,
    "label_service": cc.LABEL_SERVICE,
    "label_date": cc.LABEL_DATE,
    "label_time": cc.LABEL_TIME,
    "label_status": cc.LABEL_STATUS,
    "confirm_button": cc.CANCEL_CONFIRM_BUTTON,
    "back_button": cc.CANCEL_BACK_BUTTON,
    "cita_id": 42,
    "service_name": "Psiconutrición",
    "formatted_date": "martes, 3 de noviembre de 2026",
    "appointment_time": "10:30",
    "status_label": appointment_content.STATUS_CONFIRMED_LABEL,
    "document_number": "99887766",
    # Personal data deliberately supplied to prove the screen never renders it.
    "patient_name": "Ana Pérez",
    "email": "ana@ejemplo.test",
    "phone": "3001234567",
}

SUCCESS_CONTEXT = {
    "success_title": cc.CANCEL_SUCCESS_TITLE,
    "success_message": cc.CANCEL_SUCCESS_MESSAGE,
    "label_reference": cc.LABEL_REFERENCE,
    "label_service": cc.LABEL_SERVICE,
    "label_date": cc.LABEL_DATE,
    "label_time": cc.LABEL_TIME,
    "label_status": cc.LABEL_STATUS,
    "cita_id": 42,
    "service_name": "Psiconutrición",
    "formatted_date": "martes, 3 de noviembre de 2026",
    "appointment_time": "10:30",
    "status_label": cc.STATUS_CANCELLED_LABEL,
    # Personal data deliberately supplied to prove the screen never renders it.
    "document_number": "99887766",
    "patient_name": "Ana Pérez",
    "email": "ana@ejemplo.test",
    "phone": "3001234567",
}


def _render(app, template_name: str, **context: object) -> str:
    with app.app_context(), app.test_request_context():
        return render_template(template_name, view=get_home_view(), **context)


def _css_rule(selector: str) -> str:
    match = re.search(re.escape(selector) + r"\s*\{([^}]*)\}", MAIN_CSS)
    assert match is not None, selector
    return match.group(1)


# --- verify.html (RF-3, Q-C) -------------------------------------------------


def test_verify_muestra_literales_aviso_previo_y_referencia(app) -> None:
    html = _render(app, "cancellation/verify.html", **VERIFY_CONTEXT)

    assert cc.CANCEL_PAGE_TITLE in html
    assert cc.CANCEL_NOTICE in html
    assert cc.LABEL_REFERENCE in html
    assert "#42" in html
    assert cc.LABEL_DOCUMENT_NUMBER in html
    assert cc.CANCEL_BUTTON_LABEL in html


def test_verify_formulario_de_documento_obligatorio_y_numerico(app) -> None:
    html = _render(app, "cancellation/verify.html", **VERIFY_CONTEXT)

    assert 'action="/citas/cancelar/42"' in html
    assert 'method="post"' in html
    field = re.search(
        r'<input(?=[^>]*\bname="document_number")[^>]*>', html
    )
    assert field is not None
    tag = field.group(0)
    assert 'inputmode="numeric"' in tag
    assert "required" in tag
    assert 'pattern="[0-9]+"' in tag
    assert 'aria-live="polite"' in html


@pytest.mark.parametrize(
    "message",
    [
        cc.MSG_VERIFICATION_FAILED,
        cc.MSG_ALREADY_CANCELLED,
        cc.MSG_NOTICE_PERIOD,
    ],
)
def test_verify_muestra_el_mensaje_recibido_por_contexto(app, message) -> None:
    html = _render(
        app, "cancellation/verify.html", message=message, **VERIFY_CONTEXT
    )

    assert message in html
    assert 'role="alert"' in html


# --- summary.html (RF-3, RF-8, RF-10, D12) ----------------------------------


def test_summary_muestra_datos_de_la_cita_y_botones(app) -> None:
    html = _render(app, "cancellation/summary.html", **SUMMARY_CONTEXT)

    for literal in (
        cc.LABEL_SERVICE,
        cc.LABEL_DATE,
        cc.LABEL_TIME,
        cc.LABEL_STATUS,
        cc.LABEL_REFERENCE,
        "Psiconutrición",
        "martes, 3 de noviembre de 2026",
        "10:30",
        appointment_content.STATUS_CONFIRMED_LABEL,
        "#42",
        cc.CANCEL_CONFIRM_BUTTON,
        cc.CANCEL_BACK_BUTTON,
    ):
        assert literal in html, literal

    assert 'action="/citas/cancelar/42/confirmar"' in html
    assert 'href="/citas/confirmada/42"' in html


def test_summary_envia_el_documento_solo_en_campo_oculto(app) -> None:
    html = _render(app, "cancellation/summary.html", **SUMMARY_CONTEXT)

    hidden = re.search(
        r"<input(?=[^>]*\btype=\"hidden\")(?=[^>]*\bname=\"document_number\")[^>]*>",
        html,
    )
    assert hidden is not None
    assert 'value="99887766"' in hidden.group(0)
    assert html.count("99887766") == 1


def test_summary_carga_solo_el_script_de_cancelacion(app) -> None:
    html = _render(app, "cancellation/summary.html", **SUMMARY_CONTEXT)

    assert "js/cancellation.js" in html


# --- success.html (RF-7, D12) ------------------------------------------------


def test_success_muestra_titulo_mensaje_estado_y_datos(app) -> None:
    html = _render(app, "cancellation/success.html", **SUCCESS_CONTEXT)

    for literal in (
        cc.CANCEL_SUCCESS_TITLE,
        cc.CANCEL_SUCCESS_MESSAGE,
        cc.STATUS_CANCELLED_LABEL,
        cc.LABEL_SERVICE,
        cc.LABEL_DATE,
        cc.LABEL_TIME,
        cc.LABEL_STATUS,
        cc.LABEL_REFERENCE,
        "Psiconutrición",
        "martes, 3 de noviembre de 2026",
        "10:30",
        "#42",
    ):
        assert literal in html, literal

    assert re.search(r'<a[^>]+href="/"', html) is not None


# --- Privacy (D12) -----------------------------------------------------------


@pytest.mark.parametrize("template_name", ["summary.html", "success.html"])
def test_resumen_y_exito_no_muestran_datos_personales(
    app, template_name: str
) -> None:
    context = SUMMARY_CONTEXT if template_name == "summary.html" else SUCCESS_CONTEXT
    html = _render(app, f"cancellation/{template_name}", **context)

    for personal in ("Ana Pérez", "ana@ejemplo.test", "3001234567"):
        assert personal not in html, personal
    # On the success screen the document must not appear at all.
    if template_name == "success.html":
        assert "99887766" not in html


@pytest.mark.parametrize("template_name", ["summary.html", "success.html"])
def test_plantillas_no_referencian_campos_personales(template_name: str) -> None:
    source = (TEMPLATES_DIR / "cancellation" / template_name).read_text(
        encoding="utf-8"
    )

    for personal_field in ("patient_name", ".email", ".phone", "appointment.document_number"):
        assert personal_field not in source, personal_field


# --- RF-10 guard and assets --------------------------------------------------


def test_cancellation_js_aplica_el_guard_de_doble_envio() -> None:
    script = CANCELLATION_JS.read_text(encoding="utf-8")

    assert 'addEventListener("submit"' in script
    assert "submitting" in script
    assert "preventDefault" in script
    assert ".disabled = true" in script
    assert "aria-busy" in script
    assert 'setAttribute("aria-busy", "true")' in script


def test_solo_el_resumen_referencia_el_script_de_cancelacion() -> None:
    referencing = [
        path.relative_to(TEMPLATES_DIR).as_posix()
        for path in TEMPLATES_DIR.rglob("*.html")
        if "cancellation.js" in path.read_text(encoding="utf-8")
    ]

    assert referencing == ["cancellation/summary.html"]


def test_css_de_cancelacion_no_introduce_colores_fuera_de_la_paleta() -> None:
    from tests import expected_content as expected

    used = set(re.findall(r"#[0-9a-fA-F]{6}", MAIN_CSS))
    assert used <= expected.PALETTE


def test_css_de_cancelacion_justifica_parrafos_y_muestra_foco() -> None:
    for selector in (
        ".cancellation__notice",
        ".cancellation__message",
        ".cancellation__success-message",
    ):
        rule = _css_rule(selector)
        assert "text-align: justify" in rule, selector
        assert "hyphens: none" in rule, selector

    for selector in (
        ".cancellation__input:focus-visible",
        ".cancellation__back-link:focus-visible",
    ):
        assert selector in MAIN_CSS, selector
