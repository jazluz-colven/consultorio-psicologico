"""HU-018 end-to-end behaviour — T5 (spec 018).

Covers the notification events emitted by the delegated cancellation
(TC-018-005), the four events of a successful reschedule plus the cancellation
link (TC-018-007), the two "no cancellation" guards (TC-018-009/010), the RF-9
same-day/past behaviour with a frozen clock (TC-018-011), the post-cancellation
race (TC-018-017) and the cancel-before-create order (TC-018-018).

Every count is filtered by ``event_type``: a cancellation emits
``appointment.cancelled`` and ``appointment.cancellation_email``, and a
reschedule adds ``appointment.confirmed`` and ``appointment.confirmation_email``
(task.md review note 2026-10-23). The webhook is always patched, so no real
HTTP request is made.
"""

import datetime
import re
import sqlite3
from datetime import date, timedelta
from pathlib import Path
from unittest import mock

import pytest

from consultorio import create_app
from consultorio.config import TestConfig
from consultorio.content import admin_content as ac
from consultorio.content.appointment_content import (
    MSG_INVALID_DATE,
    STATUS_CANCELLED,
    STATUS_CONFIRMED,
)
from consultorio.persistence import appointments_repository as repository
from consultorio.persistence.appointments_repository import Appointment
from consultorio.services import appointment_service, automation_service
from consultorio.services.appointment_service import SLOT_TAKEN
from consultorio.web import admin as admin_module

TOKEN = "test-admin-token"
WEBHOOK_URL = "http://n8n.local/webhook/booking"
SERVICE_KEY = "nutrition"
DOCUMENT_NUMBER = "1234567890"
PATIENT_NAME = "Paciente de prueba"
PATIENT_EMAIL = "paciente@ejemplo.test"
PATIENT_PHONE = "3001234567"

CANCELLED_EVENT = "appointment.cancelled"
CANCELLATION_EMAIL_EVENT = "appointment.cancellation_email"
CONFIRMED_EVENT = "appointment.confirmed"
CONFIRMATION_EMAIL_EVENT = "appointment.confirmation_email"
FOUR_EVENT_TYPES = (
    CANCELLED_EVENT,
    CANCELLATION_EMAIL_EVENT,
    CONFIRMED_EVENT,
    CONFIRMATION_EMAIL_EVENT,
)


def _future_weekday(days_ahead: int = 2) -> str:
    candidate = date.today() + timedelta(days=days_ahead)
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


def _database_path(app) -> Path:
    return Path(app.config["DATABASE_PATH"])


def _insert_appointment(
    app,
    booking_date: str | None = None,
    slot: str = "09:00",
    service: str = SERVICE_KEY,
) -> Appointment:
    data = {
        "document_type": "CC",
        "document_number": DOCUMENT_NUMBER,
        "patient_name": PATIENT_NAME,
        "email": PATIENT_EMAIL,
        "phone": PATIENT_PHONE,
        "service": service,
        "date": booking_date or _future_weekday(),
        "time": slot,
    }
    return repository.insert_appointment(data, _database_path(app))


def _current(app, appointment_id: int) -> Appointment:
    current = repository.get_appointment_by_id(
        appointment_id, _database_path(app)
    )
    assert current is not None
    return current


def _appointment_count(app) -> int:
    connection = sqlite3.connect(str(_database_path(app)))
    try:
        return connection.execute(
            "SELECT COUNT(*) FROM appointments"
        ).fetchone()[0]
    finally:
        connection.close()


def _event_rows(app) -> list[tuple[str, str, int]]:
    connection = sqlite3.connect(str(_database_path(app)))
    try:
        rows = connection.execute(
            "SELECT event_type, status, appointment_id"
            " FROM automation_events ORDER BY id"
        ).fetchall()
    finally:
        connection.close()
    return [(row[0], row[1], row[2]) for row in rows]


def _events_of(app, event_type: str) -> list[tuple[str, str, int]]:
    return [row for row in _event_rows(app) if row[0] == event_type]


def _sent_of(app, event_type: str) -> list[tuple[str, str, int]]:
    return [row for row in _events_of(app, event_type) if row[1] == "sent"]


def _posts_of_type(post: mock.MagicMock, event_type: str) -> list[mock.call]:
    return [
        call
        for call in post.call_args_list
        if call[0][1].get("event_type") == event_type
    ]


def _reschedule_payload(
    booking_date: str | None = None,
    slot: str = "10:00",
    service: str = SERVICE_KEY,
) -> dict[str, str]:
    return {
        "admin_token": TOKEN,
        "service": service,
        "date": booking_date or _future_weekday(),
        "time": slot,
    }


@pytest.fixture()
def hu_app(tmp_path: Path):
    class TempConfig(TestConfig):
        DATABASE_PATH: Path = tmp_path / "hu-018.db"
        CONSULTORIO_ADMIN_TOKEN: str = TOKEN
        AUTOMATION_WEBHOOK_URL: str = WEBHOOK_URL
        AUTOMATION_WEBHOOK_AUTH_HEADER: str = ""

    application = create_app(TempConfig)
    application.config.update(TESTING=True)
    yield application


@pytest.fixture()
def hu_client(hu_app):
    return hu_app.test_client()


def test_tc_018_005_cancelar_emite_evento_cancellation_email_una_vez(
    hu_app, hu_client
) -> None:
    created = _insert_appointment(hu_app, slot="09:00")

    with mock.patch.object(
        automation_service, "_post_webhook", return_value=200
    ) as post:
        response = hu_client.post(
            f"/admin/citas/{created.id}/cancelar",
            data={"admin_token": TOKEN},
        )

    assert response.status_code == 200
    assert ac.ADMIN_CANCEL_SUCCESS in response.get_data(as_text=True)

    # Exactly one cancellation e-mail event and one matching POST.
    email_events = _events_of(hu_app, CANCELLATION_EMAIL_EVENT)
    assert len(email_events) == 1
    assert email_events[0][1] == "sent"
    assert email_events[0][2] == created.id
    assert len(_posts_of_type(post, CANCELLATION_EMAIL_EVENT)) == 1

    # The business event is a different row: it must not be counted as e-mail.
    cancelled_events = _events_of(hu_app, CANCELLED_EVENT)
    assert len(cancelled_events) == 1
    assert cancelled_events[0][1] == "sent"
    assert cancelled_events[0][2] == created.id

    assert _current(hu_app, created.id).status == STATUS_CANCELLED


def test_tc_018_007_reprogramar_a_horario_libre_emite_cuatro_eventos(
    hu_app, hu_client
) -> None:
    old = _insert_appointment(hu_app, slot="09:00")
    new_date = _future_weekday()

    with mock.patch.object(
        automation_service, "_post_webhook", return_value=200
    ) as post:
        response = hu_client.post(
            f"/admin/citas/{old.id}/reprogramar",
            data=_reschedule_payload(booking_date=new_date, slot="10:00"),
        )

    assert response.status_code == 200
    html = response.get_data(as_text=True)
    match = re.search(r"Cita reprogramada\. Nueva cita #(\d+)\.", html)
    assert match is not None
    new_id = int(match.group(1))

    old_row = _current(hu_app, old.id)
    new_row = _current(hu_app, new_id)
    assert old_row.status == STATUS_CANCELLED
    assert new_row.status == STATUS_CONFIRMED
    assert new_row.id != old_row.id

    # Exactly one `sent` event (and one POST) per event type.
    for event_type in FOUR_EVENT_TYPES:
        sent = _sent_of(hu_app, event_type)
        assert len(sent) == 1, event_type
        assert len(_posts_of_type(post, event_type)) == 1, event_type

    # Cancellation events belong to the old row, confirmations to the new one.
    assert _sent_of(hu_app, CANCELLED_EVENT)[0][2] == old.id
    assert _sent_of(hu_app, CANCELLATION_EMAIL_EVENT)[0][2] == old.id
    assert _sent_of(hu_app, CONFIRMED_EVENT)[0][2] == new_id
    assert _sent_of(hu_app, CONFIRMATION_EMAIL_EVENT)[0][2] == new_id

    # The new confirmation carries the absolute cancellation link (Spec 017).
    message = _posts_of_type(post, CONFIRMATION_EMAIL_EVENT)[0][0][1]["message"]
    expected_url = f"http://localhost/citas/cancelar/{new_id}"
    for part in (message["text"], message["html"]):
        assert expected_url in part
    assert f'href="{expected_url}"' in message["html"]

    # No extra event rows: the four expected ones are all there is.
    assert len(_event_rows(hu_app)) == 4
    assert {row[0] for row in _event_rows(hu_app)} == set(FOUR_EVENT_TYPES)


def test_tc_018_009_reprogramar_a_horario_ocupado_no_cancela(
    hu_app, hu_client
) -> None:
    old = _insert_appointment(hu_app, slot="09:00")
    target_date = _future_weekday()
    occupant = _insert_appointment(
        hu_app, booking_date=target_date, slot="10:00"
    )
    appointments_before = _appointment_count(hu_app)
    events_before = _event_rows(hu_app)

    with mock.patch.object(
        automation_service, "_post_webhook", return_value=200
    ) as post:
        response = hu_client.post(
            f"/admin/citas/{old.id}/reprogramar",
            data=_reschedule_payload(booking_date=target_date, slot="10:00"),
        )

    assert response.status_code == 200
    assert ac.ADMIN_SLOT_TAKEN in response.get_data(as_text=True)

    post.assert_not_called()
    assert _appointment_count(hu_app) == appointments_before
    assert _event_rows(hu_app) == events_before

    # The old row is untouched and the occupying row remains intact.
    assert _current(hu_app, old.id).status == STATUS_CONFIRMED
    occupant_row = _current(hu_app, occupant.id)
    assert occupant_row.status == STATUS_CONFIRMED
    assert occupant_row.service == occupant.service
    assert occupant_row.date == occupant.date
    assert occupant_row.time == occupant.time


def test_tc_018_010_reprogramar_con_fecha_pasada_o_fin_de_semana_no_cancela(
    hu_app, hu_client
) -> None:
    old = _insert_appointment(hu_app, slot="09:00")
    past_date = "2020-01-06"  # Monday, safely in the past
    weekend = date.today() + timedelta(days=1)
    while weekend.weekday() != 5:  # Saturday
        weekend += timedelta(days=1)
    appointments_before = _appointment_count(hu_app)
    events_before = _event_rows(hu_app)

    with mock.patch.object(
        automation_service, "_post_webhook", return_value=200
    ) as post:
        for invalid_date in (past_date, weekend.isoformat()):
            response = hu_client.post(
                f"/admin/citas/{old.id}/reprogramar",
                data=_reschedule_payload(
                    booking_date=invalid_date, slot="10:00"
                ),
            )
            assert response.status_code == 200
            html = response.get_data(as_text=True)
            assert MSG_INVALID_DATE in html
            assert ac.ADMIN_LABEL_SUMMARY in html
            assert _current(hu_app, old.id).status == STATUS_CONFIRMED

    post.assert_not_called()
    assert _appointment_count(hu_app) == appointments_before
    assert _event_rows(hu_app) == events_before


def test_tc_018_011_cancelar_hoy_y_pasada_y_reprogramar_a_hoy(
    hu_app, hu_client, monkeypatch
) -> None:
    fixed_today = date(2026, 11, 9)  # Monday, a working day
    assert fixed_today.weekday() == 0

    class FakeDate(datetime.date):
        @classmethod
        def today(cls):
            return cls(fixed_today.year, fixed_today.month, fixed_today.day)

    # Freeze only the service clock; production code is untouched.
    monkeypatch.setattr(appointment_service, "date", FakeDate)

    same_day = _insert_appointment(
        hu_app, booking_date="2026-11-09", slot="08:00"
    )
    past = _insert_appointment(
        hu_app, booking_date="2026-11-02", slot="08:30"
    )

    with mock.patch.object(
        automation_service, "_post_webhook", return_value=200
    ):
        same_day_response = hu_client.post(
            f"/admin/citas/{same_day.id}/cancelar",
            data={"admin_token": TOKEN},
        )
        past_response = hu_client.post(
            f"/admin/citas/{past.id}/cancelar",
            data={"admin_token": TOKEN},
        )

    # RF-9: the 3-hour restriction of Spec 017 does not apply here.
    assert same_day_response.status_code == 200
    assert ac.ADMIN_CANCEL_SUCCESS in same_day_response.get_data(as_text=True)
    assert _current(hu_app, same_day.id).status == STATUS_CANCELLED
    assert past_response.status_code == 200
    assert ac.ADMIN_CANCEL_SUCCESS in past_response.get_data(as_text=True)
    assert _current(hu_app, past.id).status == STATUS_CANCELLED

    old = _insert_appointment(
        hu_app, booking_date="2026-11-10", slot="09:00"
    )
    with mock.patch.object(
        automation_service, "_post_webhook", return_value=200
    ):
        rescheduled = hu_client.post(
            f"/admin/citas/{old.id}/reprogramar",
            data=_reschedule_payload(
                booking_date="2026-11-09", slot="10:00"
            ),
        )

    assert rescheduled.status_code == 200
    html = rescheduled.get_data(as_text=True)
    match = re.search(r"Cita reprogramada\. Nueva cita #(\d+)\.", html)
    assert match is not None
    new_id = int(match.group(1))
    assert _current(hu_app, old.id).status == STATUS_CANCELLED
    new_row = _current(hu_app, new_id)
    assert new_row.status == STATUS_CONFIRMED
    assert new_row.date == "2026-11-09"

    # The NEW date still follows Spec 004 (weekday, not before today), even
    # though cancelling the old row is always allowed (RF-9).
    invalid_old = _insert_appointment(
        hu_app, booking_date="2026-11-10", slot="09:30"
    )
    events_before = _event_rows(hu_app)
    with mock.patch.object(
        automation_service, "_post_webhook", return_value=200
    ) as post:
        for invalid_date in ("2026-11-02", "2026-11-14"):
            response = hu_client.post(
                f"/admin/citas/{invalid_old.id}/reprogramar",
                data=_reschedule_payload(
                    booking_date=invalid_date, slot="11:00"
                ),
            )
            assert response.status_code == 200
            assert MSG_INVALID_DATE in response.get_data(as_text=True)
            assert _current(hu_app, invalid_old.id).status == STATUS_CONFIRMED

    post.assert_not_called()
    assert _event_rows(hu_app) == events_before


def test_tc_018_017_carrera_tras_cancelar_create_booking_slot_taken(
    hu_app, hu_client
) -> None:
    old = _insert_appointment(hu_app, slot="09:00")
    target_date = _future_weekday()

    with (
        mock.patch.object(
            automation_service, "_post_webhook", return_value=200
        ) as post,
        mock.patch.object(
            admin_module, "create_booking", return_value=SLOT_TAKEN
        ),
    ):
        response = hu_client.post(
            f"/admin/citas/{old.id}/reprogramar",
            data=_reschedule_payload(booking_date=target_date, slot="10:00"),
        )

    assert response.status_code == 200
    assert ac.ADMIN_SLOT_TAKEN in response.get_data(as_text=True)

    # The earlier cancellation is committed and never reverted (RF-6).
    assert _current(hu_app, old.id).status == STATUS_CANCELLED
    assert _appointment_count(hu_app) == 1

    # Cancellation events exist; no confirmation event was emitted because no
    # new appointment was created.
    assert len(_sent_of(hu_app, CANCELLED_EVENT)) == 1
    assert len(_sent_of(hu_app, CANCELLATION_EMAIL_EVENT)) == 1
    assert _events_of(hu_app, CONFIRMED_EVENT) == []
    assert _events_of(hu_app, CONFIRMATION_EMAIL_EVENT) == []
    assert len(_posts_of_type(post, CANCELLED_EVENT)) == 1
    assert len(_posts_of_type(post, CANCELLATION_EMAIL_EVENT)) == 1


def test_tc_018_018_orden_cancelar_antes_de_crear(
    hu_app, hu_client, monkeypatch
) -> None:
    old = _insert_appointment(hu_app, slot="09:00")
    target_date = _future_weekday()
    calls: list[str] = []

    real_cancel = appointment_service.cancel_appointment
    real_create = appointment_service.create_booking

    def spy_cancel(*args, **kwargs):
        calls.append("cancel_appointment")
        return real_cancel(*args, **kwargs)

    def spy_create(*args, **kwargs):
        calls.append("create_booking")
        return real_create(*args, **kwargs)

    monkeypatch.setattr(admin_module, "cancel_appointment", spy_cancel)
    monkeypatch.setattr(admin_module, "create_booking", spy_create)

    with mock.patch.object(
        automation_service, "_post_webhook", return_value=200
    ):
        response = hu_client.post(
            f"/admin/citas/{old.id}/reprogramar",
            data=_reschedule_payload(booking_date=target_date, slot="10:00"),
        )

    assert response.status_code == 200
    assert calls == ["cancel_appointment", "create_booking"]

    html = response.get_data(as_text=True)
    match = re.search(r"Cita reprogramada\. Nueva cita #(\d+)\.", html)
    assert match is not None
    new_id = int(match.group(1))
    assert _current(hu_app, old.id).status == STATUS_CANCELLED
    assert _current(hu_app, new_id).status == STATUS_CONFIRMED
