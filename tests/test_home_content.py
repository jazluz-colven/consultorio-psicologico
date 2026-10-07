from consultorio.config import Config
from consultorio.content import hero_image, home_content, nav_links, services_highlights

from tests import expected_content as expected


def test_nav_links_sin_duplicados_ni_vacios() -> None:
    labels = [item["label"] for item in nav_links.NAV_LINKS]
    urls = [item["url"] for item in nav_links.NAV_LINKS]

    assert len(urls) == len(set(urls))
    assert len(labels) == len(set(labels))
    assert all(label.strip() for label in labels)
    assert all(url.strip() for url in urls)
    assert len(nav_links.NAV_LINKS) == 6


def test_imagen_hero_existe_y_no_vacia() -> None:
    asset = Config.STATIC_DIR / hero_image.HERO_IMAGE["path"]

    assert asset.is_file()
    assert asset.stat().st_size > 0


def test_resumen_servicios_minimo_dos_items() -> None:
    items = services_highlights.SERVICES_HIGHLIGHT

    assert len(items) >= 2
    for item in items:
        assert item["name"].strip()
        assert item["summary"].strip()
        assert item["url"].strip()


def test_trust_line_y_marca_secundaria_coinciden_con_los_literales_de_la_spec() -> None:
    assert home_content.SECONDARY_BRAND == expected.SECONDARY_BRAND
    assert home_content.TRUST_LINE == expected.TRUST_LINE


def test_home_content_completo_coincide_con_los_literales_de_la_spec() -> None:
    assert home_content.HOME_CONTENT == expected.HOME_CONTENT
    assert home_content.DEFAULT_HOME_CONTENT == expected.HOME_CONTENT
