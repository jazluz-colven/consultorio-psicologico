import re

from tests import expected_content as expected


def _services_html(client) -> str:
    response = client.get("/servicios")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def _main_html(html: str) -> str:
    match = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    assert match is not None
    return match.group(1)


def test_get_servicios_muestra_titulo_y_los_dos_nombres(client) -> None:
    main = _main_html(_services_html(client))

    assert '<h1 class="services-page__title">Servicios</h1>' in main
    for service in expected.SERVICES_CATALOG.values():
        assert f'<h2 class="services-page__block-title">{service["name"]}</h2>' in main


def test_get_servicios_muestra_dos_secciones_con_descripcion_y_beneficios(client) -> None:
    main = _main_html(_services_html(client))

    sections = re.findall(r'<section class="services-page__block">(.*?)</section>', main, re.S)
    assert len(sections) == 2
    for section, service in zip(sections, expected.SERVICES_CATALOG.values()):
        assert service["description"] in section
        assert '<ul class="services-page__benefits">' in section
        for benefit in service["benefits"]:
            assert f'<li class="services-page__benefit">{benefit}</li>' in section


def test_metodos_escritores_devuelven_405(client) -> None:
    for method in (client.post, client.put, client.delete):
        response = method("/servicios")
        assert response.status_code == 405


def test_subrecurso_desconocido_devuelve_404(client) -> None:
    response = client.get("/servicios/psicologia")

    assert response.status_code == 404
    html = response.get_data(as_text=True)
    assert "<h1>Página no encontrada</h1>" in html
    assert "La página que buscas no existe o ya no está disponible." in html


def test_regresion_placeholders_y_navegacion(client) -> None:
    assert "/servicios" not in expected.PLACEHOLDER_SECTIONS
    for path in expected.PLACEHOLDER_SECTIONS:
        response = client.get(path)

        assert response.status_code == 200, path
        assert "Sección en construcción." in response.get_data(as_text=True)

    assert client.get("/").status_code == 200
    assert client.get("/nosotros").status_code == 200

    nav_html = re.search(r"<nav[^>]*>.*?</nav>", _services_html(client), re.S).group(0)
    hrefs = re.findall(r'<a href="([^"]+)"', nav_html)

    assert len(hrefs) == 6
    for href in hrefs:
        assert client.get(href).status_code == 200, href
