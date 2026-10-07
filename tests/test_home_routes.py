import re

from tests import expected_content as expected


def _home_html(client) -> str:
    response = client.get("/")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def test_get_home_devuelve_presentacion_clara(client) -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.content_type.startswith("text/html")

    html = response.get_data(as_text=True)
    assert f"<h1>{expected.BRAND_NAME}</h1>" in html
    assert expected.INTRO in html
    assert expected.TAGLINE in html


def test_get_home_muestra_imagen_representativa(client) -> None:
    html = _home_html(client)

    match = re.search(r"<img[^>]*>", html)
    assert match is not None

    image_tag = match.group(0)
    assert f'alt="{expected.HERO_ALT}"' in image_tag
    assert f'filename="{expected.HERO_SRC}"' in html or expected.HERO_SRC in image_tag


def test_get_home_muestra_accesos_de_navegacion(client) -> None:
    html = _home_html(client)

    nav_html = re.search(r"<nav[^>]*>.*?</nav>", html, re.S).group(0)
    hrefs = re.findall(r'<a href="([^"]+)"', nav_html)

    assert len(hrefs) == 6
    assert hrefs == [item["url"] for item in expected.NAV_LINKS]
    for item in expected.NAV_LINKS:
        assert item["label"] in nav_html


def test_post_home_devuelve_405(client) -> None:
    response = client.post("/")

    assert response.status_code == 405
    assert client.get("/").status_code == 200


def test_home_no_contiene_formularios_ni_administracion(client) -> None:
    html = _home_html(client).lower()

    assert "<form" not in html
    assert "<input" not in html
    assert "type=\"password\"" not in html
    assert "admin" not in html


def test_home_muestra_marca_secundaria(client) -> None:
    html = _home_html(client)

    brand_index = html.find(expected.SECONDARY_BRAND)
    heading_index = html.find("<h1")

    assert brand_index != -1
    assert heading_index != -1
    assert brand_index < heading_index


def test_bloque_servicios_enlaza_a_servicios(client) -> None:
    html = _home_html(client)

    assert expected.SERVICES_TITLE in html
    for item in expected.SERVICES:
        assert item["name"] in html
        assert item["summary"] in html
    assert expected.SERVICES_LINK_LABEL in html
    assert f'href="{expected.SERVICES_LINK_URL}"' in html
    assert client.get(expected.SERVICES_LINK_URL).status_code == 200


def test_frase_de_valores_esta_presente(client) -> None:
    html = _home_html(client)

    assert expected.TRUST_LINE in html


def test_secciones_sin_implementar_responden_200(client) -> None:
    for path in expected.PLACEHOLDER_SECTIONS:
        response = client.get(path)

        assert response.status_code == 200, path
        assert "Sección en construcción." in response.get_data(as_text=True)


def test_toda_ruta_de_navegacion_responde_200(client) -> None:
    for item in expected.NAV_LINKS:
        response = client.get(item["url"])

        assert response.status_code == 200, item["url"]

        html = response.get_data(as_text=True)
        assert "Volver al inicio" in html or item["url"] == "/"
        assert "<nav" in html


def test_ruta_desconocida_devuelve_404(client) -> None:
    response = client.get("/ruta-inexistente")

    assert response.status_code == 404
    assert "Página no encontrada" in response.get_data(as_text=True)
