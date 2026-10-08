"""SQLite connection and schema for the first persistence layer (HU-004)."""

import sqlite3
from pathlib import Path

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
    status          TEXT NOT NULL DEFAULT 'pending',
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE (service, date, time)
);
"""


def get_connection(database_path: str | Path) -> sqlite3.Connection:
    connection = sqlite3.connect(str(database_path))
    connection.row_factory = sqlite3.Row
    return connection


def init_db(database_path: str | Path) -> None:
    path = Path(database_path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with get_connection(path) as connection:
        connection.executescript(SCHEMA)
