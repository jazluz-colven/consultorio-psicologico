"""Schema bootstrap tests against real PostgreSQL (Spec 019, T4).

Covers:
* TC-019-003 — empty database creates tables, ``UNIQUE(event_id)``, the partial
  unique index and ``schema_migrations``; verified against ``pg_indexes`` and
  ``information_schema``.
* TC-019-004 — a second run is idempotent and keeps rows.
* TC-019-005 — two concurrent instances serialize on the advisory lock and
  leave a single set of objects.
* TC-019-018 — reapplying the additive DDL over existing data preserves rows
  and integrity.

``TEST_DATABASE_URL`` is mandatory: without PostgreSQL these tests fail with a
clear message instead of skipping (D9/CL-10). Each test uses a throwaway schema
from the ``pg_schema``/``pg_target`` fixtures and never touches ``public``.
"""

import threading
from typing import Any

import pytest

from consultorio.persistence.database import Database, DatabaseTarget

PARTIAL_INDEX_NAME = "ux_appointments_slot_open"
EXPECTED_TABLES = {"appointments", "automation_events", "schema_migrations"}
EXPECTED_MIGRATION_VERSIONS = [1, 2, 3, 4]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _fetch(url: str, query: Any, params: tuple[Any, ...] = ()) -> list[tuple]:
    import psycopg

    with psycopg.connect(url, connect_timeout=5) as connection:
        return connection.execute(query, params).fetchall()


def _table_names(url: str, schema: str) -> set[str]:
    rows = _fetch(
        url,
        """
        SELECT table_name
        FROM information_schema.tables
        WHERE table_schema = %s
        """,
        (schema,),
    )
    return {row[0] for row in rows}


def _index_names(url: str, schema: str) -> set[str]:
    rows = _fetch(
        url,
        "SELECT indexname FROM pg_indexes WHERE schemaname = %s",
        (schema,),
    )
    return {row[0] for row in rows}


def _columns(url: str, schema: str, table: str) -> dict[str, dict[str, Any]]:
    rows = _fetch(
        url,
        """
        SELECT column_name, data_type, is_nullable, column_default
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = %s
        ORDER BY ordinal_position
        """,
        (schema, table),
    )
    return {
        row[0]: {
            "data_type": row[1],
            "is_nullable": row[2],
            "column_default": row[3],
        }
        for row in rows
    }


def _count(url: str, schema: str, table: str) -> int:
    from psycopg import sql

    query = sql.SQL("SELECT count(*) FROM {}.{}").format(
        sql.Identifier(schema), sql.Identifier(table)
    )
    return int(_fetch(url, query)[0][0])


def _migration_versions(url: str, schema: str) -> list[int]:
    from psycopg import sql

    query = sql.SQL(
        "SELECT version FROM {}.schema_migrations ORDER BY version"
    ).format(sql.Identifier(schema))
    return [int(row[0]) for row in _fetch(url, query)]


def _insert_appointment(connection: Any, **overrides: Any) -> int:
    values = {
        "document_type": "CC",
        "document_number": "123456789",
        "patient_name": "Paciente de prueba",
        "email": "paciente@example.com",
        "phone": "3000000000",
        "service": "terapia-individual",
        "date": "2026-11-10",
        "time": "08:00",
    }
    values.update(overrides)
    row = connection.execute(
        """
        INSERT INTO appointments (
            document_type, document_number, patient_name, email, phone,
            service, date, time
        )
        VALUES (%(document_type)s, %(document_number)s, %(patient_name)s,
                %(email)s, %(phone)s, %(service)s, %(date)s, %(time)s)
        RETURNING id
        """,
        values,
    ).fetchone()
    return row["id"]


def _insert_event(connection: Any, event_id: str, appointment_id: int) -> None:
    connection.execute(
        """
        INSERT INTO automation_events (
            event_id, event_type, event_version, appointment_id
        )
        VALUES (%s, %s, %s, %s)
        """,
        (event_id, "appointment.confirmed", 1, appointment_id),
    )


# ---------------------------------------------------------------------------
# TC-019-003 — empty database creates the expected schema
# ---------------------------------------------------------------------------


def test_tc_019_003_empty_database_creates_expected_schema(
    pg_target: DatabaseTarget,
) -> None:
    url, schema = pg_target.dsn, pg_target.schema
    assert url is not None and schema is not None

    Database(pg_target).ensure_schema()

    # Tables exist in the catalogs.
    assert EXPECTED_TABLES <= _table_names(url, schema)

    # ``automation_events.event_id`` is unique at the engine level.
    constraints = _fetch(
        url,
        """
        SELECT conname, pg_get_constraintdef(c.oid)
        FROM pg_constraint AS c
        JOIN pg_class AS t ON t.oid = c.conrelid
        JOIN pg_namespace AS n ON n.oid = t.relnamespace
        WHERE n.nspname = %s
          AND t.relname = 'automation_events'
          AND c.contype = 'u'
        """,
        (schema,),
    )
    assert any(
        "UNIQUE" in definition and "event_id" in definition
        for _name, definition in constraints
    )

    # Partial unique index, exactly as approved in plan §3.1.
    indexes = _fetch(
        url,
        """
        SELECT indexdef
        FROM pg_indexes
        WHERE schemaname = %s AND tablename = 'appointments' AND indexname = %s
        """,
        (schema, PARTIAL_INDEX_NAME),
    )
    assert len(indexes) == 1
    indexdef = indexes[0][0]
    assert indexdef.startswith("CREATE UNIQUE INDEX")
    assert PARTIAL_INDEX_NAME in indexdef
    assert "USING btree" in indexdef
    assert '(service, date, "time")' in indexdef
    assert "WHERE (status <> 'cancelled'" in indexdef

    # schema_migrations contract.
    migration_columns = _columns(url, schema, "schema_migrations")
    assert list(migration_columns) == ["version", "applied_at"]
    assert migration_columns["version"]["data_type"] == "integer"
    assert migration_columns["applied_at"]["data_type"] == "text"
    assert migration_columns["applied_at"]["is_nullable"] == "NO"
    assert "to_char" in migration_columns["applied_at"]["column_default"]
    assert "UTC" in migration_columns["applied_at"]["column_default"]

    # BIGSERIAL ids and UTC defaults from plan §3.1.
    appointment_columns = _columns(url, schema, "appointments")
    assert appointment_columns["id"]["data_type"] == "bigint"
    assert "to_char" in appointment_columns["created_at"]["column_default"]
    assert "UTC" in appointment_columns["created_at"]["column_default"]

    event_columns = _columns(url, schema, "automation_events")
    assert event_columns["id"]["data_type"] == "bigint"
    assert event_columns["event_id"]["data_type"] == "text"
    assert "to_char" in event_columns["created_at"]["column_default"]
    assert "UTC" in event_columns["created_at"]["column_default"]

    assert _migration_versions(url, schema) == EXPECTED_MIGRATION_VERSIONS


# ---------------------------------------------------------------------------
# TC-019-004 — second execution is idempotent and keeps data
# ---------------------------------------------------------------------------


def test_tc_019_004_second_run_is_idempotent_and_keeps_data(
    pg_target: DatabaseTarget,
) -> None:
    url, schema = pg_target.dsn, pg_target.schema
    assert url is not None and schema is not None

    first = Database(pg_target)
    first.ensure_schema()
    tables_before = _table_names(url, schema)
    indexes_before = _index_names(url, schema)

    with first.transaction() as connection:
        appointment_id = _insert_appointment(connection)
        _insert_event(connection, "evt-idempotent", appointment_id)

    # A fresh instance resets the ready flag, so the DDL really runs again.
    second = Database(pg_target)
    second.ensure_schema()

    assert _table_names(url, schema) == tables_before
    assert _index_names(url, schema) == indexes_before
    assert _count(url, schema, "appointments") == 1
    assert _count(url, schema, "automation_events") == 1
    # ON CONFLICT DO NOTHING: no duplicated migration markers.
    assert _migration_versions(url, schema) == EXPECTED_MIGRATION_VERSIONS


# ---------------------------------------------------------------------------
# TC-019-005 — two concurrent instances on an empty database
# ---------------------------------------------------------------------------


def test_tc_019_005_concurrent_bootstrap_leaves_single_object_set(
    pg_target: DatabaseTarget,
) -> None:
    url, schema = pg_target.dsn, pg_target.schema
    assert url is not None and schema is not None

    databases = [Database(pg_target), Database(pg_target)]
    barrier = threading.Barrier(len(databases))
    errors: list[BaseException] = []

    def bootstrap(database: Database) -> None:
        barrier.wait(timeout=10)
        try:
            database.ensure_schema()
        except BaseException as exc:  # noqa: BLE001 - collected and asserted
            errors.append(exc)

    threads = [
        threading.Thread(target=bootstrap, args=(database,))
        for database in databases
    ]
    for thread in threads:
        thread.start()
    for thread in threads:
        thread.join(timeout=30)

    assert not any(thread.is_alive() for thread in threads)
    assert errors == []
    assert EXPECTED_TABLES <= _table_names(url, schema)

    index_rows = _fetch(
        url,
        """
        SELECT indexname
        FROM pg_indexes
        WHERE schemaname = %s AND indexname = %s
        """,
        (schema, PARTIAL_INDEX_NAME),
    )
    assert index_rows == [(PARTIAL_INDEX_NAME,)]
    assert _migration_versions(url, schema) == EXPECTED_MIGRATION_VERSIONS


# ---------------------------------------------------------------------------
# TC-019-018 — reapply the additive DDL over existing data
# ---------------------------------------------------------------------------


def test_tc_019_018_reapply_over_data_preserves_rows_and_integrity(
    pg_target: DatabaseTarget,
) -> None:
    import psycopg.errors as pg_errors

    url, schema = pg_target.dsn, pg_target.schema
    assert url is not None and schema is not None

    first = Database(pg_target)
    first.ensure_schema()
    with first.transaction() as connection:
        appointment_id = _insert_appointment(connection)
        _insert_event(connection, "evt-preserved", appointment_id)

    # Reapply with a fresh instance over the populated schema.
    second = Database(pg_target)
    second.ensure_schema()

    with second.connection() as connection:
        appointment = connection.execute(
            "SELECT id, service, date, time, status FROM appointments"
        ).fetchone()
        event = connection.execute(
            "SELECT event_id, appointment_id FROM automation_events"
        ).fetchone()

    assert appointment["id"] == appointment_id
    assert appointment["service"] == "terapia-individual"
    assert appointment["status"] == "confirmed"
    assert event["event_id"] == "evt-preserved"
    assert event["appointment_id"] == appointment_id

    # Integrity survives the reapplication: no duplicate active slot.
    with pytest.raises(pg_errors.UniqueViolation):
        with second.transaction() as connection:
            _insert_appointment(connection)

    # And no duplicate event id either.
    with pytest.raises(pg_errors.UniqueViolation):
        with second.transaction() as connection:
            _insert_event(connection, "evt-preserved", appointment_id)
