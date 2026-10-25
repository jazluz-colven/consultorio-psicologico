"""Patient cancellation flow: ownership verification and the 3-hour window.

Read-only step of the HU-017 flow (spec 017 RF-1, RF-2, RF-4; plan D1, D3,
D4 and D6). It performs **no** state transition and sends **no** notification:
execution delegates to ``appointment_service.cancel_appointment()`` (Spec 010)
— plan D7, task T3.

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
from consultorio.services.appointment_service import ALREADY_CANCELLED

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
