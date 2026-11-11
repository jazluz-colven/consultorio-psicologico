"""SQLite rollback verification (Spec 019, plan D9/D10; relocated TC-010-014).

This test is deliberately NOT part of the PostgreSQL parity suite (RF-28). It
exercises the temporary SQLite rollback route: migration of the legacy
``appointments`` schema (inline ``UNIQUE (service, date, time)``) to the partial
unique index ``ux_appointments_slot_open`` with backup, data preservation,
idempotency and abort on active duplicates.

Execution and recording as a rollback check belong to T15
(``docs/evidencias/hu-019/rollback.md``); the PostgreSQL parity evidence is
``docs/evidencias/hu-019/suite-postgres.txt``.
"""

import sqlite3
from pathlib import Path

import pytest

from consultorio.persistence.database import (
    PARTIAL_INDEX_NAME,
    get_connection,
    init_db,
)

LEGACY_SCHEMA = """
CREATE TABLE appointments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type   TEXT NOT NULL,
    document_number TEXT NOT NULL UNIQUE,
    patient_name    TEXT NOT NULL,
    email           TEXT NOT NULL,
    phone           TEXT NOT NULL,
    service         TEXT NOT NULL,
    date            TEXT NOT NULL,
    time            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'confirmed',
    created_at      TEXT NOT NULL DEFAULT (datetime('now', 'localtime')),
    UNIQUE (service, date, time)
)
"""

LEGACY_SCHEMA_WITH_DUPLICATES = """
CREATE TABLE appointments (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    document_type   TEXT NOT NULL,
    document_number TEXT NOT NULL UNIQUE,
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

ROW_NUTRITION = (
    "CC",
    "111111111",
    "Ana Pérez",
    "ana@correo.com",
    "3001111111",
    "nutrition",
    "2026-11-02",
    "08:00",
    "confirmed",
)
ROW_PSYCHOLOGY = (
    "CC",
    "222222222",
    "Luis Gómez",
    "luis@correo.com",
    "3002222222",
    "psychology_integral",
    "2026-11-02",
    "10:00",
    "confirmed",
)
ROW_CANCELLED = (
    "CC",
    "333333333",
    "María Ruiz",
    "maria@correo.com",
    "3003333333",
    "nutrition",
    "2026-11-03",
    "09:00",
    "cancelled",
)
DUPLICATE_ACTIVE = (
    "CC",
    "444444444",
    "Pedro Días",
    "pedro@correo.com",
    "3004444444",
    "nutrition",
    "2026-11-02",
    "08:00",
    "confirmed",
)


def _create_legacy_db(path: Path, schema: str, rows: list[tuple]) -> None:
    connection = sqlite3.connect(str(path))
    try:
        connection.execute(schema)
        connection.executemany(
            """
            INSERT INTO appointments (
                document_type, document_number, patient_name, email, phone,
                service, date, time, status
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        connection.commit()
    finally:
        connection.close()


def test_tc_010_014_migracion_indice_parcial_respaldo_idempotente_y_aborto(
    tmp_path,
) -> None:
    path = tmp_path / "legacy.db"
    _create_legacy_db(
        path, LEGACY_SCHEMA, [ROW_NUTRITION, ROW_PSYCHOLOGY, ROW_CANCELLED]
    )

    init_db(path)

    with get_connection(path) as connection:
        table_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table'"
            " AND name = 'appointments'"
        ).fetchone()["sql"]
        assert "UNIQUE" not in table_sql.upper()
        index = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'index' AND name = ?",
            (PARTIAL_INDEX_NAME,),
        ).fetchone()
        assert index is not None
        assert "status <> 'cancelled'" in index["sql"]
        rows = connection.execute(
            "SELECT id, service, time, status FROM appointments ORDER BY id"
        ).fetchall()
    assert [(row["id"], row["service"], row["time"], row["status"]) for row in rows] == [
        (1, "nutrition", "08:00", "confirmed"),
        (2, "psychology_integral", "10:00", "confirmed"),
        (3, "nutrition", "09:00", "cancelled"),
    ]
    backups = list(tmp_path.glob("legacy.db.bak-*"))
    assert len(backups) == 1

    # Second run: the partial index already exists → no-op, no extra backup.
    init_db(path)
    assert len(list(tmp_path.glob("legacy.db.bak-*"))) == 1
    with get_connection(path) as connection:
        total = connection.execute(
            "SELECT COUNT(*) AS total FROM appointments"
        ).fetchone()["total"]
    assert total == 3

    # Abort: active duplicates among non-cancelled rows must fail loudly and
    # leave the legacy data untouched (constitución #5).
    dup_path = tmp_path / "dup.db"
    _create_legacy_db(
        dup_path, LEGACY_SCHEMA_WITH_DUPLICATES, [ROW_NUTRITION, DUPLICATE_ACTIVE]
    )
    with pytest.raises(RuntimeError, match="migration aborted"):
        init_db(dup_path)
    with get_connection(dup_path) as connection:
        table_sql = connection.execute(
            "SELECT sql FROM sqlite_master WHERE type = 'table'"
            " AND name = 'appointments'"
        ).fetchone()["sql"]
        total = connection.execute(
            "SELECT COUNT(*) AS total FROM appointments"
        ).fetchone()["total"]
    assert total == 2
    assert "UNIQUE" in table_sql.upper()
