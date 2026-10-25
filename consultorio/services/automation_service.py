"""Post-booking automation events dispatched to n8n (HU-007).

The automation layer never raises: the booking is already valid when this
module runs (RF-2, RF-4, RF-7). Payload allowlist carries no personal data
(RF-3, minimization).
"""

import json
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path

from consultorio.content.automation_content import (
    CANCELLED_EVENT_TYPE,
    CANCELLED_EVENT_VERSION,
    DETAIL_INVALID_RESPONSE_TEMPLATE,
    DETAIL_NOT_CONFIGURED,
    DETAIL_TIMEOUT,
    DETAIL_UNAVAILABLE,
    DETAIL_UNEXPECTED,
    EVENT_TYPE,
    EVENT_VERSION,
)
from consultorio.persistence import automation_events_repository as events_repository
from consultorio.persistence.appointments_repository import Appointment


def _build_automation_event(
    appointment: Appointment,
    event_type: str,
    event_version: int,
) -> dict[str, object]:
    """Shared payload allowlist of the business events; no personal data (RF-9)."""
    return {
        "event_id": f"{event_type}:{appointment.id}:v{event_version}",
        "event_type": event_type,
        "event_version": event_version,
        "occurred_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "appointment": {
            "id": appointment.id,
            "service": appointment.service,
            "date": appointment.date,
            "time": appointment.time,
            "status": appointment.status,
        },
    }


def build_event(appointment: Appointment) -> dict[str, object]:
    """Contract payload of the spec: allowlist of fields, no personal data."""
    return _build_automation_event(appointment, EVENT_TYPE, EVENT_VERSION)


def build_cancelled_event(appointment: Appointment) -> dict[str, object]:
    """Contract payload of `appointment.cancelled` (spec 010 RF-9, no PII)."""
    return _build_automation_event(
        appointment, CANCELLED_EVENT_TYPE, CANCELLED_EVENT_VERSION
    )


def on_appointment_confirmed(
    appointment: Appointment,
    database_path: str | Path,
    webhook_url: str = "",
    timeout_seconds: float = 3.0,
    auth_header: str = "",
) -> None:
    """Register the event and best-effort dispatch it; never raises (RF-2/RF-4/RF-7)."""
    try:
        event = build_event(appointment)
        event_id = str(event["event_id"])
        created = events_repository.insert_event(
            event_id,
            str(event["event_type"]),
            int(event["event_version"]),  # type: ignore[arg-type]
            appointment.id,
            database_path,
        )
        if not created:
            # same reservation processed again: no duplicate automations (RF-5)
            return
        if not webhook_url:
            events_repository.mark_skipped(
                event_id, DETAIL_NOT_CONFIGURED, database_path
            )
            return
        try:
            status_code = _post_webhook(
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
        # a registration failure must never invalidate the booking (RF-2/RF-4/RF-7)
        return


def publish_cancelled_event(
    appointment: Appointment,
    database_path: str | Path,
    url: str = "",
    timeout: float = 3.0,
    auth: str = "",
) -> None:
    """Publish `appointment.cancelled` AFTER the cancellation commit (RF-8/RF-10).
    
    Publication only: the `pending` row already exists — it was registered
    inside the SAME transaction that cancelled the appointment (RF-11,
    `update_appointment_status_with_pending_event`). Empty URL marks the event
    `skipped`; the POST outcome marks it `sent`/`failed` with the existing
    Spanish DETAIL_* reasons. Never raises: the cancellation is already
    committed when this runs, so a publication failure can neither revert nor
    block it (RF-10).
    """
    try:
        event = build_cancelled_event(appointment)
        event_id = str(event["event_id"])
        if not url:
            events_repository.mark_skipped(
                event_id, DETAIL_NOT_CONFIGURED, database_path
            )
            return
        try:
            status_code = _post_webhook(url, event, timeout, auth)
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
        # a publication failure must never affect the cancellation (RF-10)
        return


def reprocess_automation_event(
    event_id: str,
    database_path: str | Path,
    url: str = "",
    timeout: float = 3.0,
    auth: str = "",
) -> None:
    """
    Reprocess a failed business event by attempting publication again (RF-13, RF-14, RF-15).
    
    Admission is atomic via `claim_failed_event`. If not admitted (not failed, 
    wrong type, or concurrent claim), it's a no-op.
    """
    try:
        if not events_repository.claim_failed_event(event_id, database_path):
            return

        event_record = events_repository.get_by_event_id(event_id, database_path)
        if not event_record:
            return

        # Retrieve the associated appointment to rebuild the payload
        from consultorio.persistence import appointments_repository
        appointment = appointments_repository.get_appointment_by_id(
            event_record.appointment_id, database_path
        )
        if not appointment:
            events_repository.mark_failed(
                event_id, "Cita asociada no encontrada.", database_path
            )
            return

        # Rebuild payload with the same deterministic ID
        event = build_cancelled_event(appointment)
        
        if not url:
            events_repository.mark_skipped(
                event_id, DETAIL_NOT_CONFIGURED, database_path
            )
            return

        try:
            status_code = _post_webhook(url, event, timeout, auth)
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
        # Best-effort: never propagate exceptions during reprocessing
        return



def _post_webhook(
    url: str,
    payload: dict[str, object],
    timeout_seconds: float,
    auth_header: str = "",
) -> int:
    """POST JSON with the stdlib only (constitution #1); returns the HTTP status.

    `auth_header` (enmienda 2, Q7/D14) is a "Name: value" pair sent as-is;
    empty means no extra header. The value is an environment secret.
    """
    headers = {"Content-Type": "application/json"}
    name, separator, value = auth_header.partition(": ")
    if separator and name:
        headers[name] = value.strip()
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers=headers,
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return int(response.status)
