import os
import sys
import uuid
from pathlib import Path
from typing import Iterator

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from consultorio import create_app
from consultorio.config import TestConfig
from consultorio.persistence.database import DatabaseTarget, init_db

TEST_DATABASE_URL_ENV = "TEST_DATABASE_URL"


def require_test_database_url() -> str:
    """Return ``TEST_DATABASE_URL`` or fail explicitly (Spec 019 D9/CL-10).

    There is no ``skip``: without PostgreSQL the schema tests must fail with a
    clear instruction instead of producing empty evidence.
    """
    url = os.environ.get(TEST_DATABASE_URL_ENV, "").strip()
    if not url:
        pytest.fail(
            "TEST_DATABASE_URL no está definida: la Spec 019 exige PostgreSQL "
            "para los tests de esquema. Define el DSN local (ver "
            "docs/operaciones/postgresql.md) y vuelve a ejecutar."
        )
    return url


@pytest.fixture()
def app(tmp_path: Path) -> Iterator:
    class TempConfig(TestConfig):
        DATABASE_PATH: Path = tmp_path / "consultorio.db"
        # Keep the general suite away from any DATABASE_URL present in the
        # environment; PostgreSQL schema tests opt in through their own
        # fixtures and TEST_DATABASE_URL.
        DATABASE_URL: str = ""

    application = create_app(TempConfig)
    application.config.update(TESTING=True)
    yield application


@pytest.fixture()
def client(app) -> object:
    return app.test_client()


@pytest.fixture()
def database_path(tmp_path: Path) -> Iterator[Path]:
    path = tmp_path / "appointment.db"
    init_db(path)
    yield path


@pytest.fixture()
def pg_schema() -> Iterator[tuple[str, str]]:
    """Create a throwaway PostgreSQL schema and drop it afterwards.

    The schema is unique per test (``test_hu019_<uuid>``) so tests never touch
    the development data in ``public``. ``connect_timeout`` is always passed:
    without it this environment can block indefinitely.
    """
    import psycopg
    from psycopg import sql

    url = require_test_database_url()
    schema = f"test_hu019_{uuid.uuid4().hex}"
    try:
        with psycopg.connect(url, connect_timeout=5, autocommit=True) as conn:
            conn.execute(
                sql.SQL("CREATE SCHEMA {}").format(sql.Identifier(schema))
            )
    except Exception as exc:  # noqa: BLE001 - surface a clear failure
        pytest.fail(
            "No se pudo preparar el esquema de prueba en PostgreSQL "
            f"({type(exc).__name__}). ¿Está arriba el contenedor local? "
            "Ver docs/operaciones/postgresql.md."
        )
    try:
        yield url, schema
    finally:
        try:
            with psycopg.connect(
                url, connect_timeout=5, autocommit=True
            ) as conn:
                conn.execute(
                    sql.SQL("DROP SCHEMA IF EXISTS {} CASCADE").format(
                        sql.Identifier(schema)
                    )
                )
        except Exception:  # noqa: BLE001 - cleanup is best-effort
            pass


@pytest.fixture()
def pg_target(pg_schema: tuple[str, str]) -> DatabaseTarget:
    url, schema = pg_schema
    return DatabaseTarget(
        backend="postgres",
        dsn=url,
        schema=schema,
        connect_timeout=5.0,
        acquire_timeout=5.0,
        statement_timeout_ms=15000,
    )
