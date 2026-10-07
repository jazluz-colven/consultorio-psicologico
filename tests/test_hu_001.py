import re
from pathlib import Path

from consultorio.config import Config

from tests import expected_content as expected

MAIN_CSS = Path(Config.STATIC_DIR) / "css" / "main.css"


def test_home_es_responsive(client) -> None:
    html = client.get("/").get_data(as_text=True)
    css = MAIN_CSS.read_text(encoding="utf-8")

    assert 'name="viewport"' in html
    assert "@media" in css
    assert "@media (max-width" in css
    assert re.search(r'<img[^>]*width="\d+"[^>]*height="\d+"', html, re.S)


def test_css_usa_solo_colores_de_la_paleta() -> None:
    css = MAIN_CSS.read_text(encoding="utf-8")
    used = set(re.findall(r"#[0-9a-fA-F]{6}", css))

    assert used
    assert used <= expected.PALETTE


def test_navegacion_principal_funciona_de_extremo_a_extremo(client) -> None:
    html = client.get("/").get_data(as_text=True)
    nav_html = re.search(r"<nav[^>]*>.*?</nav>", html, re.S).group(0)
    hrefs = re.findall(r'<a href="([^"]+)"', nav_html)

    assert hrefs
    for href in hrefs:
        assert client.get(href).status_code == 200, href
