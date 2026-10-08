"""Data access for appointments; no business rules live here."""

import sqlite3
from dataclasses import dataclass
from pathlib import Path

from consultorio.persistence.database import get_connection


@dataclass(frozen=True)
class Appointment:
    id: int
    document_type: str
    document_number: str
    patient_name: str
    email: str
    phone: str
    service: str
    date: str
    time: str
    status: str
    created_at: str


def _to_appointment(row: sqlite3.Row) -> Appointment:
    return Appointment(
        id=row["id"],
        document_type=row["document_type"],
        document_number=row["document_number"],
        patient_name=row["patient_name"],
        email=row["email"],
        phone=row["phone"],
        service=row["service"],
        date=row["date"],
        time=row["time"],
        status=row["status"],
        created_at=row["created_at"],
    )


def insert_appointment(data: dict[str, str], database_path: str | Path) -> Appointment:
    with get_connection(database_path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO appointments (
                document_type, document_number, patient_name, email, phone,
                service, date, time, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'pending')
            """,
            (
                data["document_type"],
                data["document_number"],
                data["patient_name"],
                data["email"],
                data["phone"],
                data["service"],
                data["date"],
                data["time"],
            ),
        )
        appointment_id = cursor.lastrowid
    created = get_appointment_by_id(appointment_id, database_path)
    if created is None:  # pragma: no cover - defensive
        raise RuntimeError("Appointment inserted but not found.")
    return created


def get_appointment_by_id(
    appointment_id: int, database_path: str | Path
) -> Appointment | None:
    with get_connection(database_path) as connection:
        row = connection.execute(
            "SELECT * FROM appointments WHERE id = ?", (appointment_id,)
        ).fetchone()
    return _to_appointment(row) if row is not None else None


def is_slot_taken(
    service: str, date: str, time: str, database_path: str | Path
) -> bool:
    with get_connection(database_path) as connection:
        row = connection.execute(
            """
            SELECT 1 FROM appointments
            WHERE service = ? AND date = ? AND time = ?
            """,
            (service, date, time),
        ).fetchone()
    return row is not None


def list_booked_times(
    service: str, date: str, database_path: str | Path
) -> list[str]:
    with get_connection(database_path) as connection:
        rows = connection.execute(
            """
            SELECT time FROM appointments
            WHERE service = ? AND date = ?
            ORDER BY time
            """,
            (service, date),
        ).fetchall()
    return [row["time"] for row in rows]
