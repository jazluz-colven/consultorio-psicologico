"""SQLite connection and schema for the first persistence layer (HU-004)."""

import shutil
import sqlite3
from datetime import datetime
from pathlib import Path

# HU-010 (spec 010 amended 2026-10-13): the inline UNIQUE (service, date, time)
# is replaced by a partial unique index that ignores cancelled appointments, so
# a cancelled slot can be booked again while live slots stay unique (RF-4).
SCHEMA = """
CREATE TABLE IF NOT EXISTS appointments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type   TEXT NOT NULL,
    document_number TEXT NOT NULL,
    patient_name    TEXT NOT NULL,
    email           TEXT NOT NULL,
    phone           TEXT NOT NULL,
    service         TEXT NOT NULL,
    date            TEXT NOT NULL,
    time            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'confirmed',
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
);

CREATE TABLE IF NOT EXISTS automation_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        TEXT NOT NULL UNIQUE,
    event_type      TEXT NOT NULL,
    event_version   INTEGER NOT NULL,
    appointment_id  INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    detail          TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    sent_at         TEXT
);
"""

APPOINTMENTS_TABLE_SQL = """
CREATE TABLE appointments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type   TEXT NOT NULL,
    document_number TEXT NOT NULL,
    patient_name    TEXT NOT NULL,
    email           TEXT NOT NULL,
    phone           TEXT NOT NULL,
    service         TEXT NOT NULL,
    date            TEXT NOT NULL,
    time            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'confirmed',
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime'))
)
"""

PARTIAL_INDEX_NAME = "ux_appointments_slot_open"
_PARTIAL_INDEX_SQL = (
    f"CREATE UNIQUE INDEX IF NOT EXISTS {PARTIAL_INDEX_NAME} "
    "ON appointments(service, date, time) WHERE status <> 'cancelled'"
)


def get_connection(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    return connection


def init_db(database_path: str | Path) -> None:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(path) as connection:
        connection.executescript(SCHEMA)
        _migrate_appointment_uniqueness(connection, path)


def _migrate_appointment_uniqueness(
    connection: sqlite3.Connection, path: Path
) -> None:
    """One-time migration: inline UNIQUE -> partial unique index (spec 010).

    Backs the database file up before touching anything, keeps all rows, is
    idempotent (no-op once the partial index exists) and aborts loudly if
    duplicates among non-cancelled appointments were ever found.
    """
    existing = connection.execute(
        "SELECT 1 FROM sqlite_master WHERE type = 'index' AND name = ?",
        (PARTIAL_INDEX_NAME,),
    ).fetchone()
    if existing is not None:
        return
    table_row = connection.execute(
        "SELECT sql FROM sqlite_master WHERE type = 'table' AND name = 'appointments'"
    ).fetchone()
    table_sql = ((table_row["sql"] if table_row is not None else "") or "")
    if "UNIQUE" not in table_sql.upper():
        # Fresh schema (or already rebuilt table): only ensure the index.
        connection.execute(_PARTIAL_INDEX_SQL)
        return
    backup = path.with_name(
        path.name + ".bak-" + datetime.now().strftime("%Y%m%d%H%M%S")
    )
    shutil.copy2(path, backup)
    duplicates = connection.execute(
        """
        SELECT service, date, time FROM appointments
        WHERE status <> 'cancelled'
        GROUP BY service, date, time HAVING COUNT(*) > 1
        """
    ).fetchall()
    if duplicates:
        raise RuntimeError(
            "appointments migration aborted: duplicate active slots found."
        )
    # Manual transaction: rollback on any failure below (constitución #5).
    connection.execute("BEGIN")
    connection.execute("ALTER TABLE appointments RENAME TO appointments_legacy")
    connection.execute(APPOINTMENTS_TABLE_SQL)
    connection.execute(
        """
        INSERT INTO appointments (
            id, document_type, document_number, patient_name, email, phone,
            service, date, time, status, created_at
        )
        SELECT id, document_type, document_number, patient_name, email, phone,
               service, date, time, status, created_at
        FROM appointments_legacy
        """
    )
    connection.execute("DROP TABLE appointments_legacy")
    connection.execute(_PARTIAL_INDEX_SQL)
    connection.execute("COMMIT")
