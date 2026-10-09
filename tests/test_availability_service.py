from datetime import date, timedelta
from pathlib import Path

from consultorio.content.appointment_content import BOOKING_HOURS
from consultorio.services import appointment_service as service


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


def _booking_data(service_key: str, booking_date: str, time: str) -> dict[str, str]:
    return {
        "service": service_key,
        "date": booking_date,
        "time": time,
        "document_type": "CC",
        "document_number": "1234567890",
        "patient_name": "Ana Pérez",
        "email": "ana@correo.com",
        "phone": "3001234567",
    }


def _fill_day(database_path: Path, service_key: str, booking_date: str) -> None:
    for hour in BOOKING_HOURS:
        service.create_booking(
            _booking_data(service_key, booking_date, hour), database_path
        )


def test_get_hours_with_status_sin_citas_14_libres_en_orden(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    pairs = service.get_hours_with_status("nutrition", booking_date, database_path)
    assert [hour for hour, _ in pairs] == BOOKING_HOURS
    assert all(is_free for _, is_free in pairs)


def test_get_hours_with_status_hora_reservada_ocupa_y_envoltura_la_excluye(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    service.create_booking(
        _booking_data("nutrition", booking_date, "08:00"), database_path
    )
    pairs = service.get_hours_with_status("nutrition", booking_date, database_path)
    assert dict(pairs)["08:00"] is False
    assert sum(1 for _, is_free in pairs if is_free) == 13
    available = service.get_available_hours("nutrition", booking_date, database_path)
    assert "08:00" not in available
    assert available == BOOKING_HOURS[1:]


def test_get_available_days_sin_citas_laborables_del_mes_ordenados(
    database_path: Path,
) -> None:
    today = date.today()
    year, month = today.year, today.month
    days = service.get_available_days("nutrition", year, month, database_path)
    expected = []
    current = today
    while current.month == month:
        if current.weekday() < 5:
            expected.append(current.isoformat())
        current += timedelta(days=1)
    assert days == expected
    for iso in days:
        parsed = date.fromisoformat(iso)
        assert parsed.weekday() < 5
        assert parsed >= today


def test_get_available_days_tras_reserva_dia_sigue_hasta_llenarse(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    year, month = date.fromisoformat(booking_date).year, date.fromisoformat(booking_date).month
    service.create_booking(
        _booking_data("nutrition", booking_date, "08:00"), database_path
    )
    days = service.get_available_days("nutrition", year, month, database_path)
    assert booking_date in days
    _fill_day(database_path, "nutrition", booking_date)
    days = service.get_available_days("nutrition", year, month, database_path)
    assert booking_date not in days
    pairs = service.get_hours_with_status("nutrition", booking_date, database_path)
    assert all(not is_free for _, is_free in pairs)


def test_get_available_days_dia_lleno_en_servicio_a_sigue_libre_en_b(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    year, month = date.fromisoformat(booking_date).year, date.fromisoformat(booking_date).month
    _fill_day(database_path, "psychology_integral", booking_date)
    days_a = service.get_available_days(
        "psychology_integral", year, month, database_path
    )
    days_b = service.get_available_days("nutrition", year, month, database_path)
    assert booking_date not in days_a
    assert booking_date in days_b


def test_get_available_days_mes_lleno_vacio_y_finde_o_pasada_sin_horas(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    year, month = date.fromisoformat(booking_date).year, date.fromisoformat(booking_date).month
    current = date.fromisoformat(booking_date)
    while current.month == month:
        if current.weekday() < 5:
            _fill_day(database_path, "nutrition", current.isoformat())
        current += timedelta(days=1)
    assert service.get_available_days("nutrition", year, month, database_path) == []
    assert service.get_hours_with_status(
        "nutrition", _future_weekend(), database_path
    ) == []
    assert service.get_hours_with_status(
        "nutrition", _past_weekday(), database_path
    ) == []
    assert service.get_hours_with_status(
        "nutrition", "no-fecha", database_path
    ) == []


def test_get_hours_with_status_ocupada_en_a_libre_en_b(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    service.create_booking(
        _booking_data("psychology_integral", booking_date, "08:00"), database_path
    )
    pairs_a = service.get_hours_with_status(
        "psychology_integral", booking_date, database_path
    )
    pairs_b = service.get_hours_with_status("nutrition", booking_date, database_path)
    assert dict(pairs_a)["08:00"] is False
    assert dict(pairs_b)["08:00"] is True
