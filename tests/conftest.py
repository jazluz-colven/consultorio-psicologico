import os
import sys
import uuid
from pathlib import Path
from typing import Iterator

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from consultorio import DATABASE_EXTENSION_KEY, create_app
from consultorio.config import TestConfig
from consultorio.persistence.database import Database, DatabaseTarget

TEST_DATABASE_URL_ENV = "TEST_DATABASE_URL"

_TEST_DATABASE_HELP = """
La Spec 019 (plan D9, RF-28/RF-29, CL-10) exige que la suite se ejecute
SIEMPRE contra PostgreSQL. No se usa `skip` ni `xfail`: sin base de datos la
sesión se detiene al inicio.

1) Levanta el contenedor local reproducible (si ya existe, usa `docker start`):

   docker run -d --name consultorio-pg-019 -e POSTGRES_DB=consultorio_dev -e POSTGRES_USER=consultorio_dev -e POSTGRES_PASSWORD=<password-local> -p 127.0.0.1:55432:5432 -v consultorio-pgdata-019:/var/lib/postgresql/data postgres:16-alpine

   docker start consultorio-pg-019

2) Define el DSN solo en la sesión de PowerShell:

   $env:TEST_DATABASE_URL = "postgresql://consultorio_dev:<password-local>@127.0.0.1:55432/consultorio_dev?sslmode=disable"

3) Repite:

   python -m pytest -q

Procedimiento completo: docs/operaciones/postgresql.md
""".strip()


def _test_database_url() -> str:
    return os.environ.get(TEST_DATABASE_URL_ENV, "").strip()


def check_test_database_or_exit() -> None:
    """Fail the whole session when PostgreSQL is missing (D9/CL-10).

    Called from ``pytest_configure`` only, never at import time. The DSN is
    never printed and no ``skip`` is used.
    """
    url = _test_database_url()
    if not url:
        pytest.exit(
            "TEST_DATABASE_URL no está definida. "
            + _TEST_DATABASE_HELP,
            returncode=1,
        )
    import psycopg

    try:
        with psycopg.connect(url, connect_timeout=5) as connection:
            connection.execute("SELECT 1")
    except Exception as exc:  # noqa: BLE001 - surface a clear failure
        pytest.exit(
            "No se pudo conectar a TEST_DATABASE_URL "
            f"({type(exc).__name__}). "
            + _TEST_DATABASE_HELP,
            returncode=1,
        )


def pytest_configure(config: pytest.Config) -> None:
    """Validate the mandatory test database before collecting any test."""
    check_test_database_or_exit()


def require_test_database_url() -> str:
    """Return ``TEST_DATABASE_URL`` or fail explicitly (Spec 019 D9/CL-10).

    There is no ``skip``: without PostgreSQL the schema tests must fail with a
    clear instruction instead of producing empty evidence. The session hook
    normally stops pytest earlier; this guard keeps the fixtures honest if one
    is used from a different entry point.
    """
    url = _test_database_url()
    if not url:
        pytest.fail(
            "TEST_DATABASE_URL no está definida: la Spec 019 exige PostgreSQL "
            "para los tests de esquema. Define el DSN local (ver "
            "docs/operaciones/postgresql.md) y vuelve a ejecutar."
        )
    return url


@pytest.fixture()
def app(tmp_path: Path, pg_target: DatabaseTarget) -> Iterator:
    """Flask app bound to an isolated PostgreSQL schema.

    ``create_app`` bootstraps with the SQLite rollback target (``DATABASE_URL``
    empty) so it never opens a connection against ``public``. The persistence
    facade is then replaced by a PostgreSQL ``Database`` whose ``search_path``
    points to the per-test ``test_hu019_<uuid>`` schema. Its teardown runs
    before ``pg_schema`` drops the schema.
    """
    class TempConfig(TestConfig):
        DATABASE_PATH: Path = tmp_path / "consultorio.db"
        # Keep the bootstrap away from any DATABASE_URL present in the
        # environment; PostgreSQL is attached explicitly below.
        DATABASE_URL: str = ""

    application = create_app(TempConfig)
    application.config.update(TESTING=True)

    database = Database(pg_target)
    database.ensure_schema()
    application.extensions[DATABASE_EXTENSION_KEY] = database
    # Keep the configuration coherent with the database actually in use.
    application.config["PERSISTENCE_BACKEND"] = "postgres"
    application.config["DATABASE_URL"] = pg_target.dsn or ""

    try:
        yield application
    finally:
        # The app teardown closes request-scoped connections; this is a safe
        # no-op outside an app context and guarantees nothing stays open
        # before the schema is dropped.
        with application.app_context():
            database.close_request()


@pytest.fixture()
def database(app):
    """The PostgreSQL ``Database`` registered by the ``app`` fixture."""
    return app.extensions[DATABASE_EXTENSION_KEY]


@pytest.fixture()
def client(app) -> object:
    return app.test_client()


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
