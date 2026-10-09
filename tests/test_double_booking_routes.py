"""HU-006 — double-booking protection over HTTP (spec 006)."""

import re
import threading
from concurrent.futures import ThreadPoolExecutor
from datetime import date, timedelta

from consultorio.content.appointment_content import (
    MSG_OCCUPIED_HOUR,
    MSG_SLOT_TAKEN,
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


def _selectable_radio(html: str, hour: str) -> bool:
    return f'name="time" value="{hour}"' in html


def test_tc_006_006_post_sobre_ocupado_da_conflicto_claro(app, client) -> None:
    data = _form()
    assert client.post("/citas", data=data).status_code == 303

    response = client.post("/citas", data=data)
    html = _main_html(response.get_data(as_text=True))

    assert response.status_code == 200
    assert MSG_SLOT_TAKEN in html
    assert MSG_OCCUPIED_HOUR in html
    assert not _selectable_radio(html, data["time"])
    assert _count_appointments(app) == 1


def test_tc_006_007_ocho_post_concurrentes_una_sola_cita(app) -> None:
    workers = 8
    barrier = threading.Barrier(workers)
    payload = _form()
    codes: list[int] = []
    conflict_bodies: list[str] = []
    lock = threading.Lock()

    def submit() -> None:
        client = app.test_client()
        barrier.wait(timeout=10)
        response = client.post("/citas", data=payload)
        with lock:
            codes.append(response.status_code)
            if response.status_code == 200:
                conflict_bodies.append(response.get_data(as_text=True))

    with ThreadPoolExecutor(max_workers=workers) as pool:
        for future in [pool.submit(submit) for _ in range(workers)]:
            future.result(timeout=60)

    assert len(codes) == workers
    assert codes.count(303) == 1
    assert codes.count(200) == workers - 1
    assert all(MSG_SLOT_TAKEN in body for body in conflict_bodies)
    assert _count_appointments(app) == 1


def test_tc_006_008_hora_ocupada_en_a_libre_en_servicio_b(app, client) -> None:
    data_a = _form(service="nutrition")
    assert client.post("/citas", data=data_a).status_code == 303

    data_b = _form(service="psychology_integral")
    response = client.post("/citas", data=data_b)

    assert response.status_code == 303
    assert _count_appointments(app) == 2


def test_tc_006_009_get_citas_expone_el_literal_en_curso(client) -> None:
    html = client.get("/citas").get_data(as_text=True)
    assert f'data-submitting="{expected.MSG_SUBMITTING}"' in html
    assert 'class="appointment__submit"' in html
    assert expected.MSG_SUBMITTING == "Registrando tu cita…"


def test_tc_006_010_regresion_disponibilidad_tras_reserva_y_errores(
    app, client
) -> None:
    booking_date = _future_weekday()
    for index, hour in enumerate(
        ["08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00",
         "11:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30"]
    ):
        payload = _form(time=hour, document_number=f"12345678{index:02d}")
        assert client.post("/citas", data=payload).status_code == 303

    hours = client.get(
        f"/citas/horarios?service=nutrition&date={booking_date}"
    ).get_json()
    assert hours["occupied"] == [
        "08:00", "08:30", "09:00", "09:30", "10:00", "10:30", "11:00",
        "11:30", "14:00", "14:30", "15:00", "15:30", "16:00", "16:30",
    ]
    assert hours["available"] == []

    month = booking_date[:7]
    days = client.get(
        f"/citas/disponibilidad?service=nutrition&month={month}"
    ).get_json()["days"]
    assert booking_date not in days

    assert client.get("/citas/horarios?service=bogus").status_code == 400
    assert client.post("/citas/horarios").status_code == 405
    assert _count_appointments(app) == 14
