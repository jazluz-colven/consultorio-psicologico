"""E-mail events dispatched to n8n: confirmation (HU-008) and cancellation
(HU-010).

The application composes the message (subject, plain text, HTML); n8n only
transports it (Q6, spec 008). The module never raises: the booking/cancellation
is already persisted when this runs, so a delivery failure can never invalidate
it (RF-3, best-effort Q2; spec 010 D7).
"""

import re
import urllib.error
from datetime import date, datetime

from consultorio.content.appointment_content import (
    STATUS_CANCELLED_LABEL,
    STATUS_CONFIRMED_LABEL,
)
from consultorio.content.email_content import (
    CANCELLATION_EMAIL_BODY_HEADER,
    CANCELLATION_EMAIL_FOOTER,
    CANCELLATION_EMAIL_SUBJECT_TEMPLATE,
    DETAIL_CANCELLATION_NOT_CONFIGURED,
    DETAIL_EMAIL_NOT_CONFIGURED,
    DETAIL_INVALID_RECIPIENT,
    DETAIL_INVALID_RESPONSE_TEMPLATE,
    DETAIL_TIMEOUT,
    DETAIL_UNEXPECTED,
    DETAIL_UNAVAILABLE,
    EMAIL_BODY_HEADER,
    EMAIL_FOOTER,
    EMAIL_GREETING_TEMPLATE,
    EMAIL_HTML_TEMPLATE,
    EMAIL_LABEL_DATE,
    EMAIL_LABEL_REFERENCE,
    EMAIL_LABEL_SERVICE,
    EMAIL_LABEL_STATUS,
    EMAIL_LABEL_TIME,
    EMAIL_SENDER_NAME,
    EMAIL_SUBJECT_TEMPLATE,
    MSG_APPOINTMENT_INCOMPLETE,
    MONTHS_ES,
    WEEKDAYS_ES,
)
from consultorio.content.services_catalog import SERVICES_CATALOG
from consultorio.persistence import automation_events_repository as events_repository
from consultorio.persistence.appointments_repository import Appointment
from consultorio.services import automation_service

EVENT_TYPE: str = "appointment.confirmation_email"
EVENT_VERSION: int = 1

CANCELLATION_EVENT_TYPE: str = "appointment.cancellation_email"
CANCELLATION_EVENT_VERSION: int = 1

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def format_spanish_date(iso_date: str) -> str:
    """«martes, 15 de octubre de 2026» from a YYYY-MM-DD string (legibility)."""
    parsed = date.fromisoformat(iso_date)
    weekday = WEEKDAYS_ES[parsed.weekday()]
    month = MONTHS_ES[parsed.month - 1]
    return f"{weekday}, {parsed.day} de {month} de {parsed.year}"


def build_confirmation_message(appointment: Appointment) -> dict[str, str]:
    """Subject, plain text and HTML parts of the confirmation (RF-2)."""
    service_name = SERVICES_CATALOG[appointment.service]["name"]
    date_label = format_spanish_date(appointment.date)
    status_label = STATUS_CONFIRMED_LABEL

    subject = EMAIL_SUBJECT_TEMPLATE.format(
        service_name=service_name, date_label=date_label, time=appointment.time
    )
    greeting = EMAIL_GREETING_TEMPLATE.format(
        patient_name=appointment.patient_name
    )
    text = "\n".join(
        [
            f"{EMAIL_SENDER_NAME}",
            "",
            greeting,
            EMAIL_BODY_HEADER,
            "",
            f"{EMAIL_LABEL_SERVICE}: {service_name}",
            f"{EMAIL_LABEL_DATE}: {date_label}",
            f"{EMAIL_LABEL_TIME}: {appointment.time}",
            f"{EMAIL_LABEL_STATUS}: {status_label}",
            f"{EMAIL_LABEL_REFERENCE}: #{appointment.id}",
            "",
            EMAIL_FOOTER,
        ]
    )
    html = EMAIL_HTML_TEMPLATE.format(
        sender_name=EMAIL_SENDER_NAME,
        greeting=greeting,
        body_header=EMAIL_BODY_HEADER,
        label_service=EMAIL_LABEL_SERVICE,
        label_date=EMAIL_LABEL_DATE,
        label_time=EMAIL_LABEL_TIME,
        label_status=EMAIL_LABEL_STATUS,
        label_reference=EMAIL_LABEL_REFERENCE,
        service_name=service_name,
        date_label=date_label,
        time=appointment.time,
        status=status_label,
        appointment_id=appointment.id,
        footer=EMAIL_FOOTER,
    )
    return {"subject": subject, "text": text, "html": html}


def build_cancellation_message(appointment: Appointment) -> dict[str, str]:
    """Subject, plain text and HTML parts of the cancellation (spec 010 RF-2)."""
    service_name = SERVICES_CATALOG[appointment.service]["name"]
    date_label = format_spanish_date(appointment.date)
    status_label = STATUS_CANCELLED_LABEL

    subject = CANCELLATION_EMAIL_SUBJECT_TEMPLATE.format(
        service_name=service_name, date_label=date_label, time=appointment.time
    )
    greeting = EMAIL_GREETING_TEMPLATE.format(
        patient_name=appointment.patient_name
    )
    text = "\n".join(
        [
            f"{EMAIL_SENDER_NAME}",
            "",
            greeting,
            CANCELLATION_EMAIL_BODY_HEADER,
            "",
            f"{EMAIL_LABEL_SERVICE}: {service_name}",
            f"{EMAIL_LABEL_DATE}: {date_label}",
            f"{EMAIL_LABEL_TIME}: {appointment.time}",
            f"{EMAIL_LABEL_STATUS}: {status_label}",
            f"{EMAIL_LABEL_REFERENCE}: #{appointment.id}",
            "",
            CANCELLATION_EMAIL_FOOTER,
        ]
    )
    html = EMAIL_HTML_TEMPLATE.format(
        sender_name=EMAIL_SENDER_NAME,
        greeting=greeting,
        body_header=CANCELLATION_EMAIL_BODY_HEADER,
        label_service=EMAIL_LABEL_SERVICE,
        label_date=EMAIL_LABEL_DATE,
        label_time=EMAIL_LABEL_TIME,
        label_status=EMAIL_LABEL_STATUS,
        label_reference=EMAIL_LABEL_REFERENCE,
        service_name=service_name,
        date_label=date_label,
        time=appointment.time,
        status=status_label,
        appointment_id=appointment.id,
        footer=CANCELLATION_EMAIL_FOOTER,
    )
    return {"subject": subject, "text": text, "html": html}


def build_event(appointment: Appointment) -> dict[str, object]:
    """Payload allowlist of spec 008: recipient + message, no document/phone."""
    return {
        "event_id": f"{EVENT_TYPE}:{appointment.id}:v{EVENT_VERSION}",
        "event_type": EVENT_TYPE,
        "event_version": EVENT_VERSION,
        "occurred_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "recipient": {
            "to": appointment.email,
            "patient_name": appointment.patient_name,
        },
        "message": build_confirmation_message(appointment),
        "appointment": {
            "id": appointment.id,
            "service": appointment.service,
            "date": appointment.date,
            "time": appointment.time,
            "status": appointment.status,
        },
    }


def build_cancellation_event(appointment: Appointment) -> dict[str, object]:
    """Payload allowlist of spec 010: recipient + message, no document/phone."""
    return {
        "event_id": (
            f"{CANCELLATION_EVENT_TYPE}:{appointment.id}"
            f":v{CANCELLATION_EVENT_VERSION}"
        ),
        "event_type": CANCELLATION_EVENT_TYPE,
        "event_version": CANCELLATION_EVENT_VERSION,
        "occurred_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "recipient": {
            "to": appointment.email,
            "patient_name": appointment.patient_name,
        },
        "message": build_cancellation_message(appointment),
        "appointment": {
            "id": appointment.id,
            "service": appointment.service,
            "date": appointment.date,
            "time": appointment.time,
            "status": appointment.status,
        },
    }


def send_confirmation(
    appointment: Appointment,
    database_path: str,
    webhook_url: str = "",
    timeout_seconds: float = 3.0,
    auth_header: str = "",
) -> None:
    """Register the e-mail event and best-effort dispatch it; never raises."""
    try:
        event_id = f"{EVENT_TYPE}:{appointment.id}:v{EVENT_VERSION}"
        if not _has_complete_data(appointment):
            if appointment.id:
                if events_repository.insert_event(
                    event_id, EVENT_TYPE, EVENT_VERSION, appointment.id,
                    database_path,
                ):
                    events_repository.mark_failed(
                        event_id, MSG_APPOINTMENT_INCOMPLETE, database_path
                    )
            return
        if not _is_valid_recipient(appointment.email):
            if events_repository.insert_event(
                event_id, EVENT_TYPE, EVENT_VERSION, appointment.id,
                database_path,
            ):
                events_repository.mark_failed(
                    event_id, DETAIL_INVALID_RECIPIENT, database_path
                )
            return
        event = build_event(appointment)
        created = events_repository.insert_event(
            event_id, EVENT_TYPE, EVENT_VERSION, appointment.id, database_path
        )
        if not created:
            # same reservation processed again: no duplicate e-mails (RF-4)
            return
        if not webhook_url:
            events_repository.mark_skipped(
                event_id, DETAIL_EMAIL_NOT_CONFIGURED, database_path
            )
            return
        try:
            # module-attribute reference (D14): existing test patches intercept it
            status_code = automation_service._post_webhook(
                webhook_url, event, timeout_seconds, auth_header
            )
        except TimeoutError:
            events_repository.mark_failed(event_id, DETAIL_TIMEOUT, database_path)
            return
        except urllib.error.URLError:
            events_repository.mark_failed(
                event_id, DETAIL_UNAVAILABLE, database_path
            )
            return
        except Exception:
            events_repository.mark_failed(
                event_id, DETAIL_UNEXPECTED, database_path
            )
            return
        if 200 <= status_code < 300:
            events_repository.mark_sent(event_id, database_path)
        else:
            events_repository.mark_failed(
                event_id,
                DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code=status_code),
                database_path,
            )
    except Exception:
        # the confirmation must never invalidate the booking (RF-3, Q2)
        return


def send_cancellation(
    appointment: Appointment,
    database_path: str,
    webhook_url: str = "",
    timeout_seconds: float = 3.0,
    auth_header: str = "",
) -> None:
    """Register the cancellation e-mail event and best-effort dispatch it.

    Never raises: the cancellation is already committed when this runs, so a
    delivery failure can never revert or block it (spec 010 RF-1, D7).
    """
    try:
        event_id = (
            f"{CANCELLATION_EVENT_TYPE}:{appointment.id}"
            f":v{CANCELLATION_EVENT_VERSION}"
        )
        if not _has_complete_data(appointment):
            if appointment.id:
                if events_repository.insert_event(
                    event_id,
                    CANCELLATION_EVENT_TYPE,
                    CANCELLATION_EVENT_VERSION,
                    appointment.id,
                    database_path,
                ):
                    events_repository.mark_failed(
                        event_id, MSG_APPOINTMENT_INCOMPLETE, database_path
                    )
            return
        if not _is_valid_recipient(appointment.email):
            if events_repository.insert_event(
                event_id,
                CANCELLATION_EVENT_TYPE,
                CANCELLATION_EVENT_VERSION,
                appointment.id,
                database_path,
            ):
                events_repository.mark_failed(
                    event_id, DETAIL_INVALID_RECIPIENT, database_path
                )
            return
        event = build_cancellation_event(appointment)
        created = events_repository.insert_event(
            event_id,
            CANCELLATION_EVENT_TYPE,
            CANCELLATION_EVENT_VERSION,
            appointment.id,
            database_path,
        )
        if not created:
            # cancellation reprocessed: no duplicate e-mails (spec 010 RF-4)
            return
        if not webhook_url:
            events_repository.mark_skipped(
                event_id, DETAIL_CANCELLATION_NOT_CONFIGURED, database_path
            )
            return
        try:
            # module-attribute reference (D14): existing test patches intercept it
            status_code = automation_service._post_webhook(
                webhook_url, event, timeout_seconds, auth_header
            )
        except TimeoutError:
            events_repository.mark_failed(event_id, DETAIL_TIMEOUT, database_path)
            return
        except urllib.error.URLError:
            events_repository.mark_failed(
                event_id, DETAIL_UNAVAILABLE, database_path
            )
            return
        except Exception:
            events_repository.mark_failed(
                event_id, DETAIL_UNEXPECTED, database_path
            )
            return
        if 200 <= status_code < 300:
            events_repository.mark_sent(event_id, database_path)
        else:
            events_repository.mark_failed(
                event_id,
                DETAIL_INVALID_RESPONSE_TEMPLATE.format(status_code=status_code),
                database_path,
            )
    except Exception:
        # the cancellation email must never revert the cancellation (RF-1)
        return


def _has_complete_data(appointment: Appointment) -> bool:
    required = (
        appointment.id,
        appointment.service,
        appointment.date,
        appointment.time,
    )
    return all(required)


def _is_valid_recipient(email: str | None) -> bool:
    return bool(email) and bool(_EMAIL_RE.fullmatch(str(email).strip()))
