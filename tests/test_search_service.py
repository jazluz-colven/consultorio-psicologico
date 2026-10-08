from consultorio.services.search_service import (
    STATUS_EMPTY,
    STATUS_OK,
    build_index,
    search,
)


def test_tc_016_001_busqueda_con_resultados_devuelve_titulo_extracto_y_enlace() -> None:
    hits, status = search("psicología")

    assert status == STATUS_OK
    assert len(hits) >= 1
    for item in hits:
        assert item.title
        assert item.snippet
        assert item.url.startswith("/")
    assert any(item.url == "/servicios" for item in hits)


def test_tc_016_002_indice_cubre_portada_nosotros_servicios_y_navegacion() -> None:
    entries = build_index()

    urls = {entry.url for entry in entries}
    assert {"/", "/nosotros", "/servicios"} <= urls

    titles = {entry.title for entry in entries}
    for label in (
        "Inicio",
        "Nosotros",
        "Servicios",
        "Blog",
        "Contacto",
        "Agendar cita",
    ):
        assert label in titles


def test_tc_016_003_termino_sin_coincidencias_devuelve_lista_vacia() -> None:
    hits, status = search("zzzzz")

    assert status == STATUS_OK
    assert hits == []


def test_tc_016_004_consulta_vacia_o_solo_espacios_devuelve_estado_vacio() -> None:
    for query in ("", "   "):
        hits, status = search(query)

        assert status == STATUS_EMPTY, query
        assert hits == [], query


def test_tc_016_011_consulta_larga_o_con_caracteres_especiales_no_lanza_excepcion() -> None:
    queries = [
        "ñ" * 500,
        "@#$%^&*()[]{}<>?",
        "   psicología   ",
        "a" * 1000 + " \t\n ",
    ]

    for query in queries:
        hits, status = search(query)

        assert status in {STATUS_OK, STATUS_EMPTY}, query
        assert isinstance(hits, list), query
