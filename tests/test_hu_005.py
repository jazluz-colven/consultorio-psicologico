import re

from consultorio.config import Config

from tests import expected_content as expected

MAIN_CSS = Config.STATIC_DIR / "css" / "main.css"
AVAILABILITY_JS = Config.STATIC_DIR / "js" / "availability.js"


def _main_html(html: str) -> str:
    match = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    assert match is not None
    return match.group(1)


def test_tc_005_014_leyenda_estados_visuales_y_data_attrs(client) -> None:
    html = client.get("/citas").get_data(as_text=True)
    main = _main_html(html)

    assert 'class="appointment__calendar-legend"' in main
    assert expected.CALENDAR_LEGEND_FREE in main
    assert expected.CALENDAR_LEGEND_FULL in main
    assert 'data-checking="' in main
    assert 'data-occupied-label="' in main
    assert 'data-day-no-hours="' in main
    assert 'data-slot-taken="' in main

    css = MAIN_CSS.read_text(encoding="utf-8")
    for rule in (
        ".appointment__calendar-day.is-full",
        ".appointment__hour--taken",
        ".appointment__calendar-legend",
        ".appointment__legend-item--free",
        ".appointment__legend-item--full",
        ".appointment__hour-badge",
    ):
        assert rule in css, rule
    used = set(re.findall(r"#[0-9A-Fa-f]{6}", css))
    assert used <= expected.PALETTE
    assert re.search(
        r"\.appointment__helper\s*\{[^}]*text-align:\s*justify;[^}]*hyphens:\s*none",
        css,
    )


def test_tc_005_015_js_estados_guard_carga_y_ocupadas() -> None:
    js = AVAILABILITY_JS.read_text(encoding="utf-8")
    for token in (
        "/citas/disponibilidad",
        "is-full",
        "seq",
        "data-checking",
        "data-occupied-label",
        "data-day-no-hours",
        "data-slot-taken",
        "loadDayStates",
        "appointment__hour--taken",
        "booking-calendar",
        "refreshHours",
        "isBookable",
        "/citas/horarios",
    ):
        assert token in js, token
    assert "import " not in js
    assert "import(" not in js
    assert re.search(r"if\s*\(\s*seq\s*!==\s*hoursSeq\s*\)", js)
    assert re.search(r"if\s*\(\s*seq\s*!==\s*daySeq\s*\)", js)


def test_tc_005_016_regresion_carga_inicial_14_radios_y_suite_intacta(client) -> None:
    html = client.get("/citas").get_data(as_text=True)
    main = _main_html(html)
    q = chr(34)
    assert main.count("name=" + q + "time" + q) == len(expected.BOOKING_HOURS)
    taken = main.count('class="appointment__hour appointment__hour--taken"')
    assert taken == 0
    assert f'data-occupied-label="{expected.MSG_OCCUPIED_HOUR}"' in html
