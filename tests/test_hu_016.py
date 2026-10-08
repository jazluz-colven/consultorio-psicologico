import re

from consultorio.config import Config
from tests import expected_content as expected

MAIN_CSS = (Config.STATIC_DIR / "css" / "main.css").read_text(encoding="utf-8")


def test_tc_016_009_estilos_del_buscador_conformes_a_pantalla_y_paleta() -> None:
    assert ".site-search" in MAIN_CSS
    assert ".site-search__input" in MAIN_CSS
    assert ".site-search__button" in MAIN_CSS
    assert ".search-result" in MAIN_CSS

    media_rules = re.findall(r"@media[^{]+", MAIN_CSS)
    assert any("(max-width: 767px)" in rule for rule in media_rules)
    assert any("(min-width: 768px)" in rule for rule in media_rules)

    used = set(re.findall(r"#[0-9A-Fa-f]{6}", MAIN_CSS))
    assert used <= expected.PALETTE


def test_tc_016_010_regresion_de_paginas_principales_con_buscador_presente(
    client,
) -> None:
    for path in ("/", "/nosotros", "/servicios"):
        response = client.get(path)
        assert response.status_code == 200, path

        html = response.get_data(as_text=True)
        assert f'action="{expected.SEARCH_URL}"' in html, path
        assert "<nav" in html, path

    assert client.get("/ruta-inexistente").status_code == 404

    for item in expected.NAV_LINKS:
        response = client.get(item["url"])
        assert response.status_code == 200, item["url"]
