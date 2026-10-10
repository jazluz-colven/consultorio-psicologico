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


def build_event(appointment: Appointment) -> dict[str, object]:
    """Contract payload of the spec: allowlist of fields, no personal data."""
    return {
        "event_id": f"{EVENT_TYPE}:{appointment.id}:v{EVENT_VERSION}",
        "event_type": EVENT_TYPE,
        "event_version": EVENT_VERSION,
        "occurred_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "appointment": {
            "id": appointment.id,
            "service": appointment.service,
            "date": appointment.date,
            "time": appointment.time,
            "status": appointment.status,
        },
    }


def on_appointment_confirmed(
    appointment: Appointment,
    database_path: str | Path,
    webhook_url: str = "",
    timeout_seconds: float = 3.0,
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
            status_code = _post_webhook(webhook_url, event, timeout_seconds)
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


def _post_webhook(
    url: str, payload: dict[str, object], timeout_seconds: float
) -> int:
    """POST JSON with the stdlib only (constitution #1); returns the HTTP status."""
    request = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout_seconds) as response:
        return int(response.status)
