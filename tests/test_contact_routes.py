import re

from tests import expected_content as expected


def _contact_html(client) -> str:
    response = client.get("/contacto")
    assert response.status_code == 200
    return response.get_data(as_text=True)


def _main_html(html: str) -> str:
    match = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    assert match is not None
    return match.group(1)


def test_tc_015_009_get_contacto_muestra_titulo_y_bloques(client) -> None:
    main = _main_html(_contact_html(client))

    assert '<h1 class="contact__title">Contacto</h1>' in main
    assert main.count('<section class="contact__block">') >= 4


def test_tc_015_010_muestra_direccion_whatsapp_y_correo_sin_bloque_telefono(client) -> None:
    main = _main_html(_contact_html(client))

    assert expected.CONTACT_BLOCK_LABELS["address"] in main
    for line in expected.CONTACT_ADDRESS_LINES:
        assert line in main
    assert '<a href="https://wa.me/573168756020">+573168756020</a>' in main
    assert (
        f'<a href="mailto:{expected.CONTACT_EMAIL}">{expected.CONTACT_EMAIL}</a>'
        in main
    )
    assert expected.CONTACT_BLOCK_LABELS["phone"] not in main
    assert "tel:" not in main


def test_tc_015_011_muestra_horarios_y_redes_sociales(client) -> None:
    main = _main_html(_contact_html(client))

    assert expected.CONTACT_BLOCK_LABELS["hours"] in main
    for hour in expected.CONTACT_OFFICE_HOURS:
        assert hour["label"] in main
        assert hour["days"] in main
        assert hour["hours"] in main

    assert expected.CONTACT_BLOCK_LABELS["social"] in main
    for social in expected.CONTACT_SOCIAL_LINKS:
        assert (
            f'<a href="{social["url"]}" target="_blank" rel="noopener">'
            f'{social["label"]}</a>' in main
        )


def test_tc_015_012_cada_canal_esta_en_su_propia_seccion_con_h2(client) -> None:
    main = _main_html(_contact_html(client))

    sections = re.findall(
        r'<section class="contact__block">(.*?)</section>', main, re.S
    )
    assert len(sections) == 5
    for section in sections:
        assert re.search(r'<h2 class="contact__block-title">[^<]+</h2>', section)

    whatsapp_section = next(s for s in sections if "wa.me" in s)
    assert "mailto:" not in whatsapp_section
    assert "Calle 34" not in whatsapp_section

    email_section = next(s for s in sections if "mailto:" in s)
    assert "wa.me" not in email_section


def test_tc_015_013_metodos_escritores_405_y_subrecurso_404(client) -> None:
    for method in (client.post, client.put, client.delete):
        response = method("/contacto")
        assert response.status_code == 405

    response = client.get("/contacto/horarios")
    assert response.status_code == 404
    html = response.get_data(as_text=True)
    assert "<h1>Página no encontrada</h1>" in html


def test_tc_015_014_regresion_placeholders_navegacion_y_buscador(client) -> None:
    assert expected.PLACEHOLDER_SECTIONS == ["/articulos"]
    for path in expected.PLACEHOLDER_SECTIONS:
        response = client.get(path)
        assert response.status_code == 200, path
        assert "Sección en construcción." in response.get_data(as_text=True)

    assert client.get("/").status_code == 200
    assert client.get("/nosotros").status_code == 200
    assert client.get("/servicios").status_code == 200

    html = _contact_html(client)
    assert 'action="/buscar"' in html

    nav_html = re.search(r"<nav[^>]*>.*?</nav>", html, re.S).group(0)
    hrefs = re.findall(r'<a href="([^"]+)"', nav_html)
    assert len(hrefs) == 6
    for href in hrefs:
        assert client.get(href).status_code == 200, href
