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

from consultorio import DATABASE_EXTENSION_KEY, create_app
from consultorio.config import TestConfig
from consultorio.persistence import appointments_repository as appointments
from consultorio.persistence.database import (
    PARTIAL_INDEX_NAME,
    Database,
    DatabaseTarget,
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


# ---------------------------------------------------------------------------
# TC-019-021 - temporary SQLite rollback (Spec 019, plan D10, RF-18/RF-19)
#
# This is a rollback verification, not PostgreSQL parity evidence (RF-28):
# the switch makes one store visible at a time and no rows are transferred
# between engines. The row loss after the cut is accepted by the user and the
# operational procedure (manual Neon snapshot + cut time) is documented in
# docs/operaciones/postgresql.md and docs/evidencias/hu-019/rollback.md.
# ---------------------------------------------------------------------------

PG_ORIGINAL_ROW = {
    "document_type": "CC",
    "document_number": "900000001",
    "patient_name": "Paciente PostgreSQL",
    "email": "pg.rollback@example.invalid",
    "phone": "3000000001",
    "service": "nutrition",
    "date": "2026-11-20",
    "time": "08:00",
}

ROLLBACK_ONLY_ROW = {
    "document_type": "CC",
    "document_number": "900000002",
    "patient_name": "Paciente Rollback",
    "email": "sqlite.rollback@example.invalid",
    "phone": "3000000002",
    "service": "psychology_integral",
    "date": "2026-11-20",
    "time": "10:00",
}

APP_ROLLBACK_ROW = {
    "document_type": "CC",
    "document_number": "900000003",
    "patient_name": "Paciente Arranque Rollback",
    "email": "app.rollback@example.invalid",
    "phone": "3000000003",
    "service": "nutrition",
    "date": "2026-11-21",
    "time": "09:00",
}


def _count_appointments(database: Database) -> int:
    with database.connection() as connection:
        row = connection.execute(
            "SELECT count(*) AS total FROM appointments"
        ).fetchone()
    return int(row["total"])


def test_tc_019_021_rollback_switch_isolates_stores_and_postgres_data_survives(
    pg_target: DatabaseTarget, tmp_path: Path
) -> None:
    """Switching to SQLite hides PostgreSQL rows and never copies them back.

    Sequence of the rollback drill (D10):

    1. create an appointment in the isolated PostgreSQL schema;
    2. switch ``PERSISTENCE_BACKEND`` to ``sqlite`` with a temporary
       ``DATABASE_PATH`` and check the PostgreSQL row is not visible;
    3. create an appointment while rolled back;
    4. return to PostgreSQL: the SQLite-only row is not transferred and the
       original PostgreSQL appointment is intact;
    5. start the app with the rollback configuration without ``DATABASE_URL``.
    """
    # 1. PostgreSQL (isolated ``test_hu019_<uuid>`` schema, never ``public``).
    pg_database = Database(pg_target)
    pg_database.ensure_schema()
    original = appointments.insert_appointment(PG_ORIGINAL_ROW, pg_database)
    assert original.id >= 1
    assert _count_appointments(pg_database) == 1

    # 2. The environment switch is equivalent to ``PERSISTENCE_BACKEND=sqlite``
    # plus ``DATABASE_PATH``; no code changes are needed.
    rollback_path = tmp_path / "rollback.db"
    rollback_target = DatabaseTarget.from_config(
        {
            "PERSISTENCE_BACKEND": "sqlite",
            "DATABASE_PATH": rollback_path,
            "DATABASE_URL": "",
        }
    )
    assert rollback_target.backend == "sqlite"
    assert rollback_target.dsn is None
    assert rollback_target.sqlite_path == rollback_path

    rolled_back = Database(rollback_target)
    rolled_back.ensure_schema()
    assert _count_appointments(rolled_back) == 0
    assert (
        appointments.get_appointment_by_id(original.id, rolled_back) is None
    )
    assert (
        appointments.is_slot_taken(
            original.service,
            original.date,
            original.time,
            rolled_back,
        )
        is False
    )

    # 3. A new appointment during the rollback lives only in SQLite.
    rollback_only = appointments.insert_appointment(
        ROLLBACK_ONLY_ROW, rolled_back
    )
    assert rollback_only.id >= 1
    assert (
        appointments.get_appointment_by_id(rollback_only.id, rolled_back)
        == rollback_only
    )
    assert _count_appointments(rolled_back) == 1

    # 4. Back to PostgreSQL: the original row is intact, the SQLite-only row
    # was not transferred and its slot is still free.
    assert (
        appointments.get_appointment_by_id(original.id, pg_database)
        == original
    )
    assert _count_appointments(pg_database) == 1
    with pg_database.connection() as connection:
        transferred = connection.execute(
            "SELECT count(*) AS total FROM appointments"
            " WHERE document_number = %s",
            (ROLLBACK_ONLY_ROW["document_number"],),
        ).fetchone()
    assert int(transferred["total"]) == 0
    assert (
        appointments.is_slot_taken(
            ROLLBACK_ONLY_ROW["service"],
            ROLLBACK_ONLY_ROW["date"],
            ROLLBACK_ONLY_ROW["time"],
            pg_database,
        )
        is False
    )

    # 5. The app starts and persists with the rollback configuration and an
    # empty ``DATABASE_URL`` (RF-18, RNF-7).
    app_rollback_path = tmp_path / "app-rollback.db"

    class RollbackConfig(TestConfig):
        PERSISTENCE_BACKEND = "sqlite"
        DATABASE_PATH = app_rollback_path
        DATABASE_URL = ""

    application = create_app(RollbackConfig)
    application.config.update(TESTING=True)
    registered = application.extensions[DATABASE_EXTENSION_KEY]
    assert isinstance(registered, Database)
    assert registered.target.backend == "sqlite"
    assert registered.target.dsn is None

    with application.app_context():
        app_created = appointments.insert_appointment(
            APP_ROLLBACK_ROW, registered
        )
        assert (
            appointments.get_appointment_by_id(app_created.id, registered)
            == app_created
        )

    # Teardown closed the request connection; the row is really on disk.
    with get_connection(app_rollback_path) as connection:
        persisted = connection.execute(
            "SELECT count(*) AS total FROM appointments"
            " WHERE document_number = ?",
            (APP_ROLLBACK_ROW["document_number"],),
        ).fetchone()
    assert int(persisted["total"]) == 1
