"""Booking rules: validate, check availability, register and cancel
appointments (HU-004…HU-008, HU-010)."""

import re
from datetime import date, timedelta

from consultorio.content.appointment_content import (
    BOOKING_HOURS,
    DOCUMENT_TYPES,
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
    STATUS_CANCELLED,
)
from consultorio.content.automation_content import (
    CANCELLED_EVENT_TYPE,
    CANCELLED_EVENT_VERSION,
)
from consultorio.content.services_catalog import SERVICES_CATALOG
from consultorio.persistence import appointments_repository as repository
from consultorio.persistence.appointments_repository import (
    Appointment,
    DatabaseResource,
)
from consultorio.persistence.database import (
    is_slot_uniqueness_violation,
    translate_persistence_error,
)
from consultorio.services import automation_service, email_service

SLOT_TAKEN: str = "slot_taken"
APPOINTMENT_NOT_FOUND: str = "appointment_not_found"
ALREADY_CANCELLED: str = "already_cancelled"

_DOCUMENT_NUMBER_RE = re.compile(r"^[0-9]{4,20}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
_PHONE_RE = re.compile(r"^[0-9]{7,15}$")
_DOCUMENT_CODES: tuple[str, ...] = tuple(code for code, _ in DOCUMENT_TYPES)


def validate_booking(data: dict[str, str]) -> dict[str, str]:
    errors: dict[str, str] = {}

    service = data.get("service", "").strip()
    if not service:
        errors["service"] = MSG_REQUIRED_SERVICE
    elif service not in SERVICES_CATALOG:
        errors["service"] = MSG_INVALID_SERVICE

    raw_date = data.get("date", "").strip()
    if not raw_date:
        errors["date"] = MSG_REQUIRED_DATE
    elif not _is_valid_weekday(raw_date):
        errors["date"] = MSG_INVALID_DATE

    time = data.get("time", "").strip()
    if not time:
        errors["time"] = MSG_REQUIRED_TIME
    elif time not in BOOKING_HOURS:
        errors["time"] = MSG_INVALID_TIME

    document_type = data.get("document_type", "").strip()
    if not document_type:
        errors["document_type"] = MSG_REQUIRED_DOC_TYPE

    document_number = data.get("document_number", "").strip()
    if not document_number:
        errors["document_number"] = MSG_REQUIRED_DOC_NUMBER
    elif not _DOCUMENT_NUMBER_RE.fullmatch(document_number):
        errors["document_number"] = MSG_INVALID_DOC_NUMBER

    patient_name = data.get("patient_name", "").strip()
    if not patient_name:
        errors["patient_name"] = MSG_REQUIRED_NAME
    elif not 3 <= len(patient_name) <= 120:
        errors["patient_name"] = MSG_INVALID_NAME

    email = data.get("email", "").strip()
    if not email:
        errors["email"] = MSG_REQUIRED_EMAIL
    elif not _EMAIL_RE.fullmatch(email):
        errors["email"] = MSG_INVALID_EMAIL

    phone = data.get("phone", "").strip()
    if not phone:
        errors["phone"] = MSG_REQUIRED_PHONE
    elif not _PHONE_RE.fullmatch(phone):
        errors["phone"] = MSG_INVALID_PHONE

    return errors


def get_hours_with_status(
    service: str, booking_date: str, database: DatabaseResource
) -> list[tuple[str, bool]]:
    """Ordered (hour, is_free) pairs for a weekday; [] on weekend/past/invalid."""
    if not _is_valid_weekday(booking_date):
        return []
    booked = repository.list_booked_times(service, booking_date, database)
    return [(hour, hour not in booked) for hour in BOOKING_HOURS]


def get_available_hours(
    service: str, booking_date: str, database: DatabaseResource
) -> list[str]:
    return [
        hour
        for hour, is_free in get_hours_with_status(
            service, booking_date, database
        )
        if is_free
    ]


def get_available_days(
    service: str, year: int, month: int, database: DatabaseResource
) -> list[str]:
    """Weekdays >= today in the month with at least one free hour."""
    first = date(year, month, 1)
    if month == 12:
        last = date(year, 12, 31)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
    booked_by_date = repository.list_booked_times_by_date(
        service, first.isoformat(), last.isoformat(), database
    )
    days: list[str] = []
    current = first
    today = date.today()
    while current <= last:
        if current.weekday() < 5 and current >= today:
            booked = booked_by_date.get(current.isoformat(), [])
            if any(hour not in booked for hour in BOOKING_HOURS):
                days.append(current.isoformat())
        current += timedelta(days=1)
    return days


def create_booking(
    data: dict[str, str],
    database: DatabaseResource,
    automation_url: str = "",
    automation_timeout: float = 3.0,
    automation_auth_header: str = "",
    cancellation_url_builder: "Callable[[int], str] | None" = None,
) -> Appointment | str:
    """Validate availability, insert the appointment and notify (HU-004/008).

    ``cancellation_url_builder`` is optional (spec 017 RF-13, plan D9): the
    web layer passes a callable because the id only exists after the INSERT.
    It receives the new id and returns the absolute cancellation URL. The
    annotation stays a forward-reference string on purpose: the Spec 010
    stdlib-only check (``test_hu_010``) restricts this module's imports.

    Only the slot unique-index violation becomes ``SLOT_TAKEN`` (plan D6).
    Driver unavailability (``OperationalError``/``InterfaceError``) is
    translated to ``PersistenceUnavailable``; it is never reported as an
    occupied slot. Programming errors and other integrity failures keep
    propagating unchanged.
    """
    try:
        if repository.is_slot_taken(
            data["service"], data["date"], data["time"], database
        ):
            return SLOT_TAKEN
        appointment = repository.insert_appointment(data, database)
    except Exception as error:
        if is_slot_uniqueness_violation(error):
            return SLOT_TAKEN
        translated = translate_persistence_error(error)
        if translated is error:
            raise
        raise translated from error
    # best-effort automation: never raises, never conditions the booking (RF-2/RF-7)
    automation_service.on_appointment_confirmed(
        appointment,
        database,
        automation_url,
        automation_timeout,
        automation_auth_header,
    )
    cancellation_url = ""
    if cancellation_url_builder is not None and appointment.id:
        cancellation_url = cancellation_url_builder(appointment.id)
    # best-effort confirmation e-mail via n8n (HU-008): never raises either
    email_service.send_confirmation(
        appointment,
        database,
        automation_url,
        automation_timeout,
        automation_auth_header,
        cancellation_url=cancellation_url,
    )
    return appointment


def cancel_appointment(
    appointment_id: int,
    database: DatabaseResource,
    automation_url: str = "",
    automation_timeout: float = 3.0,
    automation_auth_header: str = "",
) -> Appointment | str:
    """Atomically move a confirmed appointment to cancelled (spec 010 RF-1).

    Returns the updated appointment, or the APPOINTMENT_NOT_FOUND /
    ALREADY_CANCELLED sentinel. The business event `appointment.cancelled` is
    emitted first and the cancellation e-mail second (RF-8, F2-D1); both are
    best-effort and only attempted on the first successful transition
    (RF-4, D6/D7).
    """
    appointment = repository.get_appointment_by_id(appointment_id, database)
    if appointment is None:
        return APPOINTMENT_NOT_FOUND
    updated = repository.update_appointment_status_with_pending_event(
        appointment_id,
        STATUS_CANCELLED,
        f"{CANCELLED_EVENT_TYPE}:{appointment_id}:v{CANCELLED_EVENT_VERSION}",
        CANCELLED_EVENT_TYPE,
        CANCELLED_EVENT_VERSION,
        database,
    )
    if updated is None:
        # already cancelled / concurrent cancellation: no second notification
        return ALREADY_CANCELLED
    # business event first (RF-8, F2-D1): best-effort, never raises (RF-10)
    automation_service.publish_cancelled_event(
        updated,
        database,
        automation_url,
        automation_timeout,
        automation_auth_header,
    )
    # cancellation e-mail after the business event (F2-D1): best-effort too
    email_service.send_cancellation(
        updated,
        database,
        automation_url,
        automation_timeout,
        automation_auth_header,
    )
    return updated


def is_valid_iso_date(raw_date: str) -> bool:
    try:
        date.fromisoformat(raw_date)
    except ValueError:
        return False
    return True


def is_valid_month(raw_month: str) -> bool:
    """True for a real YYYY-MM month (e.g. 2026-10)."""
    parts = raw_month.split("-")
    if len(parts) != 2 or not all(part.isdigit() for part in parts):
        return False
    year, month = int(parts[0]), int(parts[1])
    if not (1 <= month <= 12):
        return False
    try:
        date(year, month, 1)
    except ValueError:
        return False
    return True


def _is_valid_weekday(raw_date: str) -> bool:
    try:
        parsed = date.fromisoformat(raw_date)
    except ValueError:
        return False
    return parsed.weekday() < 5 and parsed >= date.today()
