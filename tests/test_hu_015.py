import re
from pathlib import Path

from consultorio.config import Config

from tests import expected_content as expected

MAIN_CSS = Path(Config.STATIC_DIR) / "css" / "main.css"


def _main_html(html: str) -> str:
    match = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    assert match is not None
    return match.group(1)


def test_tc_015_015_contacto_es_responsive_con_medida_y_justificacion(client) -> None:
    html = client.get("/contacto").get_data(as_text=True)
    css = MAIN_CSS.read_text(encoding="utf-8")

    assert 'name="viewport"' in html
    assert re.search(r"@media\s*\(max-width", css)
    assert re.search(r"\.contact\s*\{[^}]*max-width:\s*\d+ch", css)
    assert re.search(
        r"\.contact__value\s*\{[^}]*text-align:\s*justify;[^}]*hyphens:\s*none", css
    )
    assert re.search(
        r"\.contact__row\s*\{[^}]*\}", css
    )
    assert re.search(
        r"@media\s*\(min-width:\s*900px\)[^{]*\{[^}]*\.contact\s*\{[^}]*"
        r"grid-template-columns:[^}]*\}",
        css,
        re.S,
    )

    used = set(re.findall(r"#[0-9a-fA-F]{6}", css))
    assert used
    assert used <= expected.PALETTE


def test_tc_015_016_e2e_desde_portada_y_fuera_de_alcance(client) -> None:
    home = client.get("/")

    assert home.status_code == 200
    home_html = home.get_data(as_text=True)
    assert 'href="/contacto"' in home_html

    contact = client.get("/contacto")

    assert contact.status_code == 200
    html = contact.get_data(as_text=True)
    assert '<h1 class="contact__title">Contacto</h1>' in html
    assert "Volver al inicio" in html

    back = client.get("/")
    assert back.status_code == 200

    main = _main_html(html)
    assert "<form" not in main
    assert "<input" not in main
    for forbidden in ("chat en línea", "formulario de contacto", "Enviar mensaje"):
        assert forbidden not in main
