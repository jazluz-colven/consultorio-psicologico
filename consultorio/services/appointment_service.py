"""Booking rules: validate, check availability and register appointments."""

import re
import sqlite3
from datetime import date, timedelta
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
from consultorio.services import automation_service

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


def get_hours_with_status(
    service: str, booking_date: str, database_path: str | Path
) -> list[tuple[str, bool]]:
    """Ordered (hour, is_free) pairs for a weekday; [] on weekend/past/invalid."""
    if not _is_valid_weekday(booking_date):
        return []
    booked = repository.list_booked_times(service, booking_date, database_path)
    return [(hour, hour not in booked) for hour in BOOKING_HOURS]


def get_available_hours(
    service: str, booking_date: str, database_path: str | Path
) -> list[str]:
    return [
        hour
        for hour, is_free in get_hours_with_status(
            service, booking_date, database_path
        )
        if is_free
    ]


def get_available_days(
    service: str, year: int, month: int, database_path: str | Path
) -> list[str]:
    """Weekdays >= today in the month with at least one free hour."""
    first = date(year, month, 1)
    if month == 12:
        last = date(year, 12, 31)
    else:
        last = date(year, month + 1, 1) - timedelta(days=1)
    booked_by_date = repository.list_booked_times_by_date(
        service, first.isoformat(), last.isoformat(), database_path
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
    database_path: str | Path,
    automation_url: str = "",
    automation_timeout: float = 3.0,
    automation_auth_header: str = "",
) -> Appointment | str:
    if repository.is_slot_taken(
        data["service"], data["date"], data["time"], database_path
    ):
        return SLOT_TAKEN
    try:
        appointment = repository.insert_appointment(data, database_path)
    except sqlite3.IntegrityError:
        # UNIQUE (service, date, time) enforced at the persistence point
        return SLOT_TAKEN
    except sqlite3.OperationalError:
        # lock/busy under concurrency: user-facing rejection, never a raw 500
        return SLOT_TAKEN
    # any other exception propagates (a real 500 must not be silenced)
    # best-effort automation: never raises, never conditions the booking (RF-2/RF-7)
    automation_service.on_appointment_confirmed(
        appointment,
        database_path,
        automation_url,
        automation_timeout,
        automation_auth_header,
    )
    return appointment


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
