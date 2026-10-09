import re
from datetime import date, timedelta

from consultorio.content.appointment_content import (
    BOOKING_HOURS,
    CONFIRMATION_TITLE,
    MSG_INVALID_DATE,
    MSG_INVALID_DOC_NUMBER,
    MSG_INVALID_EMAIL,
    MSG_INVALID_PARAMS,
    MSG_INVALID_SERVICE,
    MSG_REQUIRED_DATE,
    MSG_REQUIRED_DOC_NUMBER,
    MSG_REQUIRED_DOC_TYPE,
    MSG_REQUIRED_EMAIL,
    MSG_REQUIRED_NAME,
    MSG_REQUIRED_PHONE,
    MSG_REQUIRED_SERVICE,
    MSG_REQUIRED_TIME,
    MSG_SLOT_TAKEN,
    STATUS_PENDING_LABEL,
)
from consultorio.persistence import appointments_repository as repository
from tests import expected_content as expected

VALID_FORM = {
    "service": "nutrition",
    "date": "",
    "time": "08:00",
    "document_type": "CC",
    "document_number": "1234567890",
    "patient_name": "Ana Pérez",
    "email": "ana@correo.com",
    "phone": "3001234567",
}


def _future_weekday() -> str:
    candidate = date.today()
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


def _form(**overrides: str) -> dict[str, str]:
    base = {**VALID_FORM, "date": _future_weekday()}
    base.update(overrides)
    return base


def _main_html(html: str) -> str:
    match = re.search(r"<main[^>]*>(.*?)</main>", html, re.S)
    return match.group(1) if match else html


def _count_appointments(app) -> int:
    with app.app_context():
        path = app.config["DATABASE_PATH"]
    with repository.get_connection(path) as connection:
        return connection.execute(
            "SELECT COUNT(*) AS total FROM appointments"
        ).fetchone()["total"]


def test_get_citas_muestra_formulario_completo(client) -> None:
    response = client.get("/citas")
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert expected.BOOKING_PAGE_TITLE in html
    main = _main_html(html)
    for name in (
        "service",
        "date",
        "time",
        "document_type",
        "document_number",
        "patient_name",
        "email",
        "phone",
    ):
        assert f'name="{name}"' in main, name
    for hour in expected.BOOKING_HOURS:
        assert f'value="{hour}"' in main, hour
    assert "Volver al inicio" in main
    assert 'href="/"' in main
    nav_hrefs = re.findall(r'<a href="(/[^"]*)">', html)
    assert len(set(nav_hrefs)) >= 6


def test_post_valido_redirige_a_confirmacion_y_crea_1_fila(app, client) -> None:
    data = _form()
    response = client.post("/citas", data=data, follow_redirects=False)
    assert response.status_code == 303
    location = response.headers["Location"]
    assert "/citas/confirmada/" in location
    confirmation = client.get(location)
    assert confirmation.status_code == 200
    html = confirmation.get_data(as_text=True)
    assert expected.CONFIRMATION_TITLE in html
    assert expected.STATUS_PENDING_LABEL in html
    assert "08:00" in html
    assert data["date"] in html
    assert "Psiconutrición" in html
    assert data["patient_name"] in html
    assert _count_appointments(app) == 1


def test_post_sin_cada_obligatorio_da_mensaje_y_0_filas(app, client) -> None:
    cases = {
        "service": MSG_REQUIRED_SERVICE,
        "date": MSG_REQUIRED_DATE,
        "time": MSG_REQUIRED_TIME,
        "document_type": MSG_REQUIRED_DOC_TYPE,
        "document_number": MSG_REQUIRED_DOC_NUMBER,
        "patient_name": MSG_REQUIRED_NAME,
        "email": MSG_REQUIRED_EMAIL,
        "phone": MSG_REQUIRED_PHONE,
    }
    for field, message in cases.items():
        response = client.post("/citas", data=_form(**{field: ""}))
        assert response.status_code == 200, field
        html = response.get_data(as_text=True)
        assert message in html, field
        assert _count_appointments(app) == 0, field


def test_post_dato_invalido_conserva_valores_y_0_filas(app, client) -> None:
    cases = [
        ("email", "mal@", MSG_INVALID_EMAIL),
        ("document_number", "12AB", MSG_INVALID_DOC_NUMBER),
        ("date", "2020-01-01", MSG_INVALID_DATE),
    ]
    for field, value, message in cases:
        response = client.post("/citas", data=_form(**{field: value}))
        assert response.status_code == 200, field
        html = response.get_data(as_text=True)
        assert message in html, field
        preserved = value if field != "date" else _form()[field]
        if field != "date":
            assert f'value="{value}"' in html, field
        assert _count_appointments(app) == 0, field


def test_post_horario_ocupado_da_slot_taken_y_exactamente_1_fila(
    app, client,
) -> None:
    data = _form()
    assert client.post("/citas", data=data).status_code == 303
    response = client.post("/citas", data=data)
    assert response.status_code == 200
    html = response.get_data(as_text=True)
    assert expected.MSG_SLOT_TAKEN in html
    assert _count_appointments(app) == 1


def test_post_servicio_invalido_y_horarios_con_servicio_invalido_400(
    app, client,
) -> None:
    response = client.post("/citas", data=_form(service="fantasma"))
    assert response.status_code == 200
    assert MSG_INVALID_SERVICE in response.get_data(as_text=True)
    assert _count_appointments(app) == 0
    bad = client.get("/citas/horarios?service=fantasma&date=2026-10-12")
    assert bad.status_code == 400
    assert bad.get_json() == {"error": MSG_INVALID_PARAMS}


def test_horarios_json_disponibilidad_y_405(client) -> None:
    booking_date = _future_weekday()
    response = client.get(
        f"/citas/horarios?service=nutrition&date={booking_date}"
    )
    assert response.status_code == 200
    assert response.get_json() == {"available": BOOKING_HOURS, "occupied": []}
    weekend = date.today()
    while weekend.weekday() < 5:
        weekend += timedelta(days=1)
    empty = client.get(
        f"/citas/horarios?service=nutrition&date={weekend.isoformat()}"
    )
    assert empty.status_code == 200
    assert empty.get_json() == {"available": [], "occupied": []}
    missing = client.get("/citas/horarios")
    assert missing.status_code == 400
    assert missing.get_json() == {"error": MSG_INVALID_PARAMS}
    assert client.post("/citas/horarios").status_code == 405


def test_confirmacion_inexistente_404_y_put_citas_405(client) -> None:
    missing = client.get("/citas/confirmada/999999")
    assert missing.status_code == 404
    assert "Página no encontrada" in missing.get_data(as_text=True)
    assert client.put("/citas").status_code == 405


def test_regresion_placeholders_navegacion_y_secciones_intactas(client) -> None:
    assert "/citas" not in expected.PLACEHOLDER_SECTIONS
    for section in expected.PLACEHOLDER_SECTIONS:
        response = client.get(section)
        assert response.status_code == 200, section
        assert "Sección en construcción." in response.get_data(as_text=True)
    home = client.get("/")
    assert home.status_code == 200
    html = home.get_data(as_text=True)
    for item in expected.NAV_LINKS:
        assert f'href="{item["url"]}"' in html, item["url"]
    for url in ("/nosotros", "/servicios", "/buscar?q=psicolog"):
        assert client.get(url).status_code == 200, url
    citas = client.get("/citas")
    assert citas.status_code == 200
    assert "Volver al inicio" in citas.get_data(as_text=True)
