"""Patient cancellation flow: ownership verification and the 3-hour window.

Steps of the HU-017 flow (spec 017 RF-1, RF-2, RF-4, RF-5, RF-8, RF-9;
plan D1, D3, D4, D6 and D7):

1. ``verify_cancellation_request()`` — read-only: it performs **no** state
   change and sends **no** notification.
2. ``cancel_verified_request()`` — re-verifies and then **delegates** the
   execution to ``appointment_service.cancel_appointment()`` (Spec 010); this
   module contains no transition, no persistence statement and no
   notification of its own (RF-5, constitution #3).

Result values (plan §5):

- ``FAILED`` — the reference does not exist **or** the document number does
  not match. One single, indistinguishable result, so neither case can be
  told apart from the answer (RF-2, D4).
- ``ALREADY_CANCELLED`` — the appointment is already cancelled (RF-9).
- ``TOO_SOON`` — the appointment starts in less than 3 hours, has already
  started or has already passed (RF-4, D6).
- READY — a successful verification returns the ``Appointment`` itself, the
  same ``Appointment | str`` pattern used by ``create_booking()`` and
  ``cancel_appointment()``; the web layer renders the summary from it (RF-3).
  After execution, that same ``Appointment`` is the SUCCESS result (D7).

Check order (plan §5): ``FAILED`` → ``ALREADY_CANCELLED`` → ``TOO_SOON`` →
READY. Ownership is always checked first so no state (cancelled, notice
period) is disclosed before the document matches (D4); the already-cancelled
state is evaluated **before** the window because the 3-hour restriction only
applies to appointments that can still be cancelled — a cancelled appointment
must keep answering «Esta cita ya fue cancelada.» on retries (RF-9), even if
its start time has already passed.

The document number is compared exactly after ``strip()`` (D3); the type of
document is not part of the identification. Empty or malformed values are
validated by the web layer (task T5, Spec 004 literals), not here.
"""

from datetime import date, datetime, time, timedelta
from pathlib import Path

from consultorio.content.appointment_content import STATUS_CANCELLED
from consultorio.persistence import appointments_repository as repository
from consultorio.persistence.appointments_repository import Appointment
from consultorio.services.appointment_service import (
    ALREADY_CANCELLED,
    cancel_appointment,
)

FAILED: str = "failed"
TOO_SOON: str = "too_soon"

# Minimum advance to cancel from the site; the exact boundary is allowed
# (spec 017 Q2: «3 h exactas → permitido»).
NOTICE_PERIOD: timedelta = timedelta(hours=3)


def verify_cancellation_request(
    appointment_id: int,
    document: str,
    database_path: str | Path,
    now: datetime | None = None,
) -> Appointment | str:
    """Verify that the appointment belongs to the requester and may be
    cancelled now (RF-1, RF-2, RF-4). Read-only: nothing is written.

    Args:
        appointment_id: reference of the appointment (URL identifier).
        document: document number typed by the patient; compared exactly
            against ``document_number`` after ``strip()`` (D3).
        database_path: SQLite database used by the persistence layer.
        now: explicit reference time; defaults to ``datetime.now()`` (local,
            naive — same base as ``date.today()`` used by the booking rules).
            Passing it makes the 3-hour boundary deterministic in tests (D6).

    Returns:
        The verified :class:`Appointment` (READY), or one of the sentinels
        ``FAILED`` / ``ALREADY_CANCELLED`` / ``TOO_SOON``. ``FAILED`` carries
        no appointment data at all (D4).
    """
    appointment = repository.get_appointment_by_id(appointment_id, database_path)
    if appointment is None:
        return FAILED
    if document.strip() != appointment.document_number:
        return FAILED
    if appointment.status == STATUS_CANCELLED:
        return ALREADY_CANCELLED

    reference = now if now is not None else datetime.now()
    start = datetime.combine(
        date.fromisoformat(appointment.date),
        time.fromisoformat(appointment.time),
    )
    if start - reference < NOTICE_PERIOD:
        # started or already past included: their difference is negative (D6)
        return TOO_SOON
    return appointment


def cancel_verified_request(
    appointment_id: int,
    document: str,
    database_path: str | Path,
    now: datetime | None = None,
    automation_url: str = "",
    automation_timeout: float = 3.0,
    automation_auth_header: str = "",
) -> Appointment | str:
    """Execute a cancellation once the identity and the window are verified
    (RF-5, RF-8, RF-9; plan D7, task T3).

    It re-runs the read-only verification first (ownership + 3-hour window,
    because time passes between the summary screen and the confirmation:
    plan §1 rule 3). Any result other than READY is returned untouched and
    nothing is written. When the request is READY the execution **delegates**
    to :func:`appointment_service.cancel_appointment` (Spec 010): the state
    transition, the slot release and the notifications are guarantees of that
    service, never of this module (RF-5, constitution #3).

    Result mapping (plan D7):

    =========================  ==========================================
    Delegated result           Returned result
    =========================  ==========================================
    ``Appointment``            the same ``Appointment`` (SUCCESS)
    ``ALREADY_CANCELLED``      ``ALREADY_CANCELLED``
    ``APPOINTMENT_NOT_FOUND``  ``FAILED``
    =========================  ==========================================

    Verification results are passed through as they are: ``FAILED``,
    ``ALREADY_CANCELLED`` or ``TOO_SOON``. A retry over an already cancelled
    appointment therefore answers ``ALREADY_CANCELLED`` without a second
    transition and without a second notification (RF-9), because the
    delegated service itself is idempotent (Spec 010).

    Args:
        appointment_id: reference of the appointment (URL identifier).
        document: document number typed by the patient (D3, compared after
            ``strip()``).
        database_path: SQLite database used by the persistence layer.
        now: explicit reference time for the 3-hour window (D6); defaults to
            ``datetime.now()``.
        automation_url: webhook configuration forwarded to the delegated
            service (same three settings the booking route already passes).
        automation_timeout: timeout in seconds for the delegated service.
        automation_auth_header: optional authorization header forwarded to
            the delegated service.

    Returns:
        The updated :class:`Appointment` (SUCCESS) or one of the sentinels
        ``ALREADY_CANCELLED`` / ``FAILED`` / ``TOO_SOON``.
    """
    verification = verify_cancellation_request(
        appointment_id, document, database_path, now
    )
    if not isinstance(verification, Appointment):
        # FAILED / ALREADY_CANCELLED / TOO_SOON: stop before any write (RF-1)
        return verification

    result = cancel_appointment(
        appointment_id,
        database_path,
        automation_url,
        automation_timeout,
        automation_auth_header,
    )
    if isinstance(result, Appointment):
        return result  # SUCCESS: the appointment itself, already updated
    if result == ALREADY_CANCELLED:
        return ALREADY_CANCELLED
    # APPOINTMENT_NOT_FOUND —and any unexpected sentinel— maps to FAILED (D7)
    return FAILED
