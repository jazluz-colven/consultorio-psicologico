from consultorio.content import about_content

from tests import expected_content as expected


def test_about_content_coincide_con_el_espejo_de_la_spec() -> None:
    assert set(about_content.ABOUT_CONTENT) == set(expected.ABOUT_CONTENT)
    assert about_content.ABOUT_CONTENT == expected.ABOUT_CONTENT
    for value in about_content.ABOUT_CONTENT.values():
        assert value.strip()


def test_defaults_y_titulos_son_los_literales_de_la_spec() -> None:
    assert about_content.DEFAULT_ABOUT_CONTENT == expected.ABOUT_CONTENT
    assert about_content.BLOCK_TITLES == expected.ABOUT_BLOCK_TITLES
    assert about_content.DEFAULT_BLOCK_TITLES == expected.ABOUT_BLOCK_TITLES


def test_literales_no_contienen_servicios_ni_llamadas_a_agendar() -> None:
    forbidden = (
        "Psicología Integral",
        "Psiconutrición",
        "Ver todos los servicios",
        "Agendar cita",
    )
    for key, text in about_content.ABOUT_CONTENT.items():
        for phrase in forbidden:
            assert phrase not in text, (key, phrase)
