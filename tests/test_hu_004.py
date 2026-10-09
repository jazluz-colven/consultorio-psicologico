import re
from datetime import date, timedelta
from pathlib import Path

from consultorio.config import Config

from tests import expected_content as expected

MAIN_CSS = Config.STATIC_DIR / "css" / "main.css"
AVAILABILITY_JS = Config.STATIC_DIR / "js" / "availability.js"


def _future_weekday() -> str:
    candidate = date.today()
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


def _main_html(html: str) -> str:
    match = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    assert match is not None
    return match.group(1)


def test_tc_004_024_rnf2_responsive_paleta_justificacion_y_js_sin_dependencias(
    client,
) -> None:
    html = client.get("/citas").get_data(as_text=True)
    assert 'name="viewport"' in html

    css = MAIN_CSS.read_text(encoding="utf-8")
    assert re.search(r"@media[^{]*\(max-width", css)
    used = set(re.findall(r"#[0-9A-Fa-f]{6}", css))
    assert used
    assert used <= expected.PALETTE
    assert re.search(
        r"\.appointment__helper\s*\{[^}]*text-align:\s*justify;[^}]*hyphens:\s*none",
        css,
    )
    assert re.search(
        r"\.appointment__summary-value\s*\{[^}]*text-align:\s*justify;[^}]*hyphens:\s*none",
        css,
    )
    fixed_widths = [
        int(value)
        for value in re.findall(r"\.appointment[^{]*\{[^}]*width:\s*(\d+)px", css)
    ]
    assert all(width <= 375 for width in fixed_widths)

    js = AVAILABILITY_JS.read_text(encoding="utf-8")
    assert "fetch(" in js
    assert "import " not in js
    assert "import(" not in js
    assert "require(" not in js


def test_tc_004_025_rnf1_formulario_estrictamente_de_8_campos(client) -> None:
    html = client.get("/citas").get_data(as_text=True)
    main = _main_html(html)
    forms = re.findall(r"<form[^>]*>(.*?)</form>", main, re.S)
    assert len(forms) == 1
    booking_form = forms[0]
    names = re.findall(r'name="([a-z_]+)"', booking_form)
    assert sorted(set(names)) == sorted(
        [
            "service",
            "date",
            "time",
            "document_type",
            "document_number",
            "patient_name",
            "email",
            "phone",
        ]
    )
    assert "<textarea" not in booking_form
    lowered = booking_form.lower()
    for forbidden in ("dirección", "direccion", "motivo", "teléfono fijo", "telefono fijo"):
        assert forbidden not in lowered


def test_tc_004_026_e2e_home_agendar_submit_confirmacion(client) -> None:
    home = client.get("/")
    assert home.status_code == 200
    assert 'href="/citas"' in home.get_data(as_text=True)

    page = client.get("/citas")
    assert page.status_code == 200

    response = client.post(
        "/citas",
        data={
            "service": "psychology_integral",
            "date": _future_weekday(),
            "time": "10:00",
            "document_type": "CC",
            "document_number": "987654321",
            "patient_name": "María López",
            "email": "maria@correo.com",
            "phone": "3109876543",
        },
    )
    assert response.status_code == 303
    confirmation = client.get(response.headers["Location"])
    assert confirmation.status_code == 200
    html = confirmation.get_data(as_text=True)
    assert expected.CONFIRMATION_TITLE in html
    assert expected.STATUS_PENDING_LABEL in html
    assert "María López" in html
    assert "10:00" in html
    assert "Psicología Integral" in html


def test_tc_004_027_fuera_de_alcance_sin_correo_whatsapp_ni_cancelacion(
    client,
) -> None:
    html = client.get("/citas").get_data(as_text=True).lower()
    for forbidden in ("whatsapp", "correo de confirmación", "cancelar", "n8n"):
        assert forbidden not in html, forbidden

    home = _main_html(client.get("/").get_data(as_text=True))
    assert "<form" not in home
    assert "<input" not in home

    services = _main_html(client.get("/servicios").get_data(as_text=True))
    assert "<form" not in services
    assert "<input" not in services


def test_tc_004_028_d19_layout_dos_columnas_datepicker_y_bloques_de_horas(
    client,
) -> None:
    html = client.get("/citas").get_data(as_text=True)
    main = _main_html(html)

    assert 'class="appointment__layout"' in main
    assert main.count('class="appointment__panel"') == 2
    assert expected.BOOKING_PATIENT_SECTION_TITLE in main
    assert expected.BOOKING_SCHEDULE_SECTION_TITLE in main

    assert 'id="booking-calendar"' in main
    assert re.search(r'id="booking-calendar"[^>]*data-today="\d{4}-\d{2}-\d{2}"', main)
    assert 'type="date"' not in main
    assert 'id="calendar-grid"' in main
    assert 'id="calendar-prev"' in main
    assert 'id="calendar-next"' in main
    assert 'name="date"' in main

    assert expected.BOOKING_BLOCK_MORNING in main
    assert expected.BOOKING_BLOCK_AFTERNOON in main
    assert main.count('name="time"') == len(expected.BOOKING_HOURS)
    morning = re.search(
        r'id="hours-morning">(.*?)</div>', main, re.S
    )
    afternoon = re.search(
        r'id="hours-afternoon">(.*?)</div>', main, re.S
    )
    assert morning is not None and afternoon is not None
    morning_hours = re.findall(r'value="(\d{2}:\d{2})"', morning.group(1))
    afternoon_hours = re.findall(r'value="(\d{2}:\d{2})"', afternoon.group(1))
    assert morning_hours == expected.BOOKING_HOURS[:8]
    assert afternoon_hours == expected.BOOKING_HOURS[8:]

    css = MAIN_CSS.read_text(encoding="utf-8")
    for rule in (
        ".appointment__layout",
        ".appointment__panel",
        ".appointment__calendar",
        ".appointment__calendar-grid",
        ".appointment__calendar-day.is-bookable",
        ".appointment__calendar-day.is-disabled",
        ".appointment__calendar-day.is-selected",
        ".appointment__hours-block",
        ".appointment__hours-list",
    ):
        assert rule in css, rule
    assert re.search(r"\.appointment__layout\s*\{[^}]*flex-direction:\s*row", css)

    js = AVAILABILITY_JS.read_text(encoding="utf-8")
    for token in (
        "booking-calendar",
        "calendar-grid",
        "calendar-prev",
        "calendar-next",
        "refreshHours",
        "isBookable",
        "/citas/horarios",
    ):
        assert token in js, token
