"""Patient cancellation routes (HU-017, spec 017).

T5 scope: the verification form and the read-only summary (RF-1..RF-4).
The execution step (confirmation and success) belongs to T6.

Plan decisions applied here:

- **D2**: ``GET/POST /citas/cancelar/<int:cita_id>``. The ``<int>`` converter
  answers 404 for a non-numeric reference (D4, Q-E).
- **D4**: the GET always renders the same form with 200, whether the
  appointment exists or not; ``FAILED`` renders one single literal with no
  appointment data at all.
- **D5**: every visible text comes from ``cancellation_content`` (or the
  Spec 004 document literals); no copy lives in this module.
- **D11/D12**: the summary uses ``format_spanish_date()`` and shows only
  service, date, time, status and reference.
"""

import re
from pathlib import Path

from flask import Blueprint, current_app, render_template, request

from consultorio.content.appointment_content import (
    MSG_INVALID_DOC_NUMBER,
    MSG_REQUIRED_DOC_NUMBER,
    STATUS_CONFIRMED_LABEL,
)
from consultorio.content.cancellation_content import (
    CANCEL_BACK_BUTTON,
    CANCEL_BUTTON_LABEL,
    CANCEL_CONFIRM_BUTTON,
    CANCEL_NOTICE,
    CANCEL_PAGE_TITLE,
    LABEL_DATE,
    LABEL_DOCUMENT_NUMBER,
    LABEL_REFERENCE,
    LABEL_SERVICE,
    LABEL_STATUS,
    LABEL_TIME,
    MSG_ALREADY_CANCELLED,
    MSG_NOTICE_PERIOD,
    MSG_VERIFICATION_FAILED,
)
from consultorio.content.services_catalog import SERVICES_CATALOG
from consultorio.persistence.appointments_repository import Appointment
from consultorio.services.cancellation_flow_service import (
    ALREADY_CANCELLED,
    FAILED,
    TOO_SOON,
    verify_cancellation_request,
)
from consultorio.services.email_service import format_spanish_date
from consultorio.services.home_service import get_home_view

bp = Blueprint("cancellation", __name__)

# Same format rule as the booking form (Spec 004: 4 to 20 digits). Empty and
# malformed values reuse that spec's contractual literals (plan D5).
_DOCUMENT_NUMBER_RE = re.compile(r"^[0-9]{4,20}$")


def _database_path() -> Path:
    return Path(current_app.config["DATABASE_PATH"])


def _render_verify(cita_id: int, message: str | None = None):
    """Verification form; identical 200 response whether the row exists or not."""
    return (
        render_template(
            "cancellation/verify.html",
            view=get_home_view(),
            page_title=CANCEL_PAGE_TITLE,
            notice=CANCEL_NOTICE,
            label_reference=LABEL_REFERENCE,
            label_document_number=LABEL_DOCUMENT_NUMBER,
            button_label=CANCEL_BUTTON_LABEL,
            cita_id=cita_id,
            message=message,
        ),
        200,
    )


@bp.get("/citas/cancelar/<int:cita_id>")
def verify(cita_id: int):
    return _render_verify(cita_id)


@bp.post("/citas/cancelar/<int:cita_id>")
def verify_submit(cita_id: int):
    document = request.form.get("document_number", "").strip()
    if not document:
        return _render_verify(cita_id, MSG_REQUIRED_DOC_NUMBER)
    if not _DOCUMENT_NUMBER_RE.fullmatch(document):
        return _render_verify(cita_id, MSG_INVALID_DOC_NUMBER)

    result = verify_cancellation_request(cita_id, document, _database_path())
    if result == FAILED:
        return _render_verify(cita_id, MSG_VERIFICATION_FAILED)
    if result == ALREADY_CANCELLED:
        return _render_verify(cita_id, MSG_ALREADY_CANCELLED)
    if result == TOO_SOON:
        return _render_verify(cita_id, MSG_NOTICE_PERIOD)

    assert isinstance(result, Appointment)
    service_name = str(SERVICES_CATALOG[result.service]["name"])
    return (
        render_template(
            "cancellation/summary.html",
            view=get_home_view(),
            page_title=CANCEL_PAGE_TITLE,
            label_reference=LABEL_REFERENCE,
            label_service=LABEL_SERVICE,
            label_date=LABEL_DATE,
            label_time=LABEL_TIME,
            label_status=LABEL_STATUS,
            confirm_button=CANCEL_CONFIRM_BUTTON,
            back_button=CANCEL_BACK_BUTTON,
            cita_id=result.id,
            service_name=service_name,
            formatted_date=format_spanish_date(result.date),
            appointment_time=result.time,
            status_label=STATUS_CONFIRMED_LABEL,
            document_number=document,
        ),
        200,
    )
