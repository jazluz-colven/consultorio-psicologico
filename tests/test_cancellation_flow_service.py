"""HU-017 — ownership verification, the 3-hour window and the execution that
delegates in the Spec 010 service (spec 017 RF-1, RF-2, RF-4, RF-5, RF-8,
RF-9; plan D3/D4/D6/D7 — unit part of TC-017-001, TC-017-003, TC-017-004,
TC-017-005, TC-017-006 and TC-017-011).

Read-only checks: every call receives an explicit `now` so the 3-hour
boundary is deterministic and no test depends on the wall clock. No state
change may happen during verification (RF-1: verification happens before any
change).

Execution (T3): `cancel_verified_request()` must only verify and delegate —
the transition, the slot release and the notifications belong to
`appointment_service.cancel_appointment()` (Spec 010, RF-5).
"""

import re
import sqlite3
from datetime import date, datetime, time, timedelta
from pathlib import Path
from unittest import mock

from consultorio.persistence import appointments_repository as repository
from consultorio.persistence.appointments_repository import Appointment
from consultorio.services import appointment_service as booking
from consultorio.services import automation_service as automation
from consultorio.services import cancellation_flow_service as flow

SERVICE_KEY = "nutrition"
SLOT = "10:00"
DOCUMENT_NUMBER = "1234567890"
OTHER_DOCUMENT = "9999999999"
PATIENT_NAME = "Ana Pérez"
PATIENT_EMAIL = "ana@correo.com"
PATIENT_PHONE = "3001234567"
WEBHOOK_URL = "http://n8n.local/webhook/booking"
TIMEOUT = 3.0
AUTH_HEADER = "X-Auth-Token: prueba"


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


def _cancellation_event_id(appointment_id: int) -> str:
    """Deterministic event_id of the cancellation e-mail (Spec 010)."""
    return f"appointment.cancellation_email:{appointment_id}:v1"


def _count_events(event_id: str, database_path: Path) -> int:
    connection = sqlite3.connect(str(database_path))
    try:
        return connection.execute(
            "SELECT COUNT(*) FROM automation_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()[0]
    finally:
        connection.close()


def _count_all_events(database_path: Path) -> int:
    connection = sqlite3.connect(str(database_path))
    try:
        return connection.execute(
            "SELECT COUNT(*) FROM automation_events"
        ).fetchone()[0]
    finally:
        connection.close()


def _cancellation_posts(post: mock.MagicMock) -> list[mock.call]:
    """POSTs sent to the webhook for `appointment.cancellation_email`
    (same filter as the HU-010 tests)."""
    return [
        call
        for call in post.call_args_list
        if call[0][1].get("event_type") == "appointment.cancellation_email"
    ]


def _execute(
    appointment: Appointment,
    database_path: Path,
    now: datetime,
    document: str = DOCUMENT_NUMBER,
    url: str = WEBHOOK_URL,
) -> tuple[object, mock.MagicMock]:
    """Run cancel_verified_request() with the webhook intercepted."""
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        result = flow.cancel_verified_request(
            appointment.id, document, database_path, now, url, TIMEOUT, AUTH_HEADER
        )
    return result, post



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


# --- T3 — execution delegating in cancel_appointment() (RF-5, RF-8, RF-9) ---


def test_tc_017_004_flujo_feliz_delega_y_queda_cancelada_en_bd(
    database_path: Path,
) -> None:
    """RF-5: verification READY → cancel_verified_request() → the row is
    `cancelled` in the database, and the notification goes out once (RF-8)."""
    appointment = _create(database_path)
    now = _start(appointment) - timedelta(hours=6)

    result, post = _execute(appointment, database_path, now)

    assert isinstance(result, Appointment)
    assert result.id == appointment.id
    assert result.status == "cancelled"
    assert _status(appointment.id, database_path) == "cancelled"
    assert len(_cancellation_posts(post)) == 1
    assert _count_events(_cancellation_event_id(appointment.id), database_path) == 1


def test_tc_017_004_delega_con_la_configuracion_recibida(
    database_path: Path,
) -> None:
    """RF-5: the automation settings received as parameters are forwarded
    verbatim to cancel_appointment() (same pattern as web/appointments.py)."""
    appointment = _create(database_path)
    now = _start(appointment) - timedelta(hours=6)

    with mock.patch.object(automation, "_post_webhook", return_value=200):
        with mock.patch.object(
            flow, "cancel_appointment", wraps=booking.cancel_appointment
        ) as delegate:
            result = flow.cancel_verified_request(
                appointment.id, DOCUMENT_NUMBER, database_path, now,
                WEBHOOK_URL, TIMEOUT, AUTH_HEADER,
            )

    assert isinstance(result, Appointment)
    delegate.assert_called_once_with(
        appointment.id, database_path, WEBHOOK_URL, TIMEOUT, AUTH_HEADER
    )
    assert _status(appointment.id, database_path) == "cancelled"


def test_tc_017_006_segundo_intento_una_sola_fila_y_cero_posts_nuevos(
    database_path: Path,
) -> None:
    """RF-9 / RF-8: a second request over the same appointment answers
    ALREADY_CANCELLED with exactly 1 `appointment.cancellation_email` row and
    0 additional POSTs to the webhook (TC-017-006)."""
    appointment = _create(database_path)
    now = _start(appointment) - timedelta(hours=6)

    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        first = flow.cancel_verified_request(
            appointment.id, DOCUMENT_NUMBER, database_path, now,
            WEBHOOK_URL, TIMEOUT, AUTH_HEADER,
        )
        assert isinstance(first, Appointment)
        posts_after_first = post.call_count

        second = flow.cancel_verified_request(
            appointment.id, DOCUMENT_NUMBER, database_path, now,
            WEBHOOK_URL, TIMEOUT, AUTH_HEADER,
        )

    assert second == flow.ALREADY_CANCELLED == booking.ALREADY_CANCELLED
    assert isinstance(second, str)
    # 0 POSTs added by the retry (the first attempt already sent them)
    assert post.call_count == posts_after_first
    assert len(_cancellation_posts(post)) == 1
    assert _count_events(_cancellation_event_id(appointment.id), database_path) == 1
    assert _status(appointment.id, database_path) == "cancelled"


def test_tc_017_004_documento_incorrecto_no_cancela_ni_notifica(
    database_path: Path,
) -> None:
    """RF-1 / RF-8: a failed verification returns FAILED without writing a
    single row and without any POST."""
    appointment = _create(database_path)
    now = _start(appointment) - timedelta(hours=6)
    events_before = _count_all_events(database_path)

    result, post = _execute(
        appointment, database_path, now, document=OTHER_DOCUMENT
    )

    assert result == flow.FAILED
    assert _status(appointment.id, database_path) == "confirmed"
    assert post.call_count == 0
    assert _count_all_events(database_path) == events_before
    assert _count_events(_cancellation_event_id(appointment.id), database_path) == 0


def test_tc_017_003_ventana_insuficiente_no_cancela_ni_notifica(
    database_path: Path,
) -> None:
    """RF-4 / RF-8: inside the 3-hour window the execution returns TOO_SOON
    without writing a single row and without any POST."""
    appointment = _create(database_path)
    now = _start(appointment) - timedelta(hours=2, minutes=59)
    events_before = _count_all_events(database_path)

    result, post = _execute(appointment, database_path, now)

    assert result == flow.TOO_SOON
    assert _status(appointment.id, database_path) == "confirmed"
    assert post.call_count == 0
    assert _count_all_events(database_path) == events_before
    assert _count_events(_cancellation_event_id(appointment.id), database_path) == 0


def test_tc_017_004_cita_inexistente_en_la_delegacion_mapea_a_failed(
    database_path: Path,
) -> None:
    """Plan D7 mapping: APPOINTMENT_NOT_FOUND coming from the delegated call
    is reported as FAILED (the module never invents another sentinel)."""
    appointment = _create(database_path)
    now = _start(appointment) - timedelta(hours=6)

    with mock.patch.object(
        flow, "cancel_appointment", return_value=booking.APPOINTMENT_NOT_FOUND
    ) as delegate:
        result = flow.cancel_verified_request(
            appointment.id, DOCUMENT_NUMBER, database_path, now,
            WEBHOOK_URL, TIMEOUT, AUTH_HEADER,
        )

    assert result == flow.FAILED
    delegate.assert_called_once()
    # verification itself never changed anything (RF-1)
    assert _status(appointment.id, database_path) == "confirmed"


def test_tc_017_011_cancellation_flow_service_delega_sin_logica_propia() -> None:
    """TC-017-011 / constitution #3: source inspection — the module only
    imports and calls cancel_appointment(); it contains no SQL statement, no
    state transition and no notification of its own."""
    source = Path(flow.__file__).read_text(encoding="utf-8")

    # delegation is present
    assert "def cancel_verified_request" in source
    assert re.search(
        r"from consultorio\.services\.appointment_service import", source
    )
    assert re.search(r"[^.\w]cancel_appointment\(", source)

    # no SQL statement of its own
    for statement in (r"\bUPDATE\b", r"\bINSERT\b", r"\bDELETE\b", r"\bSELECT\b"):
        assert re.search(statement, source) is None, statement

    # no transition / registration / notification logic of its own
    for own_logic in (
        "_post_webhook",
        "send_cancellation",
        "publish_cancelled_event",
        "on_appointment_cancelled",
        "update_appointment_status",
        "insert_event",
        "mark_sent",
        "mark_failed",
        "mark_skipped",
        "events_repository",
        "urllib",
        "requests",
    ):
        assert own_logic not in source, own_logic
