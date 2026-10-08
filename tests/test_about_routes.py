import re

from tests import expected_content as expected


def _about_html(client) -> str:
    response = client.get("/nosotros")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def _main_html(html: str) -> str:
    match = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    assert match is not None
    return match.group(1)


def test_get_nosotros_muestra_los_cuatro_bloques(client) -> None:
    html = _about_html(client)

    assert '<h1 class="about__title">Nosotros</h1>' in html
    for title in expected.ABOUT_BLOCK_TITLES.values():
        assert f'<h2 class="about__block-title">{title}</h2>' in html
    for text in expected.ABOUT_CONTENT.values():
        assert text in html


def test_post_nosotros_devuelve_405(client) -> None:
    response = client.post("/nosotros")

    assert response.status_code == 405


def test_informacion_diferenciada_de_servicios_y_citas(client) -> None:
    main = _main_html(_about_html(client))

    for phrase in (
        "Psicología Integral",
        "Psiconutrición",
        "Ver todos los servicios",
        "Agendar cita",
    ):
        assert phrase not in main
    assert "<form" not in main
    assert "<input" not in main


def test_secciones_restantes_siguen_en_construccion(client) -> None:
    assert "/nosotros" not in expected.PLACEHOLDER_SECTIONS
    for path in expected.PLACEHOLDER_SECTIONS:
        response = client.get(path)

        assert response.status_code == 200, path
        assert "Sección en construcción." in response.get_data(as_text=True)

    assert "Sección en construcción." not in _about_html(client)


def test_navegacion_en_nosotros_responde_200(client) -> None:
    html = _about_html(client)
    nav_html = re.search(r"<nav[^>]*>.*?</nav>", html, re.S).group(0)
    hrefs = re.findall(r'<a href="([^"]+)"', nav_html)

    assert len(hrefs) == 6
    for href in hrefs:
        assert client.get(href).status_code == 200, href
