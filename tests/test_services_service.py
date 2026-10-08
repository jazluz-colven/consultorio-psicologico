from consultorio.services import services_service

from tests import expected_content as expected


def test_get_services_view_devuelve_los_dos_servicios_completos() -> None:
    view = services_service.get_services_view()

    assert view.title == expected.SERVICES_PAGE_TITLE
    assert len(view.items) == 2
    assert view.fallback_active is False
    for item in view.items:
        catalog = expected.SERVICES_CATALOG[item.key]
        assert item.name == catalog["name"]
        assert item.description == catalog["description"]
        assert item.benefits == catalog["benefits"]
        assert item.image == catalog["image"]
        assert item.image_alt == catalog["image_alt"]


def test_catalogo_vacio_activa_fallback_con_los_defaults(monkeypatch) -> None:
    monkeypatch.setattr(services_service, "SERVICES_CATALOG", {})

    view = services_service.get_services_view()

    assert view.fallback_active is True
    assert len(view.items) == 2
    for item in view.items:
        catalog = expected.SERVICES_CATALOG[item.key]
        assert item.name == catalog["name"]
        assert item.description == catalog["description"]
        assert item.benefits == catalog["benefits"]
        assert item.image == catalog["image"]
        assert item.image_alt == catalog["image_alt"]


def test_description_o_benefits_vacios_usan_defaults_por_campo(monkeypatch) -> None:
    monkeypatch.setattr(
        services_service,
        "SERVICES_CATALOG",
        {
            "psychology_integral": {
                "name": "Nombre personalizado",
                "description": "",
                "benefits": [],
                "image": "",
                "image_alt": "",
            },
            "nutrition": {
                "name": "Otro nombre",
                "description": "Descripción personalizada.",
                "benefits": ["Beneficio nuevo."],
                "image": "img/servicios/psiconutricion.webp",
                "image_alt": "Alt personalizado.",
            },
        },
    )

    view = services_service.get_services_view()

    assert view.fallback_active is True
    psychology = next(i for i in view.items if i.key == "psychology_integral")
    nutrition = next(i for i in view.items if i.key == "nutrition")
    assert psychology.name == "Nombre personalizado"
    assert psychology.description == expected.SERVICES_CATALOG["psychology_integral"]["description"]
    assert psychology.benefits == expected.SERVICES_CATALOG["psychology_integral"]["benefits"]
    assert psychology.image == expected.SERVICES_CATALOG["psychology_integral"]["image"]
    assert psychology.image_alt == expected.SERVICES_CATALOG["psychology_integral"]["image_alt"]
    assert nutrition.name == "Otro nombre"
    assert nutrition.description == "Descripción personalizada."
    assert nutrition.benefits == ["Beneficio nuevo."]
    assert nutrition.image == "img/servicios/psiconutricion.webp"
    assert nutrition.image_alt == "Alt personalizado."
    for item in view.items:
        assert item.name.strip()
        assert item.description.strip()
        assert item.benefits
        assert item.image.strip()
        assert item.image_alt.strip()
