"""Appointments persistence contract against PostgreSQL (Spec 019, T10).

The assertions that used to read SQLite ``PRAGMA``/``sqlite_master`` now read
the real PostgreSQL catalogs (``information_schema``, ``pg_indexes``,
``pg_index`` and ``pg_constraint``) in the isolated per-test schema. The
partial unique index and the absence of an inline unique constraint are the
same guarantees as before (Spec 010 Q4, Spec 006).
"""

import psycopg.errors as pg_errors
import pytest

from consultorio.persistence import appointments_repository as repo
from consultorio.persistence.database import PARTIAL_INDEX_NAME

VALID_DATA = {
    "document_type": "CC",
    "document_number": "1234567890",
    "patient_name": "Ana Pérez",
    "email": "ana@correo.com",
    "phone": "3001234567",
    "service": "nutrition",
    "date": "2026-10-12",
    "time": "08:00",
}

EXPECTED_COLUMNS = [
    "id",
    "document_type",
    "document_number",
    "patient_name",
    "email",
    "phone",
    "service",
    "date",
    "time",
    "status",
    "created_at",
]


def _fetch(database, query: str, params: tuple = ()) -> list:
    with database.connection() as connection:
        return connection.execute(query, params).fetchall()


def _count(database, table: str) -> int:
    rows = _fetch(database, f"SELECT count(*) AS total FROM {table}")
    return int(rows[0]["total"])


def test_init_db_crea_appointments_con_11_columnas_y_unique(database) -> None:
    schema = database.target.schema
    assert schema is not None

    columns = _fetch(
        database,
        """
        SELECT column_name
        FROM information_schema.columns
        WHERE table_schema = %s AND table_name = 'appointments'
        ORDER BY ordinal_position
        """,
        (schema,),
    )
    assert len(columns) == 11
    assert [column["column_name"] for column in columns] == EXPECTED_COLUMNS

    # The partial unique index exists and has the approved predicate.
    indexes = _fetch(
        database,
        """
        SELECT indexname, indexdef
        FROM pg_indexes
        WHERE schemaname = %s AND tablename = 'appointments'
        """,
        (schema,),
    )
    partial = [
        row for row in indexes if row["indexname"] == PARTIAL_INDEX_NAME
    ]
    assert partial, "Falta el índice UNIQUE parcial de appointments"
    indexdef = partial[0]["indexdef"]
    assert "CREATE UNIQUE INDEX" in indexdef
    assert "(service, date, \"time\")" in indexdef
    assert "WHERE (status <> 'cancelled'" in indexdef

    # ``pg_index`` confirms it is unique and partial at the engine level.
    pg_index_rows = _fetch(
        database,
        """
        SELECT i.indisunique, (i.indpred IS NOT NULL) AS is_partial
        FROM pg_index AS i
        JOIN pg_class AS c ON c.oid = i.indexrelid
        JOIN pg_class AS t ON t.oid = i.indrelid
        JOIN pg_namespace AS n ON n.oid = t.relnamespace
        WHERE n.nspname = %s AND c.relname = %s
        """,
        (schema, PARTIAL_INDEX_NAME),
    )
    assert len(pg_index_rows) == 1
    assert pg_index_rows[0]["indisunique"] is True
    assert pg_index_rows[0]["is_partial"] is True

    # HU-010 (spec 010 amended): uniqueness is NOT an inline table constraint.
    unique_constraints = _fetch(
        database,
        """
        SELECT conname, pg_get_constraintdef(c.oid) AS definition
        FROM pg_constraint AS c
        JOIN pg_class AS t ON t.oid = c.conrelid
        JOIN pg_namespace AS n ON n.oid = t.relnamespace
        WHERE n.nspname = %s
          AND t.relname = 'appointments'
          AND c.contype = 'u'
        """,
        (schema,),
    )
    assert unique_constraints == []


def test_insert_persiste_confirmed_y_get_recupera_todos_los_campos(
    database,
) -> None:
    created = repo.insert_appointment(VALID_DATA, database)
    assert created.id >= 1
    assert created.status == "confirmed"
    assert created.created_at
    fetched = repo.get_appointment_by_id(created.id, database)
    assert fetched is not None
    assert fetched.id == created.id
    assert fetched.document_type == "CC"
    assert fetched.document_number == "1234567890"
    assert fetched.patient_name == "Ana Pérez"
    assert fetched.email == "ana@correo.com"
    assert fetched.phone == "3001234567"
    assert fetched.service == "nutrition"
    assert fetched.date == "2026-10-12"
    assert fetched.time == "08:00"
    assert fetched.status == "confirmed"


def test_segundo_insert_misma_terna_genera_integrityerror_y_queda_1_fila(
    database,
) -> None:
    repo.insert_appointment(VALID_DATA, database)
    with pytest.raises(pg_errors.UniqueViolation):
        repo.insert_appointment(VALID_DATA, database)
    assert _count(database, "appointments") == 1
    assert repo.is_slot_taken("nutrition", "2026-10-12", "08:00", database)


def test_misma_hora_con_servicio_distinto_permitido(database) -> None:
    repo.insert_appointment(VALID_DATA, database)
    other = {**VALID_DATA, "service": "psychology_integral"}
    created = repo.insert_appointment(other, database)
    assert created.id >= 1
    assert _count(database, "appointments") == 2
    assert repo.is_slot_taken(
        "psychology_integral", "2026-10-12", "08:00", database
    )
    assert repo.list_booked_times("nutrition", "2026-10-12", database) == [
        "08:00"
    ]
