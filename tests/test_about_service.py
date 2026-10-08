from consultorio.services import about_service

from tests import expected_content as expected


def test_get_about_view_devuelve_los_cuatro_bloques() -> None:
    view = about_service.get_about_view()

    assert view.mission == expected.ABOUT_CONTENT["mission"]
    assert view.vision == expected.ABOUT_CONTENT["vision"]
    assert view.experience == expected.ABOUT_CONTENT["experience"]
    assert view.values == expected.ABOUT_CONTENT["values"]
    assert view.fallback_active is False


def test_get_about_view_incluye_titulos_de_bloque() -> None:
    view = about_service.get_about_view()

    assert view.titles == expected.ABOUT_BLOCK_TITLES


def test_contenido_vacio_activa_fallback(monkeypatch) -> None:
    monkeypatch.setattr(
        about_service,
        "ABOUT_CONTENT",
        {key: "" for key in expected.ABOUT_CONTENT},
    )

    view = about_service.get_about_view()

    assert view.fallback_active is True
    assert view.mission == expected.ABOUT_CONTENT["mission"]
    assert view.vision == expected.ABOUT_CONTENT["vision"]
    assert view.experience == expected.ABOUT_CONTENT["experience"]
    assert view.values == expected.ABOUT_CONTENT["values"]


def test_validate_about_no_devuelve_bloques_vacios(monkeypatch) -> None:
    monkeypatch.setattr(
        about_service,
        "ABOUT_CONTENT",
        {key: "   " for key in expected.ABOUT_CONTENT},
    )

    content, fallback_active = about_service.validate_about()

    assert fallback_active is True
    for value in (content.mission, content.vision, content.experience, content.values):
        assert value.strip()
