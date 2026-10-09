from datetime import date, timedelta

from consultorio.content.appointment_content import (
    BOOKING_HOURS,
    MSG_INVALID_PARAMS,
)
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


def _month_key(booking_date: str) -> str:
    return booking_date[:7]


def test_horarios_json_claves_available_y_occupied(client, app) -> None:
    booking_date = _future_weekday()
    with app.app_context():
        from consultorio.services.appointment_service import create_booking

        create_booking(_form(), app.config["DATABASE_PATH"])
    response = client.get(
        f"/citas/horarios?service=nutrition&date={booking_date}"
    )
    assert response.status_code == 200
    payload = response.get_json()
    assert set(payload) == {"available", "occupied"}
    assert payload["occupied"] == ["08:00"]
    assert payload["available"] == BOOKING_HOURS[1:]
    weekend = date.today()
    while weekend.weekday() < 5:
        weekend += timedelta(days=1)
    empty = client.get(
        f"/citas/horarios?service=nutrition&date={weekend.isoformat()}"
    )
    assert empty.get_json() == {"available": [], "occupied": []}


def test_e2e_reserva_y_reconsulta_hora_solo_en_occupied(app, client) -> None:
    data = _form()
    booking_date = data["date"]
    assert client.post("/citas", data=data).status_code == 303
    response = client.get(
        f"/citas/horarios?service=nutrition&date={booking_date}"
    )
    payload = response.get_json()
    assert "08:00" not in payload["available"]
    assert "08:00" in payload["occupied"]
    other = (
        date.fromisoformat(booking_date) + timedelta(days=7)
    )
    while other.weekday() >= 5:
        other += timedelta(days=1)
    elsewhere = client.get(
        f"/citas/horarios?service=nutrition&date={other.isoformat()}"
    )
    assert "08:00" in elsewhere.get_json()["available"]


def test_disponibilidad_dias_laborables_y_mes_siguiente(client) -> None:
    today = date.today()
    response = client.get(
        f"/citas/disponibilidad?service=nutrition&month={today:%Y-%m}"
    )
    assert response.status_code == 200
    days = response.get_json()["days"]
    assert days == sorted(days)
    for iso in days:
        parsed = date.fromisoformat(iso)
        assert parsed.weekday() < 5
        assert parsed >= today
    next_month = (today.replace(day=1) + timedelta(days=32)).replace(day=1)
    follow = client.get(
        f"/citas/disponibilidad?service=nutrition&month={next_month:%Y-%m}"
    )
    assert follow.status_code == 200
    assert len(follow.get_json()["days"]) > 0


def test_disponibilidad_dia_lleno_ausente_en_a_presente_en_b(
    app, client,
) -> None:
    booking_date = _future_weekday()
    with app.app_context():
        from consultorio.content.appointment_content import BOOKING_HOURS as hours
        from consultorio.services.appointment_service import create_booking

        for hour in hours:
            create_booking(
                _form(service="psychology_integral", date=booking_date, time=hour),
                app.config["DATABASE_PATH"],
            )
    month = _month_key(booking_date)
    days_a = client.get(
        f"/citas/disponibilidad?service=psychology_integral&month={month}"
    ).get_json()["days"]
    days_b = client.get(
        f"/citas/disponibilidad?service=nutrition&month={month}"
    ).get_json()["days"]
    assert booking_date not in days_a
    assert booking_date in days_b


def test_disponibilidad_parametros_invalidos_400_y_405(client) -> None:
    cases = [
        "/citas/disponibilidad?service=fantasma&month=2026-10",
        "/citas/disponibilidad?service=nutrition&month=2026-13",
        "/citas/disponibilidad?service=nutrition&month=banana",
        "/citas/disponibilidad?service=nutrition&month=2026-00",
        "/citas/disponibilidad",
        "/citas/disponibilidad?month=2026-10",
    ]
    for url in cases:
        response = client.get(url)
        assert response.status_code == 400, url
        assert response.get_json() == {"error": MSG_INVALID_PARAMS}, url
    assert client.post("/citas/disponibilidad").status_code == 405


def test_e2e_reconsulta_citas_y_horarios_tras_reserva(app, client) -> None:
    import re

    data = _form()
    booking_date = data["date"]
    assert client.post("/citas", data=data, follow_redirects=False).status_code == 303
    redisplay = client.post(
        "/citas", data=_form(patient_name="")
    )
    assert redisplay.status_code == 200
    html = redisplay.get_data(as_text=True)
    assert expected.MSG_OCCUPIED_HOUR in html
    assert re.search(
        r"appointment__hour--taken[^>]*>.*?08:00", html, re.S
    ), "08:00 must render as an occupied (taken) hour"
    assert html.count('name="time"') == len(expected.BOOKING_HOURS) - 1
    for later in range(1, 8):
        candidate = date.fromisoformat(booking_date) + timedelta(days=later)
        if candidate.weekday() >= 5:
            continue
        payload = client.get(
            f"/citas/horarios?service=nutrition&date={candidate.isoformat()}"
        ).get_json()
        assert "08:00" in payload["available"], candidate.isoformat()
    same = client.get(
        f"/citas/horarios?service=nutrition&date={booking_date}"
    ).get_json()
    assert "08:00" not in same["available"]
