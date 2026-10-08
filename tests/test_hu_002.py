import re
from pathlib import Path

from consultorio.config import Config

from tests import expected_content as expected

MAIN_CSS = Path(Config.STATIC_DIR) / "css" / "main.css"


def test_nosotros_es_responsive(client) -> None:
    html = client.get("/nosotros").get_data(as_text=True)
    css = MAIN_CSS.read_text(encoding="utf-8")

    assert 'name="viewport"' in html
    assert "@media (max-width" in css


def test_css_sigue_usando_solo_colores_de_la_paleta() -> None:
    css = MAIN_CSS.read_text(encoding="utf-8")
    used = set(re.findall(r"#[0-9a-fA-F]{6}", css))

    assert used
    assert used <= expected.PALETTE


def test_estructura_de_cuatro_bloques_con_medida(client) -> None:
    html = client.get("/nosotros").get_data(as_text=True)
    css = MAIN_CSS.read_text(encoding="utf-8")

    assert html.count('<h2 class="about__block-title">') == 4
    assert re.search(r"\.about\s*\{[^}]*max-width:\s*\d+ch", css)


def test_e2e_de_portada_a_nosotros(client) -> None:
    home = client.get("/")

    assert home.status_code == 200
    assert 'href="/nosotros"' in home.get_data(as_text=True)

    about = client.get("/nosotros")

    assert about.status_code == 200
    html = about.get_data(as_text=True)
    assert expected.ABOUT_CONTENT["mission"] in html
    assert "Volver al inicio" in html
    assert client.get("/").status_code == 200
