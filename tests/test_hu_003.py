import re
from pathlib import Path

from consultorio.config import Config

from tests import expected_content as expected

MAIN_CSS = Path(Config.STATIC_DIR) / "css" / "main.css"


def _main_html(html: str) -> str:
    match = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    assert match is not None
    return match.group(1)


def test_servicios_es_responsive_con_medida_y_justificacion(client) -> None:
    html = client.get("/servicios").get_data(as_text=True)
    css = MAIN_CSS.read_text(encoding="utf-8")

    assert 'name="viewport"' in html
    assert re.search(r"@media\s*\(max-width", css)
    assert re.search(r"\.services-page__block\s*\{[^}]*max-width:\s*\d+ch", css)
    assert re.search(
        r"\.services-page__text\s*\{[^}]*text-align:\s*justify;[^}]*hyphens:\s*none", css
    )
    assert re.search(
        r"\.services-page__image\s*\{[^}]*aspect-ratio:\s*2\s*/\s*1;[^}]*object-fit:\s*cover;[^}]*border-radius:\s*\d+px",
        css,
    )


def test_css_sigue_usando_solo_colores_de_la_paleta() -> None:
    css = MAIN_CSS.read_text(encoding="utf-8")
    used = set(re.findall(r"#[0-9a-fA-F]{6}", css))

    assert used
    assert used <= expected.PALETTE


def test_e2e_de_portada_a_servicios_y_vuelta(client) -> None:
    home = client.get("/")

    assert home.status_code == 200
    home_html = home.get_data(as_text=True)
    assert expected.SERVICES_LINK_URL in home_html
    assert expected.SERVICES_LINK_LABEL in home_html

    services = client.get(expected.SERVICES_LINK_URL)

    assert services.status_code == 200
    html = services.get_data(as_text=True)
    assert '<h1 class="services-page__title">Servicios</h1>' in html
    assert "Psicología Integral" in html
    assert "Volver al inicio" in html
    assert client.get("/").status_code == 200


def test_servicios_sin_cta_de_agendamiento(client) -> None:
    main = _main_html(client.get("/servicios").get_data(as_text=True))

    assert "<form" not in main
    assert "<input" not in main
    assert 'href="/citas"' not in main
