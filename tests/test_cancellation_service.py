"""HU-010 — cancellation e-mail event and slot release at the service layer
(spec 010 amended 2026-10-13)."""

import re
import sqlite3
import urllib.error
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from consultorio.content.automation_content import (
    DETAIL_INVALID_RESPONSE_PREFIX,
    DETAIL_INVALID_RESPONSE_TEMPLATE,
    DETAIL_PERMANENT_REJECTION_PATTERN,
    DETAIL_RETRYABLE_REJECTION_PATTERN,
    DETAIL_TIMEOUT,
    DETAIL_UNEXPECTED,
)
from consultorio.persistence import appointments_repository as repository
from consultorio.persistence.appointments_repository import Appointment
from consultorio.persistence.automation_events_repository import claim_failed_event
from consultorio.services import appointment_service as booking
from consultorio.services import automation_service as automation
from consultorio.services import email_service as email

SERVICE_KEY = "nutrition"
SLOT = "08:00"
WEBHOOK_URL = "http://n8n.local/webhook/booking"
TIMEOUT = 3.0

PALETTE = {
    "#789B8A",
    "#B8D8CE",
    "#F7F3EA",
    "#D99A7A",
    "#E8D5B5",
    "#30454B",
}


def _future_weekday() -> str:
    candidate = date.today()
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


def _booking_data(booking_date: str, time: str = SLOT) -> dict[str, str]:
    return {
        "service": SERVICE_KEY,
        "date": booking_date,
        "time": time,
        "document_type": "CC",
        "document_number": "1234567890",
        "patient_name": "Ana Pérez",
        "email": "ana@correo.com",
        "phone": "3001234567",
    }


def _event_id(appointment_id: int) -> str:
    return f"appointment.cancellation_email:{appointment_id}:v1"


def _cancellation_posts(post: mock.MagicMock) -> list[mock.call]:
    return [
        call
        for call in post.call_args_list
        if call[0][1].get("event_type") == "appointment.cancellation_email"
    ]


def _count_events(event_id: str, database_path: Path) -> int:
    connection = sqlite3.connect(str(database_path))
    try:
        return connection.execute(
            "SELECT COUNT(*) FROM automation_events WHERE event_id = ?",
            (event_id,),
        ).fetchone()[0]
    finally:
        connection.close()


def test_tc_010_001_cancelar_2xx_sent_un_post_y_payload_completo(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    posts = _cancellation_posts(post)
    assert len(posts) == 1
    url, payload, timeout, auth_header = posts[0][0]
    assert url == WEBHOOK_URL
    assert timeout == TIMEOUT
    assert auth_header == ""
    assert payload["event_id"] == _event_id(created.id)
    assert payload["recipient"]["to"] == "ana@correo.com"
    assert payload["recipient"]["patient_name"] == "Ana Pérez"
    assert set(payload["message"].keys()) == {"subject", "text", "html"}
    assert payload["message"]["subject"].startswith("Cita cancelada")
    assert payload["appointment"]["id"] == created.id
    assert payload["appointment"]["status"] == "cancelled"
    event = email.events_repository.get_by_event_id(
        _event_id(created.id), database_path
    )
    assert event is not None
    assert event.status == "sent"
    assert event.detail is None
    assert event.sent_at is not None


def test_tc_010_002_mensaje_completo_legible_y_paleta(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    cancelled = Appointment(
        id=created.id,
        document_type=created.document_type,
        document_number=created.document_number,
        patient_name=created.patient_name,
        email=created.email,
        phone=created.phone,
        service=created.service,
        date=created.date,
        time=created.time,
        status="cancelled",
        created_at=created.created_at,
    )
    message = email.build_cancellation_message(cancelled)

    expected_date_label = email.format_spanish_date(booking_date)
    assert message["subject"].startswith("Cita cancelada —")
    assert "Psiconutrición" in message["subject"]
    assert expected_date_label in message["subject"]
    for part in (message["text"], message["html"]):
        assert "Psiconutrición" in part
        assert booking_date not in part
        assert expected_date_label in part
        assert SLOT in part
        assert "Cancelada" in part
        assert f"#{created.id}" in part
        assert "Tu cita ha sido cancelada" in part
    hexes = set(re.findall(r"#[0-9A-Fa-f]{6}", message["html"]))
    assert hexes and hexes.issubset(PALETTE)
    assert "<img" not in message["html"].lower()
    assert "<link" not in message["html"].lower()
    assert "@import" not in message["html"]
    assert "http://" not in message["html"]
    assert "https://" not in message["html"]
    for forbidden in ("1234567890", "3001234567"):
        assert forbidden not in message["text"]
        assert forbidden not in message["html"]


def test_tc_010_003_url_vacia_skipped_sin_post(database_path: Path) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        result = booking.cancel_appointment(created.id, database_path)
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    assert len(_cancellation_posts(post)) == 0
    event = email.events_repository.get_by_event_id(
        _event_id(created.id), database_path
    )
    assert event is not None
    assert event.status == "skipped"
    assert event.detail == "Envío de correo no configurado."


def test_tc_010_004_urlerror_failed_cancellation_intacta(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(
        automation,
        "_post_webhook",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    event = email.events_repository.get_by_event_id(
        _event_id(created.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Servicio de automatización no disponible."


def test_tc_010_005_timeout_failed_cancellation_intacta(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", side_effect=TimeoutError):
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    event = email.events_repository.get_by_event_id(
        _event_id(created.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Tiempo de espera agotado (timeout)."


def test_tc_010_006_reproceso_already_cancelled_un_evento_un_post(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        first = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
        second = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(first, Appointment)
    assert second == booking.ALREADY_CANCELLED
    assert len(_cancellation_posts(post)) == 1
    assert _count_events(_event_id(created.id), database_path) == 1


def test_tc_010_007_email_invalido_failed_sin_post(database_path: Path) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    connection = sqlite3.connect(str(database_path))
    try:
        connection.execute(
            "UPDATE appointments SET email = '' WHERE id = ?", (created.id,)
        )
        connection.commit()
    finally:
        connection.close()
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    assert len(_cancellation_posts(post)) == 0
    event = email.events_repository.get_by_event_id(
        _event_id(created.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == (
        "Dirección de correo del paciente ausente o no válida."
    )


def test_tc_010_008_datos_incompletos_failed_sin_post(
    database_path: Path,
) -> None:
    incomplete = Appointment(
        id=1,
        document_type="CC",
        document_number="1234567890",
        patient_name="Ana Pérez",
        email="ana@correo.com",
        phone="3001234567",
        service="",
        date="",
        time="",
        status="cancelled",
        created_at="2026-10-10 10:00:00",
    )
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        email.send_cancellation(
            incomplete, str(database_path), WEBHOOK_URL, TIMEOUT
        )
    assert len(_cancellation_posts(post)) == 0
    event = email.events_repository.get_by_event_id(
        _event_id(incomplete.id), database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Datos de la cita incompletos."


def test_tc_010_009_aislamiento_repositorio_caido_cancelacion_ok(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(
        email.events_repository,
        "insert_event",
        side_effect=RuntimeError("db down"),
    ):
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"


def test_tc_010_010_payload_allowlist_event_id_determinista(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    cancelled = Appointment(
        id=created.id,
        document_type=created.document_type,
        document_number=created.document_number,
        patient_name=created.patient_name,
        email=created.email,
        phone=created.phone,
        service=created.service,
        date=created.date,
        time=created.time,
        status="cancelled",
        created_at=created.created_at,
    )
    event = email.build_cancellation_event(cancelled)
    assert set(event.keys()) == {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "recipient",
        "message",
        "appointment",
    }
    assert event["event_id"] == _event_id(created.id)
    assert event["event_type"] == "appointment.cancellation_email"
    assert event["event_version"] == 1
    assert set(event["recipient"].keys()) == {"to", "patient_name"}
    assert set(event["message"].keys()) == {"subject", "text", "html"}
    assert event["appointment"]["status"] == "cancelled"
    forbidden = {
        "document_type",
        "document_number",
        "phone",
        "created_at",
    }
    assert forbidden.isdisjoint(event.keys())
    assert forbidden.isdisjoint(event["appointment"].keys())


def test_tc_010_011_cancelar_libera_el_horario(database_path: Path) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    assert repository.is_slot_taken(SERVICE_KEY, booking_date, SLOT, database_path)
    result = booking.cancel_appointment(created.id, database_path)
    assert isinstance(result, Appointment)
    assert not repository.is_slot_taken(
        SERVICE_KEY, booking_date, SLOT, database_path
    )
    hours = dict(
        booking.get_hours_with_status(SERVICE_KEY, booking_date, database_path)
    )
    assert hours[SLOT] is True


def test_tc_010_012_slot_confirmado_sigue_dando_slot_taken(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    booking.create_booking(_booking_data(booking_date), database_path)
    result = booking.create_booking(_booking_data(booking_date), database_path)
    assert result == booking.SLOT_TAKEN
    connection = sqlite3.connect(str(database_path))
    try:
        count = connection.execute(
            "SELECT COUNT(*) FROM appointments"
        ).fetchone()[0]
    finally:
        connection.close()
    assert count == 1


import pytest

def test_tc_010_110_atomicidad_rollback_ante_fallo_registro(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    
    # Simular fallo crítico durante la inserción del evento dentro de la transacción.
    # En lugar de parchear sqlite3.Connection (que es inmutable), 
    # parcheamos el método del repositorio que realiza la operación.
    
    original_update_status = repository.update_appointment_status_with_pending_event

    def mocked_update_status(*args, **kwargs):
        # Simulamos que la transacción falla justo al insertar el evento
        # lanzando la excepción desde el punto de entrada del repositorio.
        raise RuntimeError("Simulated DB Critical Failure during event insertion")

    with mock.patch("consultorio.persistence.appointments_repository.update_appointment_status_with_pending_event", 
                    side_effect=mocked_update_status):
        with mock.patch.object(automation, "_post_webhook") as post:
            # El error debe propagarse ya que es un fallo crítico de persistencia (RF-12)
            with pytest.raises(RuntimeError, match="Simulated DB Critical Failure"):
                booking.cancel_appointment(
                    created.id, database_path, WEBHOOK_URL, TIMEOUT
                )
            
            # Verificación: la cita NO debe quedar en estado 'cancelled'
            # Debe permanecer 'confirmed' porque el error ocurrió antes del commit
            current = repository.get_appointment_by_id(created.id, database_path)
            assert current.status == "confirmed"
            
            # Verificación: no se crea ninguna fila en automation_events
            event_id = f"appointment.cancelled:{created.id}:v1"
            assert _count_events(event_id, database_path) == 0
            
            # Verificación: no se emite ningún POST al webhook
            assert post.call_count == 0

def test_tc_010_112_estado_post_commit_fallo_publicacion(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    
    # Simular fallo en la publicación (_post_webhook) pero con registro exitoso previo.
    with mock.patch.object(
        automation, 
        "_post_webhook", 
        side_effect=RuntimeError("Network crash after commit")
    ) as post:
        # La función cancel_appointment captura excepciones de publish_cancelled_event
        # y send_cancellation (RF-10), por lo que no debe lanzar excepción al usuario.
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
        
    # Resultado esperado: la cita SÍ queda en estado Cancelada (RF-10)
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    
    # Verificación: el evento queda registrado en la BD con estado 'failed'
    # ya que el commit de la transacción ocurrió antes del POST.
    event_id = f"appointment.cancelled:{created.id}:v1"
    event = automation.events_repository.get_by_event_id(event_id, database_path)
    assert event is not None
    assert event.status == "failed"
    assert "Error inesperado" in event.detail


def _cancelled_posts(post: mock.MagicMock) -> list[mock.call]:
    return [
        call
        for call in post.call_args_list
        if call[0][1].get("event_type") == "appointment.cancelled"
    ]


def test_tc_010_102_payload_negocio_allowlist_sin_pii() -> None:
    appointment = Appointment(
        id=34,
        document_type="CC",
        document_number="1234567890",
        patient_name="Ana Pérez",
        email="ana@correo.com",
        phone="3001234567",
        service=SERVICE_KEY,
        date="2026-10-15",
        time=SLOT,
        status="cancelled",
        created_at="2026-10-10 10:00:00",
    )
    event = automation.build_cancelled_event(appointment)
    assert set(event.keys()) == {
        "event_id",
        "event_type",
        "event_version",
        "occurred_at",
        "appointment",
    }
    assert event["event_id"] == "appointment.cancelled:34:v1"
    assert event["event_type"] == "appointment.cancelled"
    assert event["event_version"] == 1
    assert re.fullmatch(
        r"\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}", str(event["occurred_at"])
    )
    assert set(event["appointment"].keys()) == {
        "id",
        "service",
        "date",
        "time",
        "status",
    }
    assert event["appointment"] == {
        "id": 34,
        "service": SERVICE_KEY,
        "date": "2026-10-15",
        "time": SLOT,
        "status": "cancelled",
    }
    forbidden = {
        "patient_name",
        "email",
        "phone",
        "document_type",
        "document_number",
        "recipient",
        "message",
    }
    assert forbidden.isdisjoint(event.keys())
    assert forbidden.isdisjoint(event["appointment"].keys())


def test_tc_010_104_url_vacia_negocio_skipped_sin_post(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        cancelled = booking.cancel_appointment(created.id, database_path)
    assert isinstance(cancelled, Appointment)
    assert cancelled.status == "cancelled"
    event = automation.events_repository.get_by_event_id(
        f"appointment.cancelled:{created.id}:v1", database_path
    )
    assert event is not None
    assert event.status == "skipped"
    assert event.detail == "Automatización no configurada."
    assert len(_cancelled_posts(post)) == 0
    assert post.call_count == 0


def test_tc_010_101_cancelar_emite_evento_negocio_y_correo(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    business_posts = _cancelled_posts(post)
    assert len(business_posts) == 1
    url, payload, timeout, auth_header = business_posts[0][0]
    assert url == WEBHOOK_URL
    assert timeout == TIMEOUT
    assert auth_header == ""
    assert payload["event_id"] == f"appointment.cancelled:{created.id}:v1"
    assert payload["event_type"] == "appointment.cancelled"
    assert payload["event_version"] == 1
    assert payload["appointment"]["id"] == created.id
    assert payload["appointment"]["status"] == "cancelled"
    event = automation.events_repository.get_by_event_id(
        f"appointment.cancelled:{created.id}:v1", database_path
    )
    assert event is not None
    assert event.status == "sent"
    assert event.detail is None
    assert event.sent_at is not None
    assert len(_cancellation_posts(post)) == 1


def test_tc_010_103_evento_negocio_independiente_del_correo(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    connection = sqlite3.connect(str(database_path))
    try:
        connection.execute(
            "UPDATE appointments SET email = '' WHERE id = ?", (created.id,)
        )
        connection.commit()
    finally:
        connection.close()
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    assert len(_cancelled_posts(post)) == 1
    business_event = automation.events_repository.get_by_event_id(
        f"appointment.cancelled:{created.id}:v1", database_path
    )
    assert business_event is not None
    assert business_event.status == "sent"
    assert business_event.sent_at is not None
    assert len(_cancellation_posts(post)) == 0
    email_event = email.events_repository.get_by_event_id(
        _event_id(created.id), database_path
    )
    assert email_event is not None
    assert email_event.status == "failed"


def test_tc_010_108_reproceso_already_cancelled_un_evento_negocio(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        first = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
        second = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(first, Appointment)
    assert second == booking.ALREADY_CANCELLED
    assert len(_cancelled_posts(post)) == 1
    assert _count_events(
        f"appointment.cancelled:{created.id}:v1", database_path
    ) == 1



def test_tc_010_105_urlerror_failed_motivo_disponible(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(
        automation,
        "_post_webhook",
        side_effect=urllib.error.URLError("connection refused"),
    ):
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    event = automation.events_repository.get_by_event_id(
        f"appointment.cancelled:{created.id}:v1", database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Servicio de automatización no disponible."


def test_tc_010_106_timeout_failed_motivo_timeout(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", side_effect=TimeoutError):
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    event = automation.events_repository.get_by_event_id(
        f"appointment.cancelled:{created.id}:v1", database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Tiempo de espera agotado (timeout)."


def test_tc_010_107_http500_failed_motivo_respuesta_invalida(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    with mock.patch.object(automation, "_post_webhook", return_value=500):
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    event = automation.events_repository.get_by_event_id(
        f"appointment.cancelled:{created.id}:v1", database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == "Respuesta no válida del servicio (HTTP 500)."


def test_tc_010_111_firma_build_event_intacta() -> None:
    # Verificar que build_event sigue el contrato y no ha cambiado su firma
    appointment = Appointment(
        id=99,
        document_type="CC",
        document_number="123",
        patient_name="Test",
        email="test@test.com",
        phone="123",
        service="test",
        date="2026-10-10",
        time="10:00",
        status="confirmed",
        created_at="2026-10-01 10:00:00",
    )
    event = automation.build_event(appointment)
    assert event["event_type"] == "appointment.confirmed"
    assert event["event_version"] == 1
    assert "event_id" in event
    assert "appointment" in event


def test_tc_010_113_reproceso_exito_sent_un_post(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    event_id = f"appointment.cancelled:{created.id}:v1"
    
    # 1. Crear evento fallido
    with mock.patch.object(automation, "_post_webhook", side_effect=TimeoutError):
        booking.cancel_appointment(created.id, database_path, WEBHOOK_URL, TIMEOUT)
    
    # 2. Reprocesar con éxito
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        automation.reprocess_automation_event(event_id, database_path, WEBHOOK_URL, TIMEOUT)
    
    assert len(_cancelled_posts(post)) == 1
    event = automation.events_repository.get_by_event_id(event_id, database_path)
    assert event.status == "sent"


def test_tc_010_114_reproceso_url_vacia_skipped(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    event_id = f"appointment.cancelled:{created.id}:v1"
    
    with mock.patch.object(automation, "_post_webhook", side_effect=TimeoutError):
        booking.cancel_appointment(created.id, database_path, WEBHOOK_URL, TIMEOUT)
    
    # Reprocesar con URL vacía
    automation.reprocess_automation_event(event_id, database_path, url="", timeout=TIMEOUT)
    
    event = automation.events_repository.get_by_event_id(event_id, database_path)
    assert event.status == "skipped"
    assert event.detail == "Automatización no configurada."


def test_tc_010_115_reproceso_re_fallo_motivo_actualizado(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    event_id = f"appointment.cancelled:{created.id}:v1"
    
    # 1. Primer fallo (Timeout)
    with mock.patch.object(automation, "_post_webhook", side_effect=TimeoutError):
        booking.cancel_appointment(created.id, database_path, WEBHOOK_URL, TIMEOUT)
    
    # 2. Reprocesar y fallar con HTTP 500
    with mock.patch.object(automation, "_post_webhook", return_value=500):
        automation.reprocess_automation_event(event_id, database_path, WEBHOOK_URL, TIMEOUT)
    
    event = automation.events_repository.get_by_event_id(event_id, database_path)
    assert event.status == "failed"
    assert event.detail == "Respuesta no válida del servicio (HTTP 500)."


def test_tc_010_116_reproceso_no_op_estados_no_failed(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    event_id = f"appointment.cancelled:{created.id}:v1"
    
    # Caso 1: Evento ya 'sent'
    with mock.patch.object(automation, "_post_webhook", return_value=200):
        booking.cancel_appointment(created.id, database_path, WEBHOOK_URL, TIMEOUT)
    
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        automation.reprocess_automation_event(event_id, database_path, WEBHOOK_URL, TIMEOUT)
        assert len(_cancelled_posts(post)) == 0
        
    # Caso 2: Evento 'skipped'
    created2 = booking.create_booking(_booking_data(booking_date), database_path)
    event_id2 = f"appointment.cancelled:{created2.id}:v1"
    booking.cancel_appointment(created2.id, database_path, "", TIMEOUT)
    
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        automation.reprocess_automation_event(event_id2, database_path, WEBHOOK_URL, TIMEOUT)
        assert len(_cancelled_posts(post)) == 0


def test_tc_010_118_reproceso_solo_appointment_cancelled(
    database_path: Path,
) -> None:
    connection = sqlite3.connect(str(database_path))
    event_id = "appointment.confirmed:999:v1"
    connection.execute(
        "INSERT INTO automation_events (event_id, event_type, event_version, appointment_id, status, detail) VALUES (?, ?, ?, ?, ?, ?)",
        (event_id, "appointment.confirmed", 1, 999, "failed", "Error inicial")
    )
    connection.commit()
    connection.close()
    
    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        automation.reprocess_automation_event(event_id, database_path, WEBHOOK_URL, TIMEOUT)
        assert len(_cancelled_posts(post)) == 0


def test_tc_010_117_exclusion_concurrencia_reproceso(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    event_id = f"appointment.cancelled:{created.id}:v1"
    
    # 1. Crear evento en estado 'failed'
    with mock.patch.object(automation, "_post_webhook", side_effect=TimeoutError):
        booking.cancel_appointment(created.id, database_path, WEBHOOK_URL, TIMEOUT)
    
    # 2. Simular concurrencia determinista:
    # El side_effect del primer POST invoca una segunda llamada al reproceso.
    # El segundo intento debe fallar al intentar reclamar el evento (claim_failed_event -> False).
    
    call_count = 0
    def concurrent_side_effect(*args, **kwargs):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            # Mientras procesamos el primer POST, llega una segunda solicitud de reproceso
            automation.reprocess_automation_event(event_id, database_path, WEBHOOK_URL, TIMEOUT)
        return 200

    with mock.patch.object(automation, "_post_webhook", side_effect=concurrent_side_effect) as post:
        automation.reprocess_automation_event(event_id, database_path, WEBHOOK_URL, TIMEOUT)
    
    # Verificación:
    # - Solo debe haber UN POST emitido (el del primer reproceso).
    # - El segundo reproceso debe haber sido un no-op porque el primero ya cambió el estado a 'pending'.
    assert len(_cancelled_posts(post)) == 1
    
    # Verificación final de estado: el evento debe haber terminado en 'sent'
    event = automation.events_repository.get_by_event_id(event_id, database_path)
    assert event.status == "sent"


def test_tc_010_119_estabilidad_bateria_operaciones(
    database_path: Path,
) -> None:
    # Secuencia exhaustiva de operaciones sobre múltiples citas
    booking_date = _future_weekday()
    citas = []
    for i in range(5):
        data = _booking_data(booking_date)
        data["patient_name"] = f"Paciente {i}"
        data["email"] = f"p{i}@correo.com"
        citas.append(booking.create_booking(data, database_path))

    with mock.patch.object(automation, "_post_webhook", return_value=200) as post:
        # Mezcla de: cancelaciones exitosas, fallos, reprocesos y cancelaciones repetidas
        for i, cita in enumerate(citas):
            if isinstance(cita, str):
                continue
            if i == 0: # Exitosa
                booking.cancel_appointment(cita.id, database_path, WEBHOOK_URL, TIMEOUT)
            elif i == 1: # Fallo -> Reproceso exitoso
                post.side_effect = TimeoutError
                booking.cancel_appointment(cita.id, database_path, WEBHOOK_URL, TIMEOUT)
                post.side_effect = None
                post.return_value = 200
                event_id = f"appointment.cancelled:{cita.id}:v1"
                automation.reprocess_automation_event(event_id, database_path, WEBHOOK_URL, TIMEOUT)
            elif i == 2: # URL vacía -> Reproceso exitoso
                booking.cancel_appointment(cita.id, database_path, "", TIMEOUT)
                event_id = f"appointment.cancelled:{cita.id}:v1"
                automation.reprocess_automation_event(event_id, database_path, WEBHOOK_URL, TIMEOUT)
            elif i == 3: # Fallo -> Reproceso que vuelve a fallar
                post.side_effect = TimeoutError
                booking.cancel_appointment(cita.id, database_path, WEBHOOK_URL, TIMEOUT)
                automation.reprocess_automation_event(f"appointment.cancelled:{cita.id}:v1", database_path, WEBHOOK_URL, TIMEOUT)
                post.side_effect = None
            elif i == 4: # Cancelación repetida
                booking.cancel_appointment(cita.id, database_path, WEBHOOK_URL, TIMEOUT)
                booking.cancel_appointment(cita.id, database_path, WEBHOOK_URL, TIMEOUT)

    # Verificación de consistencia final
    for i, cita in enumerate(citas):
        # Si la cita fue creada exitosamente, es un objeto Appointment. 
        # Si falló (SLOT_TAKEN), es un str.
        if isinstance(cita, str):
            continue
            
        event_id = f"appointment.cancelled:{cita.id}:v1"
        event = automation.events_repository.get_by_event_id(event_id, database_path)
        assert event is not None
        if i == 0: assert event.status == "sent"
        if i == 1: assert event.status == "sent"
        if i == 2: assert event.status == "sent"
        if i == 3: assert event.status == "failed"
        if i == 4: assert event.status == "sent"


# --- D-010-01 / T1: clasificación de un HTTPError real en la publicación inicial ---
# El montaje usa `side_effect=HTTPError(...)`, no `return_value=500`: reproduce el
# comportamiento real de `urllib.request.urlopen` ante una respuesta 4xx/5xx
# (`HTTPError` es subclase de `URLError`, causa raíz del defecto).


def test_tc_d010_01_http400_publicacion_inicial_detalle_respuesta_invalida(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    http_error = urllib.error.HTTPError(
        WEBHOOK_URL, 400, "Bad Request", hdrs=None, fp=None
    )
    with mock.patch.object(automation, "_post_webhook", side_effect=http_error):
        # No se envuelve en pytest.raises: si la excepción se propagara, el test
        # fallaría por error; la cancelación debe devolverse normalmente (RF-10).
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    stored = repository.get_appointment_by_id(created.id, database_path)
    assert stored is not None
    assert stored.status == "cancelled"
    event = automation.events_repository.get_by_event_id(
        f"appointment.cancelled:{created.id}:v1", database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code=400)


def test_tc_d010_02_http500_publicacion_inicial_detalle_respuesta_invalida(
    database_path: Path,
) -> None:
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    http_error = urllib.error.HTTPError(
        WEBHOOK_URL, 500, "Internal Server Error", hdrs=None, fp=None
    )
    with mock.patch.object(automation, "_post_webhook", side_effect=http_error):
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    stored = repository.get_appointment_by_id(created.id, database_path)
    assert stored is not None
    assert stored.status == "cancelled"
    event = automation.events_repository.get_by_event_id(
        f"appointment.cancelled:{created.id}:v1", database_path
    )
    assert event is not None
    assert event.status == "failed"
    assert event.detail == DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code=500)


# --- D-010-01 / T5: admisión del reproceso (DP-05) ---------------------------
# Un `failed` con `detail` de rechazo HTTP PERMANENTE (4xx salvo 429) no debe
# readmitirse; un 429 o un 5xx (transitorios) sí. El montaje provoca el `failed`
# real con `side_effect=HTTPError(...)` en la publicación inicial, de modo que el
# `detail` persistido procede del mismo clasificador que se usa en producción.


def _cancel_with_http_error(
    status_code: int, database_path: Path
) -> tuple[Appointment, str, int]:
    """Cancel an appointment and leave its business event `failed` with `HTTP nnn`.

    Returns `(appointment, event_id, row_id)`; the row id lets the reproceso tests
    prove that the SAME row is reused (no second row, no id change).
    """
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    assert isinstance(created, Appointment)
    http_error = urllib.error.HTTPError(
        WEBHOOK_URL, status_code, f"HTTP {status_code}", hdrs=None, fp=None
    )
    with mock.patch.object(automation, "_post_webhook", side_effect=http_error):
        result = booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )
    # RF-10: the publication failure never reverts nor blocks the cancellation.
    assert isinstance(result, Appointment)
    assert result.status == "cancelled"
    event_id = f"appointment.cancelled:{created.id}:v1"
    event = automation.events_repository.get_by_event_id(event_id, database_path)
    assert event is not None
    assert event.status == "failed"
    assert event.detail == DETAIL_INVALID_RESPONSE_TEMPLATE.format(
        status_code=status_code
    )
    return created, event_id, event.id


def test_tc_d010_06_reproceso_http400_permanente_no_se_readmite(
    database_path: Path,
) -> None:
    """CA-D010-04/12: a 400 must not be claimed: 0 POST and an untouched row."""
    _, event_id, row_id = _cancel_with_http_error(400, database_path)
    detail = DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code=400)

    post = mock.Mock()
    with mock.patch.object(automation, "_post_webhook", post):
        automation.reprocess_automation_event(
            event_id, database_path, WEBHOOK_URL, TIMEOUT
        )

    stored = automation.events_repository.get_by_event_id(event_id, database_path)
    assert stored is not None
    assert (post.call_count, stored.status, stored.detail) == (0, "failed", detail), (
        "un rechazo HTTP 4xx permanente no debe readmitirse: "
        f"POST={post.call_count}, status={stored.status!r}, detail={stored.detail!r}"
    )
    assert stored.id == row_id
    assert _count_events(event_id, database_path) == 1


def test_tc_d010_07_reproceso_http422_permanente_no_se_readmite(
    database_path: Path,
) -> None:
    """CA-D010-04/12: a 422 must not be claimed: 0 POST and an untouched row."""
    _, event_id, row_id = _cancel_with_http_error(422, database_path)
    detail = DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code=422)

    post = mock.Mock()
    with mock.patch.object(automation, "_post_webhook", post):
        automation.reprocess_automation_event(
            event_id, database_path, WEBHOOK_URL, TIMEOUT
        )

    stored = automation.events_repository.get_by_event_id(event_id, database_path)
    assert stored is not None
    assert (post.call_count, stored.status, stored.detail) == (0, "failed", detail), (
        "un rechazo HTTP 4xx permanente no debe readmitirse: "
        f"POST={post.call_count}, status={stored.status!r}, detail={stored.detail!r}"
    )
    assert stored.id == row_id
    assert _count_events(event_id, database_path) == 1


def test_tc_d010_08_reproceso_http429_transitorio_se_readmite(
    database_path: Path,
) -> None:
    """CA-D010-12 (DP-05): a 429 is transient: exactly one POST, same row, `sent`."""
    _, event_id, row_id = _cancel_with_http_error(429, database_path)

    post = mock.Mock(return_value=200)
    with mock.patch.object(automation, "_post_webhook", post):
        automation.reprocess_automation_event(
            event_id, database_path, WEBHOOK_URL, TIMEOUT
        )

    assert post.call_count == 1
    stored = automation.events_repository.get_by_event_id(event_id, database_path)
    assert stored is not None
    assert stored.id == row_id
    assert stored.status == "sent"
    assert stored.detail is None
    assert _count_events(event_id, database_path) == 1


def test_tc_d010_09_reproceso_http500_transitorio_se_readmite(
    database_path: Path,
) -> None:
    """CA-D010-12 (DP-05): a 5xx is transient: exactly one POST, same row, `sent`."""
    _, event_id, row_id = _cancel_with_http_error(500, database_path)

    post = mock.Mock(return_value=200)
    with mock.patch.object(automation, "_post_webhook", post):
        automation.reprocess_automation_event(
            event_id, database_path, WEBHOOK_URL, TIMEOUT
        )

    assert post.call_count == 1
    stored = automation.events_repository.get_by_event_id(event_id, database_path)
    assert stored is not None
    assert stored.id == row_id
    assert stored.status == "sent"
    assert stored.detail is None
    assert _count_events(event_id, database_path) == 1


# --- D-010-01 / DP-02: vinculación template ↔ patrón de reintentabilidad ------
# La política de no reintentabilidad se decide por el prefijo del `detail`
# persistido. Si el copy de `DETAIL_INVALID_RESPONSE_TEMPLATE` cambia sin
# actualizar los patrones, la clasificación se rompería en silencio. Esta prueba
# ata ambas representaciones a la MISMA constante derivada.


def test_tc_d010_dp02_patrones_derivados_del_template() -> None:
    """DP-02 (punto 7): el patrón de rechazo permanente y la excepción 429 se
    derivan del literal vigente, y el prefijo coincide con el del template."""
    assert DETAIL_PERMANENT_REJECTION_PATTERN == (
        DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code="4__")
    )
    assert DETAIL_RETRYABLE_REJECTION_PATTERN == (
        DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code="429")
    )
    assert DETAIL_INVALID_RESPONSE_PREFIX == (
        DETAIL_INVALID_RESPONSE_TEMPLATE.split("{status_code}")[0]
    )
    # Ambos patrones deben compartir el prefijo del literal: si el copy cambia,
    # el patrón deja de coincidir con los `detail` persistidos y esta prueba falla.
    assert DETAIL_PERMANENT_REJECTION_PATTERN.startswith(
        DETAIL_INVALID_RESPONSE_PREFIX
    )
    assert DETAIL_RETRYABLE_REJECTION_PATTERN.startswith(
        DETAIL_INVALID_RESPONSE_PREFIX
    )


# --- D-010-01 / T7: concurrencia, permanencia y no-op ------------------------
# T3–T6 fijan el comportamiento; estas pruebas lo blindan frente a re-entrancia
# (dos solicitudes sobre el mismo evento) y frente a estados/tipos no reprocesables.
# No se cambia código: si fallan, el hallazgo es que la corrección no lo cubre.


def test_tc_d010_11_concurrencia_y_permanencia(database_path: Path) -> None:
    """CA-D010-04/07 (RF-14, RF-15): un 4xx permanente nunca se readmite; un
    timeout se admite exactamente una vez, incluso con una segunda solicitud
    re-entrante (mismo patrón determinista de TC-010-117)."""
    # (a) 400 permanente: dos reprocesos seguidos siguen siendo no-op.
    booking_date = _future_weekday()
    _, event_id, row_id = _cancel_with_http_error(400, database_path)
    detail_400 = DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code=400)

    post_400 = mock.Mock()
    with mock.patch.object(automation, "_post_webhook", post_400):
        automation.reprocess_automation_event(
            event_id, database_path, WEBHOOK_URL, TIMEOUT
        )
        assert post_400.call_count == 0
        automation.reprocess_automation_event(
            event_id, database_path, WEBHOOK_URL, TIMEOUT
        )
        assert post_400.call_count == 0

    stored = automation.events_repository.get_by_event_id(event_id, database_path)
    assert stored is not None
    assert (stored.id, stored.status, stored.detail) == (
        row_id,
        "failed",
        detail_400,
    ), (
        "un rechazo HTTP 4xx permanente no debe admitirse nunca: "
        f"id={stored.id}, status={stored.status!r}, detail={stored.detail!r}"
    )
    assert _count_events(event_id, database_path) == 1

    # (b) timeout: se admite una sola vez. La segunda solicitud se lanza dentro
    # del primer POST (re-entrancia determinista) y una tercera inmediatamente
    # después; ninguna de las dos debe volver a publicar.
    created = booking.create_booking(
        _booking_data(booking_date, "09:00"), database_path
    )
    assert isinstance(created, Appointment)
    timeout_event_id = f"appointment.cancelled:{created.id}:v1"
    with mock.patch.object(automation, "_post_webhook", side_effect=TimeoutError):
        booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )

    failed = automation.events_repository.get_by_event_id(
        timeout_event_id, database_path
    )
    assert failed is not None
    assert (failed.status, failed.detail) == ("failed", DETAIL_TIMEOUT)

    concurrent_calls = 0

    def concurrent_side_effect(*args, **kwargs):
        nonlocal concurrent_calls
        concurrent_calls += 1
        if concurrent_calls == 1:
            # Mientras el primer intento publica, llega otra solicitud de reproceso.
            automation.reprocess_automation_event(
                timeout_event_id, database_path, WEBHOOK_URL, TIMEOUT
            )
        return 200

    post = mock.Mock(side_effect=concurrent_side_effect)
    with mock.patch.object(automation, "_post_webhook", post):
        automation.reprocess_automation_event(
            timeout_event_id, database_path, WEBHOOK_URL, TIMEOUT
        )
        assert len(_cancelled_posts(post)) == 1
        calls_after_first = post.call_count
        # Re-entrada secuencial inmediata: ya está `sent`, debe ser no-op.
        automation.reprocess_automation_event(
            timeout_event_id, database_path, WEBHOOK_URL, TIMEOUT
        )
        assert post.call_count == calls_after_first

    assert len(_cancelled_posts(post)) == 1
    stored = automation.events_repository.get_by_event_id(
        timeout_event_id, database_path
    )
    assert stored is not None
    assert (stored.id, stored.status, stored.detail) == (failed.id, "sent", None)
    assert _count_events(timeout_event_id, database_path) == 1


def _prepare_non_reprocessable_event(
    scenario: str, database_path: Path
) -> str:
    """Create one event whose reproceso must be a no-op, and return its id."""
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    assert isinstance(created, Appointment)
    event_id = f"appointment.cancelled:{created.id}:v1"

    if scenario == "sent":
        with mock.patch.object(automation, "_post_webhook", return_value=200):
            booking.cancel_appointment(
                created.id, database_path, WEBHOOK_URL, TIMEOUT
            )
    elif scenario == "skipped":
        booking.cancel_appointment(created.id, database_path, "", TIMEOUT)
    elif scenario == "pending":
        inserted = automation.events_repository.insert_event(
            event_id, "appointment.cancelled", 1, created.id, database_path
        )
        assert inserted is True
    elif scenario == "other_type_failed":
        # `create_booking()` already registered this appointment's e-mail event
        # as `skipped`; reuse that row so the only difference is type + `failed`.
        event_id = f"appointment.confirmation_email:{created.id}:v1"
        connection = sqlite3.connect(str(database_path))
        try:
            cursor = connection.execute(
                """
                UPDATE automation_events SET status = 'failed', detail = ?
                WHERE event_id = ?
                """,
                (DETAIL_TIMEOUT, event_id),
            )
            assert cursor.rowcount == 1
            connection.commit()
        finally:
            connection.close()
    else:  # pragma: no cover - guard against a typo in the parametrization
        raise AssertionError(f"escenario no soportado: {scenario!r}")
    return event_id


@pytest.mark.parametrize(
    "scenario",
    ["sent", "skipped", "pending", "other_type_failed"],
)
def test_tc_d010_15_no_op_por_estado_y_tipo_de_evento(
    scenario: str, database_path: Path
) -> None:
    """CA-D010 (RF-14): `sent`, `skipped`, `pending` y un `failed` de otro tipo
    son no-op: 0 POST, registro sin modificar y una sola fila."""
    event_id = _prepare_non_reprocessable_event(scenario, database_path)
    before = automation.events_repository.get_by_event_id(event_id, database_path)
    assert before is not None

    post = mock.Mock()
    with mock.patch.object(automation, "_post_webhook", post):
        automation.reprocess_automation_event(
            event_id, database_path, WEBHOOK_URL, TIMEOUT
        )

    assert post.call_count == 0, (
        f"escenario {scenario!r}: un evento no reprocesable no debe publicar"
    )
    stored = automation.events_repository.get_by_event_id(event_id, database_path)
    assert stored is not None
    assert stored == before, (
        f"escenario {scenario!r}: el registro no debe modificarse: "
        f"antes={before}, después={stored}"
    )
    assert _count_events(event_id, database_path) == 1


def test_tc_d010_17_reproceso_readmite_detail_unexpected(
    database_path: Path,
) -> None:
    """DP-05: una excepción inesperada (`DETAIL_UNEXPECTED`) sigue siendo
    readmitida: el reproceso con éxito deja la MISMA fila en `sent` sin `detail`."""
    booking_date = _future_weekday()
    created = booking.create_booking(_booking_data(booking_date), database_path)
    assert isinstance(created, Appointment)
    event_id = f"appointment.cancelled:{created.id}:v1"

    with mock.patch.object(
        automation, "_post_webhook", side_effect=RuntimeError("boom")
    ):
        booking.cancel_appointment(
            created.id, database_path, WEBHOOK_URL, TIMEOUT
        )

    failed = automation.events_repository.get_by_event_id(event_id, database_path)
    assert failed is not None
    assert (failed.status, failed.detail) == ("failed", DETAIL_UNEXPECTED)

    post = mock.Mock(return_value=200)
    with mock.patch.object(automation, "_post_webhook", post):
        automation.reprocess_automation_event(
            event_id, database_path, WEBHOOK_URL, TIMEOUT
        )

    assert post.call_count == 1
    assert len(_cancelled_posts(post)) == 1
    stored = automation.events_repository.get_by_event_id(event_id, database_path)
    assert stored is not None
    assert stored.id == failed.id
    assert (stored.status, stored.detail) == ("sent", None)
    assert _count_events(event_id, database_path) == 1


def test_tc_d010_18_claim_failed_event_sin_patrones_comportamiento_heredado(
    database_path: Path,
) -> None:
    """DP-02: sin `permanent_pattern`/`retryable_pattern`, `claim_failed_event`
    conserva el comportamiento heredado y admite el `failed` (fila `pending`,
    `detail` a NULL)."""
    _, event_id, row_id = _cancel_with_http_error(400, database_path)
    detail_400 = DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code=400)
    before = automation.events_repository.get_by_event_id(event_id, database_path)
    assert before is not None
    assert (before.status, before.detail) == ("failed", detail_400)

    assert claim_failed_event(event_id, database_path) is True

    stored = automation.events_repository.get_by_event_id(event_id, database_path)
    assert stored is not None
    assert stored.id == row_id
    assert (stored.status, stored.detail) == ("pending", None)
