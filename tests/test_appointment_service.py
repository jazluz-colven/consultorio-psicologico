from datetime import date, timedelta
from pathlib import Path

from consultorio.content.appointment_content import (
    BOOKING_HOURS,
    MSG_INVALID_DATE,
    MSG_INVALID_DOC_NUMBER,
    MSG_INVALID_EMAIL,
    MSG_INVALID_NAME,
    MSG_INVALID_PHONE,
    MSG_INVALID_SERVICE,
    MSG_INVALID_TIME,
    MSG_REQUIRED_DATE,
    MSG_REQUIRED_DOC_NUMBER,
    MSG_REQUIRED_DOC_TYPE,
    MSG_REQUIRED_EMAIL,
    MSG_REQUIRED_NAME,
    MSG_REQUIRED_PHONE,
    MSG_REQUIRED_SERVICE,
    MSG_REQUIRED_TIME,
    MSG_SLOT_TAKEN,
)
from consultorio.persistence import appointments_repository as repository
from consultorio.services import appointment_service as service

VALID_DATA = {
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


def _future_weekend() -> str:
    candidate = date.today()
    while candidate.weekday() < 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


def _past_weekday() -> str:
    candidate = date.today() - timedelta(days=1)
    while candidate.weekday() >= 5:
        candidate -= timedelta(days=1)
    return candidate.isoformat()


def _data(**overrides: str) -> dict[str, str]:
    base = {**VALID_DATA, "date": _future_weekday()}
    base.update(overrides)
    return base


def test_validate_booking_datos_validos_sin_errores() -> None:
    assert service.validate_booking(_data()) == {}


def test_validate_booking_cada_campo_vacio_da_su_mensaje_literal() -> None:
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
        errors = service.validate_booking(_data(**{field: ""}))
        assert errors == {field: message}, field


def test_validate_booking_formatos_invalidos_da_mensaje_especifico() -> None:
    cases = [
        ("email", "mal@", MSG_INVALID_EMAIL),
        ("phone", "12ab", MSG_INVALID_PHONE),
        ("phone", "123456", MSG_INVALID_PHONE),
        ("document_number", "12AB", MSG_INVALID_DOC_NUMBER),
        ("document_number", "123", MSG_INVALID_DOC_NUMBER),
        ("patient_name", "An", MSG_INVALID_NAME),
        ("patient_name", "A" * 121, MSG_INVALID_NAME),
        ("date", _past_weekday(), MSG_INVALID_DATE),
        ("date", _future_weekend(), MSG_INVALID_DATE),
        ("date", "no-fecha", MSG_INVALID_DATE),
        ("time", "07:00", MSG_INVALID_TIME),
    ]
    for field, value, message in cases:
        errors = service.validate_booking(_data(**{field: value}))
        assert errors == {field: message}, (field, value)


def test_validate_booking_servicio_fuera_de_catalogo() -> None:
    for bad in ("nope", "psychology", "NUTRITION", " "):
        errors = service.validate_booking(_data(service=bad) if bad != " " else _data(service=""))
        expected = MSG_REQUIRED_SERVICE if bad == " " else MSG_INVALID_SERVICE
        assert errors == {"service": expected}, bad


def test_get_available_hours_catalogo_completo_y_finde_o_pasada_vacio(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    assert service.get_available_hours(
        "nutrition", booking_date, database_path
    ) == BOOKING_HOURS
    assert service.get_available_hours(
        "nutrition", _future_weekend(), database_path
    ) == []
    assert service.get_available_hours(
        "nutrition", _past_weekday(), database_path
    ) == []
    assert service.get_available_hours(
        "nutrition", "no-fecha", database_path
    ) == []


def test_create_booking_hora_desaparece_de_disponibilidad(
    database_path: Path,
) -> None:
    data = _data()
    created = service.create_booking(data, database_path)
    assert created.status == "pending"
    hours = service.get_available_hours(
        data["service"], data["date"], database_path
    )
    assert data["time"] not in hours
    assert hours == BOOKING_HOURS[1:]


def test_create_booking_sobre_horario_ocupado_slot_taken_sin_insert(
    database_path: Path,
) -> None:
    data = _data()
    service.create_booking(data, database_path)
    result = service.create_booking(data, database_path)
    assert result == service.SLOT_TAKEN
    assert MSG_SLOT_TAKEN
    hours = service.get_available_hours(
        data["service"], data["date"], database_path
    )
    assert data["time"] not in hours
    booked = repository.list_booked_times(
        data["service"], data["date"], database_path
    )
    assert booked.count(data["time"]) == 1
