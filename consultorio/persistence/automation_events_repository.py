"""Data access for automation events; no business rules live here (HU-007)."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from consultorio.persistence.database import get_connection


@dataclass(frozen=True)
class AutomationEvent:
    id: int
    event_id: str
    event_type: str
    event_version: int
    appointment_id: int
    status: str
    detail: str | None
    created_at: str
    sent_at: str | None


def _to_event(row: sqlite3.Row) -> AutomationEvent:
    return AutomationEvent(
        id=row["id"],
        event_id=row["event_id"],
        event_type=row["event_type"],
        event_version=row["event_version"],
        appointment_id=row["appointment_id"],
        status=row["status"],
        detail=row["detail"],
        created_at=row["created_at"],
        sent_at=row["sent_at"],
    )


def insert_event(
    event_id: str,
    event_type: str,
    event_version: int,
    appointment_id: int,
    database_path: str | Path,
) -> bool:
    """Register a pending event; False when event_id already exists (RF-5)."""
    try:
        with get_connection(database_path) as connection:
            connection.execute(
                """
                INSERT INTO automation_events (
                    event_id, event_type, event_version, appointment_id, status
                ) VALUES (?, ?, ?, ?, 'pending')
                """,
                (event_id, event_type, event_version, appointment_id),
            )
    except sqlite3.IntegrityError:
        return False
    return True


def get_by_event_id(
    event_id: str, database_path: str | Path
) -> AutomationEvent | None:
    with get_connection(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM automation_events WHERE event_id = ?", (event_id,)
        ).fetchone()
    return _to_event(row) if row is not None else None


def mark_sent(event_id: str, database_path: str | Path) -> None:
    with get_connection(database_path) as connection:
        connection.execute(
            """
            UPDATE automation_events
            SET status = 'sent', detail = NULL,
                sent_at = datetime('now', 'localtime')
            WHERE event_id = ?
            """,
            (event_id,),
        )


def mark_skipped(
    event_id: str, detail: str, database_path: str | Path
) -> None:
    with get_connection(database_path) as connection:
        connection.execute(
            """
            UPDATE automation_events SET status = 'skipped', detail = ?
            WHERE event_id = ?
            """,
            (detail, event_id),
        )


def mark_failed(
    event_id: str, detail: str, database_path: str | Path
) -> None:
    with get_connection(database_path) as connection:
        connection.execute(
            """
            UPDATE automation_events SET status = 'failed', detail = ?
            WHERE event_id = ?
            """,
            (detail, event_id),
        )


def claim_failed_event(
    event_id: str,
    database_path: str | Path,
    permanent_pattern: str | None = None,
    retryable_pattern: str | None = None,
) -> bool:
    """
    Atomically move an event from 'failed' to 'pending' for reprocessing.
    Only applies to 'appointment.cancelled' events.
    Returns True if the event was claimed, False otherwise.

    D-010-01 (DP-02): when both `LIKE` patterns are supplied, a `failed` event
    whose persisted `detail` is a PERMANENT HTTP rejection (4xx except 429) is
    excluded inside this same atomic `UPDATE` (no prior `SELECT`). The patterns
    are derived from the content literal and passed by the service, so the
    retryability policy does not live in the persistence layer. 5xx, 429,
    timeout, `URLError` and `NULL` details stay claimable. Omitting the patterns
    keeps the previous behaviour (claim any `failed` event).
    """
    query = """
        UPDATE automation_events
        SET status = 'pending', detail = NULL
        WHERE event_id = ?
          AND status = 'failed'
          AND event_type = 'appointment.cancelled'
    """
    params: list[object] = [event_id]
    if permanent_pattern is not None and retryable_pattern is not None:
        query += """
          AND (
            detail IS NULL
            OR detail NOT LIKE ?
            OR detail LIKE ?
          )
        """
        params.extend([permanent_pattern, retryable_pattern])

    with get_connection(database_path) as connection:
        cursor = connection.execute(query, tuple(params))
        return cursor.rowcount == 1
