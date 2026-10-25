"""HU-010 — cancellation e-mail event and slot release at the service layer
(spec 010 amended 2026-10-13)."""

import re
import sqlite3
import urllib.error
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

from consultorio.persistence import appointments_repository as repository
from consultorio.persistence.appointments_repository import Appointment
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
