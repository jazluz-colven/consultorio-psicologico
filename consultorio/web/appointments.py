"""Booking routes: form, availability JSON and confirmation page."""

from datetime import date, timedelta
from pathlib import Path

from flask import Blueprint, abort, current_app, jsonify, redirect, render_template
from flask import request, url_for

from consultorio.content.appointment_content import (
    BOOKING_BLOCK_AFTERNOON,
    BOOKING_BLOCK_MORNING,
    BOOKING_HELPER,
    BOOKING_PAGE_TITLE,
    BOOKING_PATIENT_SECTION_TITLE,
    BOOKING_SCHEDULE_SECTION_TITLE,
    CALENDAR_LEGEND_FREE,
    CALENDAR_LEGEND_FULL,
    CONFIRMATION_TITLE,
    DAY_LABEL_NO_HOURS,
    DOCUMENT_TYPES,
    MSG_CHECKING_HOURS,
    MSG_INVALID_PARAMS,
    MSG_NO_HOURS,
    MSG_OCCUPIED_HOUR,
    MSG_SELECT_DATE_HINT,
    MSG_SLOT_TAKEN,
    STATUS_PENDING_LABEL,
)
from consultorio.content.services_catalog import SERVICES_CATALOG
from consultorio.services.appointment_service import (
    SLOT_TAKEN,
    create_booking,
    get_available_days,
    get_hours_with_status,
    is_valid_iso_date,
    is_valid_month,
    validate_booking,
)
from consultorio.services.home_service import get_home_view
from consultorio.services.services_service import get_services_view

bp = Blueprint("appointments", __name__)

_BOOKING_FIELDS: tuple[str, ...] = (
    "service",
    "date",
    "time",
    "document_type",
    "document_number",
    "patient_name",
    "email",
    "phone",
)


def _database_path() -> Path:
    return Path(current_app.config["DATABASE_PATH"])


def _next_weekday() -> str:
    candidate = date.today()
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


def _default_service() -> str:
    return next(iter(SERVICES_CATALOG))


def _render_form(values: dict[str, str], errors: dict[str, str], status: int = 200):
    default_date = _next_weekday()
    default_service = _default_service()
    service = values.get("service", "") or default_service
    booking_date = values.get("date", "") or default_date
    pairs = get_hours_with_status(service, booking_date, _database_path())
    morning_hours = [hour for hour, free in pairs if free and hour < "12:00"]
    afternoon_hours = [hour for hour, free in pairs if free and hour >= "12:00"]
    morning_taken = [hour for hour, free in pairs if not free and hour < "12:00"]
    afternoon_taken = [hour for hour, free in pairs if not free and hour >= "12:00"]
    return (
        render_template(
            "appointments/index.html",
            view=get_home_view(),
            services=get_services_view(),
            document_types=DOCUMENT_TYPES,
            morning_hours=morning_hours,
            afternoon_hours=afternoon_hours,
            morning_taken=morning_taken,
            afternoon_taken=afternoon_taken,
            hours_empty_message=MSG_NO_HOURS,
            block_morning=BOOKING_BLOCK_MORNING,
            block_afternoon=BOOKING_BLOCK_AFTERNOON,
            patient_section_title=BOOKING_PATIENT_SECTION_TITLE,
            schedule_section_title=BOOKING_SCHEDULE_SECTION_TITLE,
            select_date_hint=MSG_SELECT_DATE_HINT,
            today_iso=date.today().isoformat(),
            selected_date=booking_date,
            helper=BOOKING_HELPER,
            page_title=BOOKING_PAGE_TITLE,
            legend_free=CALENDAR_LEGEND_FREE,
            legend_full=CALENDAR_LEGEND_FULL,
            occupied_label=MSG_OCCUPIED_HOUR,
            checking_message=MSG_CHECKING_HOURS,
            day_label_no_hours=DAY_LABEL_NO_HOURS,
            slot_taken_message=MSG_SLOT_TAKEN,
            values=values,
            errors=errors,
        ),
        status,
    )


@bp.route("/citas", methods=["GET", "POST"])
def index():
    if request.method == "GET":
        return _render_form({}, {})

    data = {field: request.form.get(field, "") for field in _BOOKING_FIELDS}
    errors = validate_booking(data)
    if errors:
        return _render_form(data, errors)

    result = create_booking(data, _database_path())
    if result == SLOT_TAKEN:
        return _render_form(data, {"time": MSG_SLOT_TAKEN})

    return redirect(url_for("appointments.confirm", cita_id=result.id), code=303)


@bp.get("/citas/horarios")
def horarios():
    service = request.args.get("service", "")
    booking_date = request.args.get("date", "")
    if service not in SERVICES_CATALOG or not is_valid_iso_date(booking_date):
        return jsonify({"error": MSG_INVALID_PARAMS}), 400
    pairs = get_hours_with_status(service, booking_date, _database_path())
    return (
        jsonify(
            {
                "available": [hour for hour, free in pairs if free],
                "occupied": [hour for hour, free in pairs if not free],
            }
        ),
        200,
    )


@bp.get("/citas/disponibilidad")
def disponibilidad():
    service = request.args.get("service", "")
    month = request.args.get("month", "")
    if service not in SERVICES_CATALOG or not is_valid_month(month):
        return jsonify({"error": MSG_INVALID_PARAMS}), 400
    year_str, month_str = month.split("-")
    days = get_available_days(
        service, int(year_str), int(month_str), _database_path()
    )
    return jsonify({"days": days}), 200


@bp.get("/citas/confirmada/<int:cita_id>")
def confirm(cita_id: int):
    appointment = _find_appointment(cita_id)
    if appointment is None:
        abort(404)
    service_name = SERVICES_CATALOG[appointment.service]["name"]
    return render_template(
        "appointments/confirmation.html",
        view=get_home_view(),
        appointment=appointment,
        service_name=service_name,
        status_label=STATUS_PENDING_LABEL,
        confirmation_title=CONFIRMATION_TITLE,
        page_title=CONFIRMATION_TITLE,
    )


def _find_appointment(cita_id: int):
    from consultorio.persistence.appointments_repository import (
        get_appointment_by_id,
    )

    return get_appointment_by_id(cita_id, _database_path())
