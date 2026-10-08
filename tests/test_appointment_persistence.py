import sqlite3

import pytest

from consultorio.persistence import appointments_repository as repo
from consultorio.persistence.database import SCHEMA, get_connection, init_db

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


def test_init_db_crea_appointments_con_11_columnas_y_unique(database_path) -> None:
    with get_connection(database_path) as connection:
        columns = connection.execute(
            "PRAGMA table_info(appointments)"
        ).fetchall()
        assert len(columns) == 11
        names = [column["name"] for column in columns]
        assert names == [
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
        index_list = connection.execute(
            "PRAGMA index_list(appointments)"
        ).fetchall()
        unique_indexes = [
            index["name"] for index in index_list if index["unique"]
        ]
        assert unique_indexes, "Falta el índice UNIQUE de appointments"
        for index_name in unique_indexes:
            info = connection.execute(
                f"PRAGMA index_info({index_name})"
            ).fetchall()
            indexed = [column["name"] for column in info]
            if indexed == ["service", "date", "time"]:
                break
        else:
            pytest.fail("No existe UNIQUE (service, date, time)")
        assert "UNIQUE (service, date, time)" in SCHEMA


def test_insert_persiste_pending_y_get_recupera_todos_los_campos(
    database_path,
) -> None:
    created = repo.insert_appointment(VALID_DATA, database_path)
    assert created.id >= 1
    assert created.status == "pending"
    assert created.created_at
    fetched = repo.get_appointment_by_id(created.id, database_path)
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
    assert fetched.status == "pending"


def test_segundo_insert_misma_terna_genera_integrityerror_y_queda_1_fila(
    database_path,
) -> None:
    repo.insert_appointment(VALID_DATA, database_path)
    with pytest.raises(sqlite3.IntegrityError):
        repo.insert_appointment(VALID_DATA, database_path)
    with get_connection(database_path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS total FROM appointments"
        ).fetchone()["total"]
    assert count == 1
    assert repo.is_slot_taken("nutrition", "2026-10-12", "08:00", database_path)


def test_misma_hora_con_servicio_distinto_permitido(database_path) -> None:
    repo.insert_appointment(VALID_DATA, database_path)
    other = {**VALID_DATA, "service": "psychology_integral"}
    created = repo.insert_appointment(other, database_path)
    assert created.id >= 1
    with get_connection(database_path) as connection:
        count = connection.execute(
            "SELECT COUNT(*) AS total FROM appointments"
        ).fetchone()["total"]
    assert count == 2
    assert repo.is_slot_taken(
        "psychology_integral", "2026-10-12", "08:00", database_path
    )
    assert repo.list_booked_times("nutrition", "2026-10-12", database_path) == [
        "08:00"
    ]
