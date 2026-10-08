"""Booking rules: validate, check availability and register appointments."""

import re
from datetime import date
from pathlib import Path

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
)
from consultorio.content.services_catalog import SERVICES_CATALOG
from consultorio.persistence import appointments_repository as repository
from consultorio.persistence.appointments_repository import Appointment

SLOT_TAKEN: str = "slot_taken"

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


def get_available_hours(
    service: str, booking_date: str, database_path: str | Path
) -> list[str]:
    if not _is_valid_weekday(booking_date):
        return []
    booked = repository.list_booked_times(service, booking_date, database_path)
    return [hour for hour in BOOKING_HOURS if hour not in booked]


def create_booking(
    data: dict[str, str], database_path: str | Path
) -> Appointment | str:
    if repository.is_slot_taken(
        data["service"], data["date"], data["time"], database_path
    ):
        return SLOT_TAKEN
    try:
        return repository.insert_appointment(data, database_path)
    except Exception as exc:  # UNIQUE (service, date, time) in persistence
        if "UNIQUE" in str(exc).upper():
            return SLOT_TAKEN
        raise


def is_valid_iso_date(raw_date: str) -> bool:
    try:
        date.fromisoformat(raw_date)
    except ValueError:
        return False
    return True


def _is_valid_weekday(raw_date: str) -> bool:
    try:
        parsed = date.fromisoformat(raw_date)
    except ValueError:
        return False
    return parsed.weekday() < 5 and parsed >= date.today()
