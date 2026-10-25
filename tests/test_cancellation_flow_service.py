"""HU-017 — ownership verification and the 3-hour cancellation window
(spec 017 RF-1, RF-2, RF-4; plan D3/D4/D6 — unit part of TC-017-001 and
TC-017-003, plus the ALREADY_CANCELLED ordering of RF-9).

Read-only checks: every call receives an explicit `now` so the 3-hour
boundary is deterministic and no test depends on the wall clock. No state
change may happen here (RF-1: verification happens before any change).
"""

from datetime import date, datetime, time, timedelta
from pathlib import Path

from consultorio.persistence import appointments_repository as repository
from consultorio.persistence.appointments_repository import Appointment
from consultorio.services import appointment_service as booking
from consultorio.services import cancellation_flow_service as flow

SERVICE_KEY = "nutrition"
SLOT = "10:00"
DOCUMENT_NUMBER = "1234567890"
OTHER_DOCUMENT = "9999999999"
PATIENT_NAME = "Ana Pérez"
PATIENT_EMAIL = "ana@correo.com"
PATIENT_PHONE = "3001234567"


def _future_weekday() -> str:
    candidate = date.today()
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


def _booking_data(booking_date: str, slot: str = SLOT) -> dict[str, str]:
    return {
        "service": SERVICE_KEY,
        "date": booking_date,
        "time": slot,
        "document_type": "CC",
        "document_number": DOCUMENT_NUMBER,
        "patient_name": PATIENT_NAME,
        "email": PATIENT_EMAIL,
        "phone": PATIENT_PHONE,
    }


def _create(database_path: Path) -> Appointment:
    created = booking.create_booking(_booking_data(_future_weekday()), database_path)
    assert isinstance(created, Appointment)
    return created


def _start(appointment: Appointment) -> datetime:
    """Appointment start exactly as the service computes it (plan D6)."""
    return datetime.combine(
        date.fromisoformat(appointment.date),
        time.fromisoformat(appointment.time),
    )


def _verify(appointment: Appointment, database_path: Path, now: datetime,
            document: str = DOCUMENT_NUMBER) -> Appointment | str:
    return flow.verify_cancellation_request(
        appointment.id, document, database_path, now
    )


def _status(appointment_id: int, database_path: Path) -> str:
    current = repository.get_appointment_by_id(appointment_id, database_path)
    assert current is not None
    return current.status


def _assert_failed_without_appointment_data(
    result: object, appointment: Appointment, database_path: Path
) -> None:
    """D4: the FAILED output must not leak any appointment data."""
    assert result == flow.FAILED
    leaked = str(result)
    for forbidden in (
        PATIENT_NAME,
        PATIENT_EMAIL,
        PATIENT_PHONE,
        DOCUMENT_NUMBER,
        SERVICE_KEY,
        appointment.date,
        appointment.time,
    ):
        assert forbidden not in leaked
    # RF-1: verification never changes the row
    assert _status(appointment.id, database_path) == "confirmed"


# --- RF-4 / TC-017-003: 3-hour window -------------------------------------


def test_tc_017_003_borde_exacto_tres_horas_listo(database_path: Path) -> None:
    appointment = _create(database_path)
    result = _verify(appointment, database_path, _start(appointment) - timedelta(hours=3))
    assert isinstance(result, Appointment)
    assert result.id == appointment.id
    assert result.status == "confirmed"
    assert _status(appointment.id, database_path) == "confirmed"


def test_tc_017_003_dos_horas_59_minutos_rechazada(database_path: Path) -> None:
    appointment = _create(database_path)
    now = _start(appointment) - timedelta(hours=2, minutes=59)
    result = _verify(appointment, database_path, now)
    assert result == flow.TOO_SOON
    assert _status(appointment.id, database_path) == "confirmed"


def test_tc_017_003_hora_iniciada_rechazada(database_path: Path) -> None:
    appointment = _create(database_path)
    result = _verify(appointment, database_path, _start(appointment))
    assert result == flow.TOO_SOON


def test_tc_017_003_hora_pasada_rechazada(database_path: Path) -> None:
    appointment = _create(database_path)
    result = _verify(appointment, database_path, _start(appointment) + timedelta(hours=2))
    assert result == flow.TOO_SOON


# --- RF-1 / RF-2 / TC-017-001: ownership ----------------------------------


def test_tc_017_001_referencia_inexistente_fallida(database_path: Path) -> None:
    appointment = _create(database_path)
    missing_id = appointment.id + 999
    result = flow.verify_cancellation_request(
        missing_id, DOCUMENT_NUMBER, database_path, _start(appointment)
    )
    assert result == flow.FAILED


def test_tc_017_001_documento_incorrecto_fallida_sin_datos(
    database_path: Path,
) -> None:
    appointment = _create(database_path)
    result = _verify(
        appointment, database_path, _start(appointment) - timedelta(hours=6),
        document=OTHER_DOCUMENT,
    )
    _assert_failed_without_appointment_data(result, appointment, database_path)


def test_tc_017_001_inexistente_e_incorrecto_indistinguibles(
    database_path: Path,
) -> None:
    """D4: one single result for «unknown reference» and «wrong document»."""
    appointment = _create(database_path)
    now = _start(appointment) - timedelta(hours=6)
    unknown = flow.verify_cancellation_request(
        appointment.id + 999, OTHER_DOCUMENT, database_path, now
    )
    mismatch = _verify(appointment, database_path, now, document=OTHER_DOCUMENT)
    assert unknown == mismatch == flow.FAILED


def test_tc_017_001_documento_con_espacios_se_compara_tras_strip(
    database_path: Path,
) -> None:
    """D3: the document number is compared exactly, after strip()."""
    appointment = _create(database_path)
    result = _verify(
        appointment, database_path, _start(appointment) - timedelta(hours=6),
        document=f"  {DOCUMENT_NUMBER}\t",
    )
    assert isinstance(result, Appointment)


# --- RF-9: already cancelled wins over the window -------------------------


def test_tc_017_006_cita_ya_cancelada_antes_de_la_ventana(
    database_path: Path,
) -> None:
    """The cancelled state is evaluated before the 3-hour window (§5 order):
    an already cancelled appointment never reports TOO_SOON."""
    appointment = _create(database_path)
    cancelled = booking.cancel_appointment(appointment.id, database_path)
    assert isinstance(cancelled, Appointment)

    past = _verify(appointment, database_path, _start(appointment) + timedelta(hours=1))
    assert past == flow.ALREADY_CANCELLED

    soon = _verify(
        appointment, database_path, _start(appointment) - timedelta(hours=1)
    )
    assert soon == flow.ALREADY_CANCELLED

    # and a wrong document still hides that state (D4)
    mismatch = _verify(
        appointment, database_path, _start(appointment) - timedelta(hours=6),
        document=OTHER_DOCUMENT,
    )
    assert mismatch == flow.FAILED
