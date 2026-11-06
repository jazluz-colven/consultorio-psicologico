"""Admin appointment management routes (HU-018, spec 018).

Minimal internal surface protected by a shared token: the detail view with the
mandatory summary and both forms (RF-2) and the delegated cancellation
(RF-3). Rescheduling is T4.

Plan decisions applied here:

- **D1**: blueprint ``admin`` with ``url_prefix="/admin"``. The POST renders
  the result directly (200); no PRG.
- **D2**: the token arrives through ``X-Admin-Token`` (scripts/tests), the
  hidden ``admin_token`` field (forms) or ``?token=`` (GET only). An empty
  ``CONSULTORIO_ADMIN_TOKEN`` disables the whole surface (403). Every admin
  response carries ``Cache-Control: no-store`` and ``Referrer-Policy:
  no-referrer``.
- **D3**: cancel loads the row first (404 when missing); an already cancelled
  row answers the Q2 literal without calling the service; otherwise the
  cancellation is delegated verbatim to ``cancel_appointment()``.
- **D7/D8**: available/processing/success/conflict/error map to the detail,
  the rendered result and the literals; no copy lives in this module.
- **D12**: neither the token nor personal data are logged.
"""

import hmac
from pathlib import Path

from flask import Blueprint, current_app, render_template, request, url_for

from consultorio.content.admin_content import (
    ADMIN_ACCESS_DENIED,
    ADMIN_APPOINTMENT_NOT_FOUND,
    ADMIN_BACK_BUTTON,
    ADMIN_CANCEL_BUTTON,
    ADMIN_CANCEL_NOTICE,
    ADMIN_CANCEL_SUCCESS,
    ADMIN_CANCEL_TITLE,
    ADMIN_LABEL_NEW_DATE,
    ADMIN_LABEL_PATIENT,
    ADMIN_LABEL_SERVICE,
    ADMIN_LABEL_STATUS,
    ADMIN_LABEL_SUMMARY,
    ADMIN_LABEL_TIME,
    ADMIN_MSG_ALREADY_CANCELLED,
    ADMIN_PAGE_TITLE,
    ADMIN_RESCHEDULE_BUTTON,
    ADMIN_RESCHEDULE_NOTICE,
    ADMIN_RESCHEDULE_TITLE,
)
from consultorio.content.appointment_content import (
    BOOKING_BLOCK_AFTERNOON,
    BOOKING_BLOCK_MORNING,
    BOOKING_HOURS,
    STATUS_CANCELLED,
    STATUS_CANCELLED_LABEL,
    STATUS_CONFIRMED_LABEL,
)
from consultorio.content.cancellation_content import LABEL_DATE
from consultorio.content.services_catalog import SERVICES_CATALOG
from consultorio.persistence.appointments_repository import get_appointment_by_id
from consultorio.services.appointment_service import (
    ALREADY_CANCELLED,
    APPOINTMENT_NOT_FOUND,
    cancel_appointment,
)
from consultorio.services.email_service import format_spanish_date
from consultorio.services.home_service import get_home_view

bp = Blueprint("admin", __name__, url_prefix="/admin")


def _database_path() -> Path:
    return Path(current_app.config["DATABASE_PATH"])


def _check_token() -> bool:
    """Validate the shared admin token without ever logging it (D2).

    Accepts ``X-Admin-Token``, the hidden ``admin_token`` form field and, for
    GET only, ``?token=``. Missing/empty values and non-ASCII input simply do
    not match; an empty configured token disables the surface.
    """
    expected = current_app.config.get("CONSULTORIO_ADMIN_TOKEN") or ""
    given = (
        request.headers.get("X-Admin-Token")
        or request.form.get("admin_token")
        or (request.args.get("token") if request.method == "GET" else "")
        or ""
    )
    if not expected or not given:
        return False
    try:
        return hmac.compare_digest(
            given.encode("utf-8"), expected.encode("utf-8")
        )
    except (AttributeError, UnicodeEncodeError):
        return False


def _automation_settings() -> tuple[str, float, str]:
    """Webhook settings forwarded to the Spec 010 service (plan D3)."""
    return (
        current_app.config["AUTOMATION_WEBHOOK_URL"],
        current_app.config["AUTOMATION_TIMEOUT_SECONDS"],
        current_app.config["AUTOMATION_WEBHOOK_AUTH_HEADER"],
    )


def _render_admin(template: str, status: int = 200, **context):
    """Render an admin screen and apply the no-cache privacy headers (D2)."""
    response = current_app.make_response(
        render_template(template, view=get_home_view(), **context)
    )
    response.status_code = status
    response.headers["Cache-Control"] = "no-store"
    response.headers["Referrer-Policy"] = "no-referrer"
    return response


def _render_result(message: str, status: int = 200):
    return _render_admin(
        "admin/result.html",
        status,
        page_title=ADMIN_PAGE_TITLE,
        message=message,
        back_button=ADMIN_BACK_BUTTON,
    )


@bp.get("/citas/<int:cita_id>")
def detail(cita_id: int):
    """Summary plus both forms (RF-2); no operative forms when cancelled."""
    if not _check_token():
        return _render_result(ADMIN_ACCESS_DENIED, 403)

    appointment = get_appointment_by_id(cita_id, _database_path())
    if appointment is None:
        return _render_result(ADMIN_APPOINTMENT_NOT_FOUND, 404)

    is_cancelled = appointment.status == STATUS_CANCELLED
    return _render_admin(
        "admin/appointment_detail.html",
        page_title=ADMIN_PAGE_TITLE,
        appointment=appointment,
        service_name=str(SERVICES_CATALOG[appointment.service]["name"]),
        formatted_date=format_spanish_date(appointment.date),
        status_label=(
            STATUS_CANCELLED_LABEL if is_cancelled else STATUS_CONFIRMED_LABEL
        ),
        is_cancelled=is_cancelled,
        admin_token=current_app.config["CONSULTORIO_ADMIN_TOKEN"],
        services=SERVICES_CATALOG,
        booking_hours=BOOKING_HOURS,
        block_morning=BOOKING_BLOCK_MORNING,
        block_afternoon=BOOKING_BLOCK_AFTERNOON,
        cancel_title=ADMIN_CANCEL_TITLE,
        cancel_notice=ADMIN_CANCEL_NOTICE,
        cancel_button=ADMIN_CANCEL_BUTTON,
        reschedule_title=ADMIN_RESCHEDULE_TITLE,
        reschedule_notice=ADMIN_RESCHEDULE_NOTICE,
        reschedule_button=ADMIN_RESCHEDULE_BUTTON,
        label_patient=ADMIN_LABEL_PATIENT,
        label_service=ADMIN_LABEL_SERVICE,
        label_date=LABEL_DATE,
        label_new_date=ADMIN_LABEL_NEW_DATE,
        label_time=ADMIN_LABEL_TIME,
        label_status=ADMIN_LABEL_STATUS,
        summary_title=ADMIN_LABEL_SUMMARY,
    )


@bp.post("/citas/<int:cita_id>/cancelar")
def cancel(cita_id: int):
    """Delegate the cancellation to the Spec 010 service (RF-3, D3)."""
    if not _check_token():
        return _render_result(ADMIN_ACCESS_DENIED, 403)

    appointment = get_appointment_by_id(cita_id, _database_path())
    if appointment is None:
        return _render_result(ADMIN_APPOINTMENT_NOT_FOUND, 404)

    if appointment.status == STATUS_CANCELLED:
        # Conflict resolved without calling the service (D3).
        return _render_result(ADMIN_MSG_ALREADY_CANCELLED, 200)

    automation_url, automation_timeout, automation_auth_header = (
        _automation_settings()
    )
    result = cancel_appointment(
        cita_id,
        _database_path(),
        automation_url,
        automation_timeout,
        automation_auth_header,
    )

    if result == APPOINTMENT_NOT_FOUND:
        return _render_result(ADMIN_APPOINTMENT_NOT_FOUND, 404)
    if result == ALREADY_CANCELLED:
        return _render_result(ADMIN_MSG_ALREADY_CANCELLED, 200)
    return _render_result(ADMIN_CANCEL_SUCCESS, 200)
