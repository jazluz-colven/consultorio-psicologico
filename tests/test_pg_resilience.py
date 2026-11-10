"""TC-019-001 — configuración PostgreSQL por entorno (Spec 019, T2).

Estas pruebas no abren una conexión real: validan que ``consultorio.config``
lee y valida ``DATABASE_URL``, ``PERSISTENCE_BACKEND`` y los límites/timeouts
sin exponer secretos. La conexión real se verifica en la evidencia de T2 y las
pruebas de conexión pertenecen a T3/T12.
"""

import importlib
import logging
import os
import sqlite3
from datetime import date, timedelta
from pathlib import Path

import pytest

import consultorio.config as config_module
from consultorio import DATABASE_EXTENSION_KEY, create_app
from consultorio.config import Config, TestConfig
from consultorio.content.admin_content import (
    ADMIN_APPOINTMENT_NOT_FOUND,
    ADMIN_BACK_BUTTON,
    ADMIN_MSG_ALREADY_CANCELLED,
)
from consultorio.content.appointment_content import (
    MSG_OCCUPIED_HOUR,
    MSG_PERSISTENCE_UNAVAILABLE,
    MSG_SLOT_TAKEN,
)
from consultorio.content.cancellation_content import (
    MSG_ALREADY_CANCELLED,
    MSG_VERIFICATION_FAILED,
)
from consultorio.errors import PersistenceUnavailable
from consultorio.persistence.database import Database, DatabaseTarget

_CONFIG_ENV_VARS = (
    "DATABASE_URL",
    "PERSISTENCE_BACKEND",
    "DATABASE_PATH",
    "DATABASE_MAX_CONNECTIONS",
    "DATABASE_CONNECT_TIMEOUT",
    "DATABASE_ACQUIRE_TIMEOUT",
    "DATABASE_STATEMENT_TIMEOUT_MS",
)


@pytest.fixture()
def isolated_config(monkeypatch) -> object:
    """Reload the config module with a clean environment and restore it later."""
    original = {name: os.environ.get(name) for name in _CONFIG_ENV_VARS}
    for name in _CONFIG_ENV_VARS:
        monkeypatch.delenv(name, raising=False)
    importlib.reload(config_module)
    try:
        yield config_module
    finally:
        for name, value in original.items():
            if value is None:
                monkeypatch.delenv(name, raising=False)
            else:
                monkeypatch.setenv(name, value)
        importlib.reload(config_module)


def _reload_with(monkeypatch, **values: str) -> object:
    for name, value in values.items():
        monkeypatch.setenv(name, value)
    return importlib.reload(config_module)


def test_default_values(isolated_config) -> None:
    assert config_module.Config.PERSISTENCE_BACKEND == "postgres"
    assert config_module.Config.DATABASE_URL == ""
    assert config_module.Config.DATABASE_MAX_CONNECTIONS == 5
    assert config_module.Config.DATABASE_CONNECT_TIMEOUT == 10.0
    assert config_module.Config.DATABASE_ACQUIRE_TIMEOUT == 5.0
    assert config_module.Config.DATABASE_STATEMENT_TIMEOUT_MS == 15000


def test_invalid_backend_raises_value_error(isolated_config, monkeypatch) -> None:
    monkeypatch.setenv("PERSISTENCE_BACKEND", "mysql")
    with pytest.raises(ValueError, match="PERSISTENCE_BACKEND"):
        importlib.reload(config_module)


def test_missing_database_url_does_not_raise(isolated_config, monkeypatch) -> None:
    monkeypatch.delenv("DATABASE_URL", raising=False)
    monkeypatch.setenv("PERSISTENCE_BACKEND", "postgres")
    reloaded = importlib.reload(config_module)
    assert reloaded.Config.DATABASE_URL == ""


@pytest.mark.parametrize(
    "query",
    ["", "?sslmode=disable", "?sslmode=prefer", "?sslmode="],
)
def test_non_local_database_url_requires_tls(
    isolated_config, monkeypatch, query: str
) -> None:
    monkeypatch.setenv(
        "DATABASE_URL",
        f"postgresql://usuario@db.example.com:5432/consultorio{query}",
    )
    with pytest.raises(ValueError, match="sslmode") as excinfo:
        importlib.reload(config_module)
    # El mensaje no debe incluir el DSN ni credenciales.
    assert "db.example.com" not in str(excinfo.value)


def test_non_local_database_url_accepts_required_tls(
    isolated_config, monkeypatch
) -> None:
    url = (
        "postgresql://usuario@db.example.com:5432/consultorio"
        "?sslmode=require"
    )
    reloaded = _reload_with(monkeypatch, DATABASE_URL=url)
    assert reloaded.Config.DATABASE_URL == url


@pytest.mark.parametrize(
    "host",
    ["localhost", "127.0.0.1", "[::1]"],
)
def test_local_database_url_accepts_disable(
    isolated_config, monkeypatch, host: str
) -> None:
    url = f"postgresql://consultorio_dev@{host}:55432/consultorio_dev?sslmode=disable"
    reloaded = _reload_with(monkeypatch, DATABASE_URL=url)
    assert reloaded.Config.DATABASE_URL == url


def test_sqlite_backend_accepts_database_path(
    isolated_config, monkeypatch, tmp_path: Path
) -> None:
    rollback_path = tmp_path / "rollback.db"
    reloaded = _reload_with(
        monkeypatch,
        PERSISTENCE_BACKEND="sqlite",
        DATABASE_PATH=str(rollback_path),
    )
    assert reloaded.Config.PERSISTENCE_BACKEND == "sqlite"
    assert reloaded.Config.DATABASE_PATH == rollback_path


def test_sqlite_backend_ignores_tls_validation(
    isolated_config, monkeypatch
) -> None:
    # A non-local DSN without sslmode would fail for postgres; sqlite ignores it.
    reloaded = _reload_with(
        monkeypatch,
        PERSISTENCE_BACKEND="sqlite",
        DATABASE_URL="postgresql://usuario@db.example.com:5432/consultorio",
    )
    assert reloaded.Config.PERSISTENCE_BACKEND == "sqlite"


def test_database_limits_and_timeouts_are_parsed(
    isolated_config, monkeypatch
) -> None:
    reloaded = _reload_with(
        monkeypatch,
        DATABASE_MAX_CONNECTIONS="8",
        DATABASE_CONNECT_TIMEOUT="2.5",
        DATABASE_ACQUIRE_TIMEOUT="3.5",
        DATABASE_STATEMENT_TIMEOUT_MS="25000",
    )
    assert reloaded.Config.DATABASE_MAX_CONNECTIONS == 8
    assert reloaded.Config.DATABASE_CONNECT_TIMEOUT == 2.5
    assert reloaded.Config.DATABASE_ACQUIRE_TIMEOUT == 3.5
    assert reloaded.Config.DATABASE_STATEMENT_TIMEOUT_MS == 25000


@pytest.mark.parametrize("raw", ["", "0", "-1", "not-a-number"])
def test_invalid_limits_fall_back_to_defaults(
    isolated_config, monkeypatch, raw: str
) -> None:
    reloaded = _reload_with(
        monkeypatch,
        DATABASE_MAX_CONNECTIONS=raw,
        DATABASE_CONNECT_TIMEOUT=raw,
        DATABASE_ACQUIRE_TIMEOUT=raw,
        DATABASE_STATEMENT_TIMEOUT_MS=raw,
    )
    assert reloaded.Config.DATABASE_MAX_CONNECTIONS == 5
    assert reloaded.Config.DATABASE_CONNECT_TIMEOUT == 10.0
    assert reloaded.Config.DATABASE_ACQUIRE_TIMEOUT == 5.0
    assert reloaded.Config.DATABASE_STATEMENT_TIMEOUT_MS == 15000


# ---------------------------------------------------------------------------
# TC-019-002 — connection layer, semaphore and domain error translation (T3)
#
# T3 does not require a real PostgreSQL server. The factory is faked so the
# test can assert real open/close/commit/rollback calls, the number of opened
# connections and permit release without TEST_DATABASE_URL. Real PostgreSQL
# integration belongs to T10/T11.
# ---------------------------------------------------------------------------


class _FakeConnection:
    def __init__(
        self,
        events: list[tuple[str, str]],
        name: str,
        *,
        execute_error: BaseException | None = None,
        commit_error: BaseException | None = None,
        rollback_error: BaseException | None = None,
    ) -> None:
        self.events = events
        self.name = name
        self.closed = False
        self.commits = 0
        self.rollbacks = 0
        self._execute_error = execute_error
        self._commit_error = commit_error
        self._rollback_error = rollback_error

    def execute(self, *_args: object, **_kwargs: object) -> None:
        self.events.append(("execute", self.name))
        if self._execute_error is not None:
            raise self._execute_error

    def commit(self) -> None:
        self.commits += 1
        self.events.append(("commit", self.name))
        if self._commit_error is not None:
            raise self._commit_error

    def rollback(self) -> None:
        self.rollbacks += 1
        self.events.append(("rollback", self.name))
        if self._rollback_error is not None:
            raise self._rollback_error

    def close(self) -> None:
        self.closed = True
        self.events.append(("close", self.name))


class _FakeConnectionFactory:
    """Records opens; can fail once with a supplied exception."""

    def __init__(
        self,
        error: BaseException | None = None,
        *,
        execute_error: BaseException | None = None,
        commit_error: BaseException | None = None,
        rollback_error: BaseException | None = None,
    ) -> None:
        self.opens = 0
        self.connections: list[_FakeConnection] = []
        self.events: list[tuple[str, str]] = []
        self._next_error = error
        self._execute_error = execute_error
        self._commit_error = commit_error
        self._rollback_error = rollback_error

    def __call__(self, _target: DatabaseTarget) -> _FakeConnection:
        self.opens += 1
        if self._next_error is not None:
            error = self._next_error
            self._next_error = None
            raise error
        connection = _FakeConnection(
            self.events,
            f"conn-{self.opens}",
            execute_error=self._execute_error,
            commit_error=self._commit_error,
            rollback_error=self._rollback_error,
        )
        self.connections.append(connection)
        self.events.append(("open", connection.name))
        return connection


class _FakeOperationalError(Exception):
    pass


class _FakeInterfaceError(Exception):
    pass


_FAKE_DRIVER_ERRORS = (_FakeOperationalError, _FakeInterfaceError)
_SECRET_DSN = (
    "postgresql://usuario:super-secret-password@db.example.com:5432/"
    "consultorio?sslmode=require"
)


def _fake_target(**overrides: object) -> DatabaseTarget:
    values: dict[str, object] = {
        "backend": "postgres",
        "dsn": _SECRET_DSN,
        "max_connections": 5,
        "connect_timeout": 1.0,
        "acquire_timeout": 0.2,
        "statement_timeout_ms": 1000,
    }
    values.update(overrides)
    return DatabaseTarget(**values)  # type: ignore[arg-type]


def test_connection_reused_within_request_and_closed_on_teardown(app) -> None:
    factory = _FakeConnectionFactory()
    database = Database(
        _fake_target(), connect_factory=factory, driver_errors=_FAKE_DRIVER_ERRORS
    )
    app.extensions[DATABASE_EXTENSION_KEY] = database

    with app.test_request_context("/citas"):
        with database.connection() as first:
            with database.connection() as second:
                assert first is second
        # Leaving the inner ``with`` must not close the request connection.
        assert factory.opens == 1
        assert len(factory.connections) == 1
        assert not first.closed

    # teardown_appcontext closes the request connection.
    assert first.closed
    assert factory.events.count(("close", first.name)) == 1


def test_close_request_is_idempotent(app) -> None:
    factory = _FakeConnectionFactory()
    database = Database(
        _fake_target(), connect_factory=factory, driver_errors=_FAKE_DRIVER_ERRORS
    )

    with app.app_context():
        with database.connection() as connection:
            assert not connection.closed
        database.close_request()
        database.close_request()

    assert connection.closed
    assert factory.events.count(("close", connection.name)) == 1


def test_connection_outside_request_opens_and_closes_each_time() -> None:
    factory = _FakeConnectionFactory()
    database = Database(
        _fake_target(), connect_factory=factory, driver_errors=_FAKE_DRIVER_ERRORS
    )

    with database.connection() as first:
        assert not first.closed
    assert first.closed

    with database.connection() as second:
        assert not second.closed
    assert second.closed

    assert factory.opens == 2
    assert first is not second
    assert factory.events == [
        ("open", "conn-1"),
        ("close", "conn-1"),
        ("open", "conn-2"),
        ("close", "conn-2"),
    ]


def test_semaphore_acquire_timeout_raises_persistence_unavailable() -> None:
    factory = _FakeConnectionFactory()
    database = Database(
        _fake_target(max_connections=1, acquire_timeout=0.05),
        connect_factory=factory,
        driver_errors=_FAKE_DRIVER_ERRORS,
    )

    with database.connection() as first:
        with pytest.raises(PersistenceUnavailable) as excinfo:
            with database.connection():
                pytest.fail("A second connection must not be acquired")
        assert str(excinfo.value) != "slot_taken"

    # The permit is released on close: a later operation succeeds.
    with database.connection() as second:
        assert not second.closed
    assert second.closed
    assert factory.opens == 2
    assert first is not second


def test_transaction_commits_once_on_success() -> None:
    factory = _FakeConnectionFactory()
    database = Database(
        _fake_target(), connect_factory=factory, driver_errors=_FAKE_DRIVER_ERRORS
    )

    with database.transaction() as connection:
        assert not connection.closed
        assert connection.commits == 0

    assert connection.commits == 1
    assert connection.rollbacks == 0
    assert connection.closed
    assert factory.opens == 1


def test_transaction_rolls_back_on_error() -> None:
    factory = _FakeConnectionFactory()
    database = Database(
        _fake_target(), connect_factory=factory, driver_errors=_FAKE_DRIVER_ERRORS
    )

    with pytest.raises(RuntimeError, match="boom"):
        with database.transaction() as connection:
            raise RuntimeError("boom")

    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.closed


def test_transaction_shares_request_connection(app) -> None:
    factory = _FakeConnectionFactory()
    database = Database(
        _fake_target(), connect_factory=factory, driver_errors=_FAKE_DRIVER_ERRORS
    )
    app.extensions[DATABASE_EXTENSION_KEY] = database

    with app.test_request_context("/citas"):
        with database.transaction() as transaction_connection:
            with database.connection() as current:
                assert current is transaction_connection
        assert transaction_connection.commits == 1
        assert not transaction_connection.closed
        assert factory.opens == 1
        database.close_request()
        assert transaction_connection.closed


@pytest.mark.parametrize(
    "error_type", [_FakeOperationalError, _FakeInterfaceError]
)
def test_driver_errors_translate_to_persistence_unavailable(
    error_type: type[BaseException],
) -> None:
    factory = _FakeConnectionFactory(
        error=error_type(f"connection failed: {_SECRET_DSN}")
    )
    database = Database(
        _fake_target(), connect_factory=factory, driver_errors=_FAKE_DRIVER_ERRORS
    )

    with pytest.raises(PersistenceUnavailable) as excinfo:
        with database.connection():
            pytest.fail("A failed open must not yield a connection")

    assert "slot_taken" != str(excinfo.value)
    assert "super-secret-password" not in str(excinfo.value)

    # The failed open released its permit: the next operation works.
    with database.connection() as connection:
        assert not connection.closed
    assert connection.closed
    assert factory.opens == 2


@pytest.mark.parametrize(
    "error",
    [
        sqlite3.OperationalError("database is locked"),
        sqlite3.InterfaceError("bad sqlite state"),
    ],
)
def test_sqlite_driver_errors_translate_to_persistence_unavailable(
    error: BaseException,
) -> None:
    """D6 also covers the SQLite rollback backend, not only psycopg."""
    factory = _FakeConnectionFactory(error=error)
    database = Database(
        DatabaseTarget(
            backend="sqlite", sqlite_path=Path("unused-for-test.db")
        ),
        connect_factory=factory,
    )

    with pytest.raises(PersistenceUnavailable) as excinfo:
        with database.connection():
            pytest.fail("A SQLite outage must not yield a connection")

    assert str(excinfo.value) != "slot_taken"
    assert "locked" not in str(excinfo.value)
    assert "bad sqlite state" not in str(excinfo.value)


def test_non_driver_errors_are_not_translated() -> None:
    factory = _FakeConnectionFactory(error=ValueError("programmer error"))
    database = Database(
        _fake_target(), connect_factory=factory, driver_errors=_FAKE_DRIVER_ERRORS
    )

    with pytest.raises(ValueError, match="programmer error"):
        with database.connection():
            pytest.fail("A non-driver error must propagate unchanged")

    # The permit was still released.
    with database.connection() as connection:
        assert not connection.closed
    assert connection.closed


@pytest.mark.parametrize("error_name", ["OperationalError", "InterfaceError"])
def test_connection_operation_driver_error_translates_and_releases(
    error_name: str,
) -> None:
    """F-01: a driver failure during the ``yield`` is not only on open."""
    import psycopg

    error_type = getattr(psycopg, error_name)
    factory = _FakeConnectionFactory(
        execute_error=error_type("connection lost during query")
    )
    database = Database(_fake_target(), connect_factory=factory)

    with pytest.raises(PersistenceUnavailable) as excinfo:
        with database.connection() as connection:
            connection.execute("SELECT 1")

    assert "slot_taken" != str(excinfo.value)
    # Outside an app context the connection is closed and the permit released.
    assert connection.closed
    assert factory.events.count(("close", connection.name)) == 1

    with database.connection() as later:
        assert not later.closed
    assert later.closed
    assert factory.opens == 2


def test_transaction_body_driver_error_translates_and_rolls_back() -> None:
    import psycopg

    factory = _FakeConnectionFactory(
        execute_error=psycopg.OperationalError("connection lost in transaction")
    )
    database = Database(_fake_target(), connect_factory=factory)

    with pytest.raises(PersistenceUnavailable) as excinfo:
        with database.transaction() as connection:
            connection.execute("UPDATE appointments SET status = 'confirmed'")

    assert "slot_taken" != str(excinfo.value)
    assert connection.commits == 0
    assert connection.rollbacks == 1
    assert connection.closed


def test_transaction_commit_driver_error_translates_and_rolls_back() -> None:
    """F-01: a failure raised by ``commit`` is translated, not leaked raw."""
    import psycopg

    factory = _FakeConnectionFactory(
        commit_error=psycopg.OperationalError("server closed the connection")
    )
    database = Database(_fake_target(), connect_factory=factory)

    with pytest.raises(PersistenceUnavailable) as excinfo:
        with database.transaction() as connection:
            pass

    assert "slot_taken" != str(excinfo.value)
    assert connection.commits == 1
    assert connection.rollbacks == 1
    assert ("rollback", connection.name) in factory.events
    assert connection.closed


def test_transaction_rollback_driver_error_translates() -> None:
    """F-01: a driver failure during the rollback is translated too."""
    import psycopg

    factory = _FakeConnectionFactory(
        rollback_error=psycopg.OperationalError("rollback failed")
    )
    database = Database(_fake_target(), connect_factory=factory)

    with pytest.raises(PersistenceUnavailable):
        with database.transaction() as connection:
            raise ValueError("business failure")

    assert connection.rollbacks == 1
    assert connection.closed


@pytest.mark.parametrize(
    "error_name",
    [
        "CannotConnectNow",
        "AdminShutdown",
        "CrashShutdown",
        "ConnectionFailure",
        "ConnectionDoesNotExist",
        "ConnectionTimeout",
    ],
)
def test_real_psycopg_operational_subclasses_translate(error_name: str) -> None:
    """F-02: real psycopg subclasses are recognised via ``isinstance``."""
    import psycopg.errors as pg_errors

    error_type = getattr(pg_errors, error_name)
    factory = _FakeConnectionFactory(error=error_type("database unavailable"))
    database = Database(_fake_target(), connect_factory=factory)

    with pytest.raises(PersistenceUnavailable) as excinfo:
        with database.connection():
            pytest.fail("A driver outage must not yield a connection")

    assert "slot_taken" != str(excinfo.value)
    # The failed open released its permit.
    with database.connection() as connection:
        assert not connection.closed
    assert connection.closed
    assert factory.opens == 2


def test_real_psycopg_unique_violation_is_not_translated() -> None:
    """Integrity conflicts stay out of ``PersistenceUnavailable`` (T5/T6)."""
    import psycopg.errors as pg_errors

    factory = _FakeConnectionFactory(
        error=pg_errors.UniqueViolation("duplicate key value")
    )
    database = Database(_fake_target(), connect_factory=factory)

    with pytest.raises(pg_errors.UniqueViolation):
        with database.connection():
            pytest.fail("A unique violation must not be treated as an outage")

    # The permit was still released.
    with database.connection() as connection:
        assert not connection.closed
    assert factory.opens == 2


def test_repr_never_exposes_dsn_or_credentials() -> None:
    target = _fake_target()
    database = Database(target, connect_factory=_FakeConnectionFactory())

    for text in (repr(target), str(target), repr(database), str(database)):
        assert "super-secret-password" not in text
        assert "db.example.com" not in text
        assert "postgresql://" not in text
    assert "dsn='<set>'" in repr(target)


def test_failed_connection_does_not_log_dsn_or_credentials(caplog) -> None:
    factory = _FakeConnectionFactory(
        error=_FakeOperationalError(f"could not connect: {_SECRET_DSN}")
    )
    database = Database(
        _fake_target(), connect_factory=factory, driver_errors=_FAKE_DRIVER_ERRORS
    )

    with caplog.at_level(logging.DEBUG):
        with pytest.raises(PersistenceUnavailable):
            with database.connection():
                pytest.fail("A failed open must not yield a connection")

    assert "super-secret-password" not in caplog.text
    assert "db.example.com" not in caplog.text
    assert "postgresql://" not in caplog.text


def test_create_app_registers_side_effect_free_database(tmp_path: Path) -> None:
    class PostgresConfig(TestConfig):
        PERSISTENCE_BACKEND = "postgres"
        DATABASE_URL = (
            "postgresql://consultorio_dev@127.0.0.1:1/consultorio_dev"
            "?sslmode=disable"
        )
        DATABASE_PATH = tmp_path / "fallback.db"

    application = create_app(PostgresConfig)
    assert DATABASE_EXTENSION_KEY in application.extensions
    database = application.extensions[DATABASE_EXTENSION_KEY]
    assert isinstance(database, Database)
    assert database.target.backend == "postgres"


def test_app_starts_without_database_url(tmp_path: Path) -> None:
    class NoDsnConfig(TestConfig):
        PERSISTENCE_BACKEND = "postgres"
        DATABASE_URL = ""
        DATABASE_PATH = tmp_path / "fallback.db"

    application = create_app(NoDsnConfig)
    database = application.extensions[DATABASE_EXTENSION_KEY]

    assert database.target.dsn is None
    with pytest.raises(PersistenceUnavailable):
        with database.connection():
            pytest.fail("Without DATABASE_URL no connection can be opened")


# ---------------------------------------------------------------------------
# TC-019-016 — startup without a database and lazy recovery (T4, RF-22/RF-23)
# ---------------------------------------------------------------------------


def _schema_tables(url: str, schema: str) -> set[str]:
    import psycopg

    with psycopg.connect(url, connect_timeout=5, autocommit=True) as conn:
        rows = conn.execute(
            """
            SELECT table_name
            FROM information_schema.tables
            WHERE table_schema = %s
            """,
            (schema,),
        ).fetchall()
    return {row[0] for row in rows}


def test_tc_019_016_startup_tolerates_outage_and_recovers(
    pg_schema, tmp_path: Path, caplog
) -> None:
    import psycopg

    from consultorio.persistence.database import _default_connect

    url, schema = pg_schema

    # Part A: create_app does not abort when the database is unreachable and a
    # page without persistence still responds (RF-22).
    class UnreachableConfig(TestConfig):
        PERSISTENCE_BACKEND = "postgres"
        DATABASE_URL = (
            "postgresql://consultorio_dev@127.0.0.1:1/consultorio_dev"
            "?sslmode=disable"
        )
        DATABASE_PATH: Path = tmp_path / "fallback.db"
        DATABASE_CONNECT_TIMEOUT = 1.0
        DATABASE_ACQUIRE_TIMEOUT = 1.0

    with caplog.at_level(logging.WARNING):
        application = create_app(UnreachableConfig)

    assert application.test_client().get("/").status_code == 200
    # The startup warning never leaks the DSN or the database user.
    assert "postgresql://" not in caplog.text
    assert "consultorio_dev" not in caplog.text

    # Part B: the database comes back. A factory that fails once and then
    # delegates to the real PostgreSQL connection simulates the recovery; the
    # next ensure_schema() retries without restarting the process (RF-23).
    target = DatabaseTarget(
        backend="postgres",
        dsn=url,
        schema=schema,
        connect_timeout=5.0,
        acquire_timeout=5.0,
        statement_timeout_ms=15000,
    )
    calls = {"count": 0}

    def flaky_connect(database_target: DatabaseTarget):
        calls["count"] += 1
        if calls["count"] == 1:
            raise psycopg.OperationalError("database unavailable")
        return _default_connect(database_target)

    database = Database(target, connect_factory=flaky_connect)

    with pytest.raises(PersistenceUnavailable):
        database.ensure_schema()
    assert _schema_tables(url, schema) == set()

    # No restart: the lazy retry applies the schema and works.
    database.ensure_schema()
    assert {"appointments", "automation_events", "schema_migrations"} <= (
        _schema_tables(url, schema)
    )
    with database.connection() as connection:
        assert connection.execute("SELECT 1 AS ok").fetchone()["ok"] == 1


# ---------------------------------------------------------------------------
# TC-019-010 — persistence outage: HTTP 503 and minimal UX (T9, RF-20/RF-21)
#
# The app is configured with a real PostgreSQL backend and an unreachable
# local DSN (127.0.0.1:1). The failure comes from the driver itself and is
# translated by the T3/T6 layers, so these tests exercise the real path from
# the route to ``PersistenceUnavailable`` and the T9 handler. No repository or
# service result is monkeypatched.
# ---------------------------------------------------------------------------

T9_DSN = (
    "postgresql://consultorio_dev:t9-secret-password@127.0.0.1:1/"
    "consultorio_dev?sslmode=disable"
)
T9_ADMIN_TOKEN = "t9-admin-token"
T9_DOCUMENT_NUMBER = "99887766"
T9_PATIENT_NAME = "Paciente T9"
T9_EMAIL = "t9-resilience@ejemplo.test"
T9_PHONE = "3000000000"


def _future_weekday() -> str:
    candidate = date.today()
    while candidate.weekday() >= 5:
        candidate += timedelta(days=1)
    return candidate.isoformat()


@pytest.fixture()
def unavailable_app(tmp_path: Path):
    """App with a real PostgreSQL target whose server does not exist."""

    class UnreachableConfig(TestConfig):
        PERSISTENCE_BACKEND = "postgres"
        DATABASE_URL = T9_DSN
        DATABASE_PATH: Path = tmp_path / "fallback.db"
        DATABASE_CONNECT_TIMEOUT = 1.0
        DATABASE_ACQUIRE_TIMEOUT = 1.0
        AUTOMATION_WEBHOOK_URL = ""
        CONSULTORIO_ADMIN_TOKEN = T9_ADMIN_TOKEN

    application = create_app(UnreachableConfig)
    application.config.update(TESTING=True)
    return application


def _valid_booking_data() -> dict[str, str]:
    return {
        "document_type": "CC",
        "document_number": T9_DOCUMENT_NUMBER,
        "patient_name": T9_PATIENT_NAME,
        "email": T9_EMAIL,
        "phone": T9_PHONE,
        "service": "nutrition",
        "date": _future_weekday(),
        "time": "08:00",
    }


def _assert_no_business_confusion(body: str) -> None:
    """The outage is never shown as a business result (RF-21)."""
    for literal in (
        MSG_SLOT_TAKEN,
        MSG_OCCUPIED_HOUR,
        MSG_VERIFICATION_FAILED,
        MSG_ALREADY_CANCELLED,
        ADMIN_APPOINTMENT_NOT_FOUND,
        ADMIN_MSG_ALREADY_CANCELLED,
    ):
        assert literal not in body, literal


def test_tc_019_010_html_booking_page_responds_503_with_literal(
    unavailable_app,
) -> None:
    response = unavailable_app.test_client().get("/citas")
    body = response.get_data(as_text=True)

    assert response.status_code == 503
    assert MSG_PERSISTENCE_UNAVAILABLE in body
    assert 'href="/citas"' in body
    assert ADMIN_BACK_BUTTON in body
    _assert_no_business_confusion(body)


def test_tc_019_010_hours_json_responds_503_with_approved_error(
    unavailable_app,
) -> None:
    response = unavailable_app.test_client().get(
        "/citas/horarios",
        query_string={"service": "nutrition", "date": _future_weekday()},
    )

    assert response.status_code == 503
    assert response.get_json() == {"error": MSG_PERSISTENCE_UNAVAILABLE}


def test_tc_019_010_availability_json_responds_503_with_approved_error(
    unavailable_app,
) -> None:
    response = unavailable_app.test_client().get(
        "/citas/disponibilidad",
        query_string={
            "service": "nutrition",
            "month": date.today().strftime("%Y-%m"),
        },
    )

    assert response.status_code == 503
    assert response.get_json() == {"error": MSG_PERSISTENCE_UNAVAILABLE}


def test_tc_019_010_post_booking_responds_503_without_confirmation(
    unavailable_app,
) -> None:
    response = unavailable_app.test_client().post(
        "/citas", data=_valid_booking_data()
    )
    body = response.get_data(as_text=True)

    assert response.status_code == 503
    assert response.status_code != 409
    assert "Location" not in response.headers
    assert "Cita registrada" not in body
    assert MSG_PERSISTENCE_UNAVAILABLE in body
    _assert_no_business_confusion(body)


def test_tc_019_010_confirmation_responds_503_not_404(
    unavailable_app,
) -> None:
    response = unavailable_app.test_client().get("/citas/confirmada/1")
    body = response.get_data(as_text=True)

    assert response.status_code == 503
    assert response.status_code != 404
    assert MSG_PERSISTENCE_UNAVAILABLE in body
    assert "Página no encontrada" not in body
    _assert_no_business_confusion(body)


def test_tc_019_010_cancellation_017_responds_503_not_business_result(
    unavailable_app,
) -> None:
    client = unavailable_app.test_client()

    verification = client.post(
        "/citas/cancelar/1", data={"document_number": T9_DOCUMENT_NUMBER}
    )
    confirmation = client.post(
        "/citas/cancelar/1/confirmar",
        data={"document_number": T9_DOCUMENT_NUMBER},
    )
    success = client.get("/citas/cancelar/1/exito")

    for response in (verification, confirmation, success):
        body = response.get_data(as_text=True)
        assert response.status_code == 503
        assert response.status_code != 303
        assert MSG_PERSISTENCE_UNAVAILABLE in body
        assert MSG_VERIFICATION_FAILED not in body
        assert MSG_ALREADY_CANCELLED not in body
        _assert_no_business_confusion(body)


def test_tc_019_010_admin_018_responds_503_not_missing_or_cancelled(
    unavailable_app,
) -> None:
    client = unavailable_app.test_client()
    headers = {"X-Admin-Token": T9_ADMIN_TOKEN}

    detail = client.get("/admin/citas/1", headers=headers)
    cancel = client.post("/admin/citas/1/cancelar", headers=headers)
    reschedule = client.post("/admin/citas/1/reprogramar", headers=headers)

    for response in (detail, cancel, reschedule):
        body = response.get_data(as_text=True)
        assert response.status_code == 503
        assert MSG_PERSISTENCE_UNAVAILABLE in body
        assert ADMIN_APPOINTMENT_NOT_FOUND not in body
        assert ADMIN_MSG_ALREADY_CANCELLED not in body
        _assert_no_business_confusion(body)


def test_tc_019_010_response_and_logs_have_no_dsn_or_pii(
    unavailable_app, caplog
) -> None:
    data = _valid_booking_data()
    with caplog.at_level(logging.WARNING):
        response = unavailable_app.test_client().post("/citas", data=data)

    body = response.get_data(as_text=True)
    assert response.status_code == 503

    for secret in (
        T9_DSN,
        "postgresql://",
        "t9-secret-password",
        "127.0.0.1:1",
        data["document_number"],
        data["patient_name"],
        data["email"],
        data["phone"],
    ):
        assert secret not in body

    for secret in (
        T9_DSN,
        "t9-secret-password",
        data["document_number"],
        data["patient_name"],
        data["email"],
        data["phone"],
    ):
        assert secret not in caplog.text


def test_tc_019_010_availability_template_and_js_show_unavailable_state(
    app,
) -> None:
    """The literal is served by the backend; the 503 branch paints no badge."""
    html = app.test_client().get("/citas").get_data(as_text=True)
    assert (
        f'data-unavailable-message="{MSG_PERSISTENCE_UNAVAILABLE}"' in html
    )

    js = (Config.STATIC_DIR / "js" / "availability.js").read_text(
        encoding="utf-8"
    )
    assert "data-unavailable-message" in js
    assert "function showUnavailable" in js
    start = js.index("function showUnavailable")
    end = js.index("function splitByBlock")
    unavailable_branch = js[start:end]
    assert "createTakenHour" not in unavailable_branch
    assert "data-occupied-label" not in unavailable_branch
    assert "data-unavailable-message" in unavailable_branch


def test_tc_019_010_404_405_500_handlers_still_work(app) -> None:
    application = app
    application.config["PROPAGATE_EXCEPTIONS"] = False

    @application.get("/_t9_internal_error")
    def _t9_internal_error():
        raise RuntimeError("T9 regression")

    client = application.test_client()

    not_found = client.get("/ruta-que-no-existe-t9")
    assert not_found.status_code == 404
    assert "Página no encontrada" in not_found.get_data(as_text=True)

    not_allowed = client.post("/")
    assert not_allowed.status_code == 405
    assert "Método no permitido" in not_allowed.get_data(as_text=True)

    internal = client.get("/_t9_internal_error")
    assert internal.status_code == 500
    assert "Error interno" in internal.get_data(as_text=True)
