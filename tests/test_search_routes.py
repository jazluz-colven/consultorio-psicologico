import re
from urllib.parse import quote

from tests import expected_content as expected

PAGES_USING_BASE = [
    "/",
    "/nosotros",
    "/servicios",
    "/articulos",
    "/contacto",
    "/citas",
]


def _get(client, url: str):
    response = client.get(url)
    assert response.status_code == 200, url
    return response


def test_tc_016_005_busqueda_con_resultados_muestra_titulo_extracto_y_enlace(
    client,
) -> None:
    response = _get(client, f"{expected.SEARCH_URL}?q={quote('psicología')}")
    html = response.get_data(as_text=True)

    assert expected.SEARCH_RESULTS_TITLE in html
    assert expected.SEARCH_RESULTS_STATUS in html
    assert 'class="search-result"' in html

    result_items = re.findall(
        r'<li class="search-result">.*?<a href="([^"]+)">(.*?)</a>',
        html,
        re.S,
    )
    assert len(result_items) >= 1
    assert any(url == "/servicios" for url, _ in result_items)


def test_tc_016_006_busqueda_insensible_a_mayusculas_y_acentos(client) -> None:
    for query in ("psiconutricion", "PSICONUTRICION", "Psiconutrición"):
        response = _get(client, f"{expected.SEARCH_URL}?q={quote(query)}")
        html = response.get_data(as_text=True)

        assert "Psiconutrición" in html, query
        assert expected.SEARCH_NO_RESULTS_PREFIX not in html, query


def test_tc_016_007_consulta_vacia_y_sin_coincidencias_respuesta_200(client) -> None:
    for url in (f"{expected.SEARCH_URL}?q=", f"{expected.SEARCH_URL}?q=%20%20%20"):
        response = client.get(url)
        html = response.get_data(as_text=True)

        assert response.status_code == 200, url
        assert expected.SEARCH_EMPTY_MESSAGE in html, url

    response = client.get(f"{expected.SEARCH_URL}?q=zzzzz")
    html = response.get_data(as_text=True)

    assert response.status_code == 200
    assert html.count(expected.SEARCH_NO_RESULTS_PREFIX) == 1
    assert "«zzzzz»" in html


def test_tc_016_008_formulario_en_cabecera_fuera_del_nav_y_post_405(client) -> None:
    for path in PAGES_USING_BASE:
        html = _get(client, path).get_data(as_text=True)

        assert f'action="{expected.SEARCH_URL}"' in html, path
        assert f'name="{expected.SEARCH_QUERY_PARAM}"' in html, path
        assert expected.SEARCH_PLACEHOLDER in html, path
        assert expected.SEARCH_LABEL in html, path

        nav_html = re.search(r"<nav[^>]*>.*?</nav>", html, re.S).group(0)
        assert "<form" not in nav_html, path

        form_position = html.find('<form class="site-search"')
        nav_end = html.find("</nav>")
        assert nav_end != -1 and form_position > nav_end, path

    search_html = _get(
        client, f"{expected.SEARCH_URL}?q={quote('psicologia')}"
    ).get_data(as_text=True)
    assert f'action="{expected.SEARCH_URL}"' in search_html

    response = client.post(expected.SEARCH_URL, data={"q": "psicología"})
    assert response.status_code == 405
