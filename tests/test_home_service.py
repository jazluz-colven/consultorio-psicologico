import pytest

from consultorio.services import home_service

from tests import expected_content as expected


def test_get_home_view_devuelve_identidad_completa() -> None:
    view = home_service.get_home_view()

    assert view.brand_name == expected.BRAND_NAME
    assert view.tagline == expected.TAGLINE
    assert view.intro == expected.INTRO
    assert view.fallback_active is False


def test_imagen_hero_disponible() -> None:
    view = home_service.get_home_view()

    assert view.hero.available is True
    assert view.hero.src == expected.HERO_SRC
    assert view.hero.alt == expected.HERO_ALT


def test_home_content_vacio_activa_fallback(client, monkeypatch) -> None:
    monkeypatch.setattr(
        home_service,
        "HOME_CONTENT",
        {key: "" for key in expected.HOME_CONTENT},
    )

    view = home_service.get_home_view()

    assert view.fallback_active is True
    assert view.brand_name == expected.BRAND_NAME
    assert view.tagline == expected.TAGLINE
    assert view.intro == expected.INTRO


def test_validate_content_no_devuelve_literales_vacios(monkeypatch) -> None:
    monkeypatch.setattr(
        home_service,
        "HOME_CONTENT",
        {key: "   " for key in expected.HOME_CONTENT},
    )

    content, fallback_active = home_service.validate_content()

    assert fallback_active is True
    for value in (
        content.secondary_brand,
        content.brand_name,
        content.tagline,
        content.intro,
        content.services_title,
        content.services_link_label,
        content.services_link_url,
        content.trust_line,
    ):
        assert value.strip()


def test_imagen_no_disponible_usa_placeholder() -> None:
    hero = home_service.resolve_hero_image(
        {"path": "img/no-existe.png", "alt": expected.HERO_ALT}
    )

    assert hero.available is False
    assert hero.src == expected.PLACEHOLDER_SRC
    assert hero.alt == expected.HERO_ALT


def test_resumen_servicios_incompleto_usa_defaults() -> None:
    services, fallback_active = home_service.validate_services(
        [{"name": "", "summary": "", "url": ""}]
    )

    assert fallback_active is True
    assert len(services) >= 2
    assert [service.name for service in services] == [
        item["name"] for item in expected.SERVICES
    ]


def test_trust_line_vacio_se_completa_con_default(monkeypatch) -> None:
    monkeypatch.setattr(home_service, "TRUST_LINE", "")

    view = home_service.get_home_view()

    assert view.trust_line == expected.TRUST_LINE
    assert view.fallback_active is True


def test_marca_secundaria_vacia_se_completa_con_default(monkeypatch) -> None:
    monkeypatch.setattr(home_service, "SECONDARY_BRAND", "")

    view = home_service.get_home_view()

    assert view.secondary_brand == expected.SECONDARY_BRAND
    assert view.fallback_active is True


def test_navegacion_sin_items_validos_cae_en_inicio() -> None:
    nav = home_service.build_navigation([{"label": "", "url": ""}])

    assert len(nav) == 1
    assert nav[0].label == "Inicio"
    assert nav[0].url == "/"


def test_find_nav_item_identifica_seccion_conocida() -> None:
    item = home_service.find_nav_item("/nosotros")

    assert item is not None
    assert item.label == "Nosotros"
    assert home_service.find_nav_item("/desconocida") is None
