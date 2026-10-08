from consultorio.content import services_catalog, services_highlights

from tests import expected_content as expected

APPROVED_KEYS = {"psychology_integral", "nutrition"}


def test_servicios_catalog_tiene_las_claves_aprobadas_sin_campos_vacios() -> None:
    assert set(services_catalog.SERVICES_CATALOG) == APPROVED_KEYS
    for key, service in services_catalog.SERVICES_CATALOG.items():
        assert str(service["name"]).strip(), key
        assert str(service["description"]).strip(), key
        benefits = service["benefits"]
        assert isinstance(benefits, list) and benefits, key
        for benefit in benefits:
            assert str(benefit).strip(), key
        assert len(benefits) == len(set(benefits)), key


def test_defaults_y_titulo_son_los_literales_de_la_spec() -> None:
    assert services_catalog.DEFAULT_SERVICES_CATALOG == expected.SERVICES_CATALOG
    assert services_catalog.SERVICES_PAGE_TITLE == expected.SERVICES_PAGE_TITLE
    assert services_catalog.SERVICES_PAGE_TITLE == "Servicios"


def test_catalogo_contiene_los_dos_servicios_minimos_coherentes_con_la_portada() -> None:
    names = {service["name"] for service in services_catalog.SERVICES_CATALOG.values()}
    assert names == {"Psicología Integral", "Psiconutrición"}
    highlight_names = {item["name"] for item in services_highlights.SERVICES_HIGHLIGHT}
    assert names == highlight_names


def test_cada_servicio_tiene_description_y_benefits_no_vacios() -> None:
    for key, service in services_catalog.SERVICES_CATALOG.items():
        assert str(service["description"]).strip(), key
        benefits = service["benefits"]
        assert isinstance(benefits, list) and len(benefits) >= 1, key
        assert all(str(benefit).strip() for benefit in benefits), key
