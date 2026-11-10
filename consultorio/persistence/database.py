"""Persistence connections, schema bootstrap and domain error translation.

The module keeps the original SQLite helpers (``get_connection``/``init_db``)
untouched for the current application and rollback route. HU-019 adds the
``DatabaseTarget``/``Database`` layer that owns connection lifecycle:

* at most one connection per Flask app context, reused and closed on teardown;
* one connection per operation outside an app context;
* a per-instance ``BoundedSemaphore`` that caps concurrency and raises
  ``PersistenceUnavailable`` when a permit cannot be acquired in time;
* transactions that commit once or roll back completely;
* lazy schema initialization: explicit PostgreSQL DDL (no ORM) and the
  unchanged SQLite rollback DDL.

Transitional coexistence (Spec 019, until T5/T6): the repositories and services
still read/write SQLite through ``DATABASE_PATH``. ``create_app`` keeps calling
``init_db`` for them *and* attempts the PostgreSQL bootstrap when the backend is
``postgres``; the latter never aborts startup (RF-22). The PostgreSQL DDL does
not replace the SQLite one, so the current suite keeps working while the data
layer is migrated task by task.

No connection is created at import time or when constructing ``Database``.
"""

import shutil
import sqlite3
import threading
from contextlib import contextmanager
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Iterator, Mapping

from flask import g, has_app_context

from consultorio.errors import PersistenceUnavailable

# HU-010 (spec 010 amended 2026-10-13): the inline UNIQUE (service, date, time)
# is replaced by a partial unique index that ignores cancelled appointments, so
# a cancelled slot can be booked again while live slots stay unique (RF-4).
# Spec 019 (D7, RF-30): the rollback route stores ``created_at`` in UTC too.
# ``datetime('now')`` in SQLite is UTC and yields the approved
# ``YYYY-MM-DD HH:MM:SS`` format, matching the PostgreSQL DDL.
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
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS automation_events (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    event_id        TEXT NOT NULL UNIQUE,
    event_type      TEXT NOT NULL,
    event_version   INTEGER NOT NULL,
    appointment_id  INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    detail          TEXT,
    created_at      TEXT NOT NULL DEFAULT (datetime('now')),
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
    created_at      TEXT NOT NULL DEFAULT (datetime('now'))
)
"""

PARTIAL_INDEX_NAME = "ux_appointments_slot_open"
_PARTIAL_INDEX_SQL = (
    f"CREATE UNIQUE INDEX IF NOT EXISTS {PARTIAL_INDEX_NAME} "
    "ON appointments(service, date, time) WHERE status <> 'cancelled'"
)

# ---------------------------------------------------------------------------
# PostgreSQL DDL (Spec 019, D4 and plan §3.1). Explicit SQL, no ORM.
#
# The schema is applied step by step inside a single transaction that starts
# with ``pg_advisory_xact_lock`` so concurrent instances serialize their
# bootstrap (CL-7). Every step is additive/idempotent and its version is
# recorded in ``schema_migrations`` with ``ON CONFLICT DO NOTHING``.
# ---------------------------------------------------------------------------

PG_SCHEMA_MIGRATIONS_SQL = """
CREATE TABLE IF NOT EXISTS schema_migrations (
    version     INTEGER PRIMARY KEY,
    applied_at  TEXT NOT NULL
        DEFAULT (to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))
)
"""

PG_APPOINTMENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS appointments (
    id              BIGSERIAL PRIMARY KEY,
    document_type   TEXT NOT NULL,
    document_number TEXT NOT NULL,
    patient_name    TEXT NOT NULL,
    email           TEXT NOT NULL,
    phone           TEXT NOT NULL,
    service         TEXT NOT NULL,
    date            TEXT NOT NULL,
    time            TEXT NOT NULL,
    status          TEXT NOT NULL DEFAULT 'confirmed',
    created_at      TEXT NOT NULL
        DEFAULT (to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS'))
)
"""

PG_AUTOMATION_EVENTS_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS automation_events (
    id              BIGSERIAL PRIMARY KEY,
    event_id        TEXT NOT NULL UNIQUE,
    event_type      TEXT NOT NULL,
    event_version   INTEGER NOT NULL,
    appointment_id  INTEGER NOT NULL,
    status          TEXT NOT NULL DEFAULT 'pending',
    detail          TEXT,
    created_at      TEXT NOT NULL
        DEFAULT (to_char(now() AT TIME ZONE 'UTC', 'YYYY-MM-DD HH24:MI:SS')),
    sent_at         TEXT
)
"""

PG_PARTIAL_INDEX_SQL = f"""
CREATE UNIQUE INDEX IF NOT EXISTS {PARTIAL_INDEX_NAME}
    ON appointments(service, date, time)
    WHERE status <> 'cancelled'
"""

PG_ADVISORY_LOCK_ID = 719019

# Ordered, additive and idempotent schema steps. The version is stored in
# ``schema_migrations`` so future changes can be tracked without an ORM.
PG_SCHEMA_STEPS: tuple[tuple[int, str], ...] = (
    (1, PG_SCHEMA_MIGRATIONS_SQL),
    (2, PG_APPOINTMENTS_TABLE_SQL),
    (3, PG_AUTOMATION_EVENTS_TABLE_SQL),
    (4, PG_PARTIAL_INDEX_SQL),
)


def _is_valid_schema_identifier(value: str) -> bool:
    """Return True for a simple unquoted SQL identifier.

    ``target.schema`` is a test-only search_path; it is embedded in libpq's
    ``options`` string, so anything beyond ``[A-Za-z_][A-Za-z0-9_]*`` is
    rejected to prevent SQL injection.
    """
    if not value or not value.isascii():
        return False
    first = value[0]
    if not (first.isalpha() or first == "_"):
        return False
    return all(character.isalnum() or character == "_" for character in value)


_REQUEST_STATES_ATTR = "_consultorio_database_states"

_DEFAULT_MAX_CONNECTIONS = 5
_DEFAULT_CONNECT_TIMEOUT = 10.0
_DEFAULT_ACQUIRE_TIMEOUT = 5.0
_DEFAULT_STATEMENT_TIMEOUT_MS = 15000


def _psycopg_unavailable_errors() -> tuple[type[BaseException], ...]:
    """Return the real driver base classes that mean "database unavailable".

    ``psycopg`` is imported lazily so importing this module never requires libpq
    (SQLite route and tests keep working). ``isinstance`` against
    ``OperationalError``/``InterfaceError`` recognises real subclasses such as
    ``CannotConnectNow``, ``AdminShutdown``, ``ConnectionFailure`` or
    ``ConnectionTimeout``. ``UniqueViolation``/``IntegrityError`` are
    deliberately excluded: integrity conflicts belong to the repositories and
    services (T5/T6), never to an outage.
    """
    try:
        import psycopg
    except ImportError:  # pragma: no cover - depends on local libpq
        return ()
    return (psycopg.OperationalError, psycopg.InterfaceError)


def is_slot_uniqueness_violation(error: BaseException) -> bool:
    """True only for the appointments slot unique-index violation (D6).

    ``create_booking()`` uses this classifier to map a lost insert race to
    ``SLOT_TAKEN``. Driver outage errors are not integrity errors and never
    reach this branch; other integrity failures (or a different constraint)
    return ``False`` so they keep propagating. The driver is imported lazily so
    the SQLite rollback route never requires libpq.
    """
    if isinstance(error, sqlite3.IntegrityError):
        # SQLite does not expose the index name; the message lists the unique
        # columns of ``ux_appointments_slot_open``.
        return (
            "UNIQUE constraint failed: appointments.service, "
            "appointments.date, appointments.time" in str(error)
        )
    try:
        from psycopg import errors as pg_errors
    except ImportError:  # pragma: no cover - depends on local libpq
        return False
    if not isinstance(error, pg_errors.UniqueViolation):
        return False
    # The partial unique index is the only unique slot constraint; a different
    # named constraint is not a slot conflict.
    constraint = getattr(getattr(error, "diag", None), "constraint_name", None)
    return constraint == PARTIAL_INDEX_NAME


def is_persistence_unavailable(error: BaseException) -> bool:
    """True for driver errors that mean the store cannot serve the operation.

    Plan D6 maps SQLite ``OperationalError``/``InterfaceError`` and psycopg
    ``OperationalError``/``InterfaceError`` (including connection timeouts) to
    ``PersistenceUnavailable``. Integrity errors are deliberately excluded:
    the slot conflict is classified separately and never becomes an outage.
    """
    if isinstance(error, PersistenceUnavailable):
        return True
    if isinstance(error, (sqlite3.OperationalError, sqlite3.InterfaceError)):
        return True
    unavailable = _psycopg_unavailable_errors()
    return bool(unavailable) and isinstance(error, unavailable)


def translate_persistence_error(error: BaseException) -> BaseException:
    """Translate only driver unavailability; return anything else unchanged.

    Services use this at the persistence boundary (D6) so they never import a
    driver. A ``PersistenceUnavailable`` is returned as-is to avoid double
    wrapping; programming errors and integrity conflicts keep their type.
    """
    if isinstance(error, PersistenceUnavailable):
        return error
    if is_persistence_unavailable(error):
        return PersistenceUnavailable("La base de datos no está disponible.")
    return error


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


def apply_postgres_schema(connection: Any) -> None:
    """Apply the PostgreSQL schema under an advisory transaction lock.

    Must run inside a transaction: ``pg_advisory_xact_lock`` is released on
    commit/rollback, so two instances that start together serialize their
    bootstrap instead of racing on ``CREATE TABLE`` (CL-7). Each step is
    idempotent and recorded in ``schema_migrations`` with
    ``ON CONFLICT DO NOTHING``. A failure rolls back the whole batch, so a
    partially applied schema never gets a migration marker.
    """
    connection.execute(
        "SELECT pg_advisory_xact_lock(%s)", (PG_ADVISORY_LOCK_ID,)
    )
    for version, statement in PG_SCHEMA_STEPS:
        connection.execute(statement)
        connection.execute(
            "INSERT INTO schema_migrations (version) VALUES (%s) "
            "ON CONFLICT DO NOTHING",
            (version,),
        )


@dataclass(frozen=True)
class DatabaseTarget:
    """Where and how to connect, without opening a connection.

    ``dsn`` is excluded from the generated ``repr`` and replaced by ``<set>`` in
    the explicit one so a DSN with credentials never leaks into logs.
    """

    backend: str = "postgres"
    dsn: str | None = field(default=None, repr=False)
    sqlite_path: Path | None = None
    schema: str | None = None  # isolated schema for tests; None in production
    max_connections: int = _DEFAULT_MAX_CONNECTIONS
    connect_timeout: float = _DEFAULT_CONNECT_TIMEOUT
    acquire_timeout: float = _DEFAULT_ACQUIRE_TIMEOUT
    statement_timeout_ms: int = _DEFAULT_STATEMENT_TIMEOUT_MS

    def __post_init__(self) -> None:
        if self.backend not in {"postgres", "sqlite"}:
            raise ValueError(
                "DatabaseTarget.backend debe ser 'postgres' o 'sqlite'; "
                f"valor recibido: {self.backend!r}"
            )
        if self.max_connections <= 0:
            raise ValueError("max_connections debe ser mayor que cero.")
        if self.connect_timeout <= 0:
            raise ValueError("connect_timeout debe ser mayor que cero.")
        if self.acquire_timeout <= 0:
            raise ValueError("acquire_timeout debe ser mayor que cero.")
        if self.statement_timeout_ms <= 0:
            raise ValueError("statement_timeout_ms debe ser mayor que cero.")

    @classmethod
    def from_config(cls, config: Mapping[str, Any] | Any) -> "DatabaseTarget":
        """Build a target from ``Config``/``app.config`` without new defaults."""

        def read(name: str, default: Any = None) -> Any:
            if isinstance(config, Mapping):
                return config.get(name, default)
            return getattr(config, name, default)

        backend = str(read("PERSISTENCE_BACKEND", "postgres")).strip().lower()
        raw_dsn = read("DATABASE_URL", "") or ""
        dsn = str(raw_dsn) if raw_dsn else None
        raw_sqlite_path = (
            read("DATABASE_PATH") if backend == "sqlite" else None
        )
        return cls(
            backend=backend,
            dsn=dsn,
            sqlite_path=(
                Path(raw_sqlite_path) if raw_sqlite_path is not None else None
            ),
            schema=None,
            max_connections=int(
                read("DATABASE_MAX_CONNECTIONS", _DEFAULT_MAX_CONNECTIONS)
            ),
            connect_timeout=float(
                read("DATABASE_CONNECT_TIMEOUT", _DEFAULT_CONNECT_TIMEOUT)
            ),
            acquire_timeout=float(
                read("DATABASE_ACQUIRE_TIMEOUT", _DEFAULT_ACQUIRE_TIMEOUT)
            ),
            statement_timeout_ms=int(
                read(
                    "DATABASE_STATEMENT_TIMEOUT_MS",
                    _DEFAULT_STATEMENT_TIMEOUT_MS,
                )
            ),
        )

    def __repr__(self) -> str:
        return (
            "DatabaseTarget("
            f"backend={self.backend!r}, "
            f"dsn={'<set>' if self.dsn else None!r}, "
            f"sqlite_path={self.sqlite_path!r}, "
            f"schema={self.schema!r}, "
            f"max_connections={self.max_connections!r}, "
            f"connect_timeout={self.connect_timeout!r}, "
            f"acquire_timeout={self.acquire_timeout!r}, "
            f"statement_timeout_ms={self.statement_timeout_ms!r})"
        )


class _RequestState:
    """Connection owned by the current Flask app context."""

    __slots__ = ("connection",)

    def __init__(self, connection: Any) -> None:
        self.connection = connection


class Database:
    """Connection facade for SQLite/PostgreSQL.

    Construction is side-effect free: it only captures the target, the
    connection factory and a per-instance semaphore. The first ``connection()``
    or ``transaction()`` call is what opens a connection.
    """

    def __init__(
        self,
        target: DatabaseTarget,
        *,
        connect_factory: Callable[[DatabaseTarget], Any] | None = None,
        driver_errors: tuple[type[BaseException], ...] = (),
    ) -> None:
        self._target = target
        self._connect_factory = connect_factory or _default_connect
        # Additional exception types (test fakes) treated like driver outages.
        self._driver_errors = driver_errors
        self._semaphore = threading.BoundedSemaphore(target.max_connections)
        self._schema_lock = threading.Lock()
        self._schema_ready = False

    @property
    def target(self) -> DatabaseTarget:
        return self._target

    def __repr__(self) -> str:
        return f"Database(target={self._target!r})"

    # -- connection lifecycle -------------------------------------------------

    @contextmanager
    def connection(self) -> Iterator[Any]:
        """Yield a connection.

        Inside a Flask app context the connection is opened once, stored in
        ``flask.g`` and reused; it is *not* closed when this ``with`` block
        exits. ``close_request()`` closes it at app-context teardown. Outside an
        app context every block opens and closes its own connection.
        """
        if has_app_context():
            state = self._get_request_state()
            if state is not None:
                try:
                    yield state.connection
                except BaseException as exc:
                    translated = self._translate_driver_error(exc)
                    if translated is not exc:
                        raise translated from exc
                    raise
                return
            connection = self._open_connection()
            self._set_request_state(_RequestState(connection))
            try:
                yield connection
            except BaseException as exc:
                translated = self._translate_driver_error(exc)
                if translated is not exc:
                    raise translated from exc
                raise
            return

        connection = self._open_connection()
        try:
            yield connection
        except BaseException as exc:
            translated = self._translate_driver_error(exc)
            if translated is not exc:
                raise translated from exc
            raise
        finally:
            self._close_connection(connection)

    @contextmanager
    def transaction(self) -> Iterator[Any]:
        """Yield a connection whose work commits once or rolls back fully."""
        if has_app_context():
            state = self._get_request_state()
            if state is None:
                connection = self._open_connection()
                self._set_request_state(_RequestState(connection))
            else:
                connection = state.connection
            with self._transaction_scope(connection):
                yield connection
            return

        connection = self._open_connection()
        try:
            with self._transaction_scope(connection):
                yield connection
        finally:
            self._close_connection(connection)

    def close_request(self) -> None:
        """Close the app-context connection and release its permit.

        Idempotent and safe to call from ``teardown_appcontext`` even when no
        connection was ever opened.
        """
        if not has_app_context():
            return
        state = self._pop_request_state()
        if state is None:
            return
        self._close_connection(state.connection)

    # -- schema ---------------------------------------------------------------

    def ensure_schema(self) -> None:
        """Apply the schema lazily (once per process) with a lock.

        SQLite delegates to the existing ``init_db``. PostgreSQL applies the
        explicit DDL in one advisory-locked transaction. The ready flag is set
        only after a successful commit: if the database is unavailable the
        exception propagates and the next call retries without a restart
        (RF-22, RF-23). There is no background retry loop.
        """
        if self._schema_ready:
            return
        with self._schema_lock:
            if self._schema_ready:
                return
            if self._target.backend == "sqlite":
                if self._target.sqlite_path is None:
                    raise PersistenceUnavailable(
                        "No se ha configurado la base de datos SQLite."
                    )
                init_db(self._target.sqlite_path)
                self._schema_ready = True
                return
            if not self._target.dsn:
                # Same domain error as an unreachable server: startup must not
                # abort and persistence routes report unavailability.
                raise PersistenceUnavailable(
                    "No se ha configurado DATABASE_URL."
                )
            # ``transaction`` commits once or rolls back completely and
            # translates driver outages to ``PersistenceUnavailable``.
            with self.transaction() as connection:
                apply_postgres_schema(connection)
            self._schema_ready = True

    # -- internals ------------------------------------------------------------

    @contextmanager
    def _transaction_scope(self, connection: Any) -> Iterator[None]:
        try:
            yield
        except BaseException as exc:
            rollback_error = self._rollback_quietly(connection)
            self._raise_translated(exc, rollback_error)
        try:
            connection.commit()
        except BaseException as exc:
            rollback_error = self._rollback_quietly(connection)
            self._raise_translated(exc, rollback_error)

    @staticmethod
    def _rollback_quietly(connection: Any) -> BaseException | None:
        """Roll back during cleanup, returning (not raising) any failure."""
        try:
            connection.rollback()
        except BaseException as exc:  # noqa: BLE001 - must not mask the original
            return exc
        return None

    def _raise_translated(
        self, exc: BaseException, cleanup_error: BaseException | None = None
    ) -> None:
        """Re-raise ``exc`` translated to a domain outage when it is one.

        A driver failure during the operation, the commit or the rollback is
        translated exactly once to ``PersistenceUnavailable``. Non-driver
        failures keep their original type. ``PersistenceUnavailable`` is never
        wrapped twice.
        """
        if isinstance(exc, PersistenceUnavailable):
            raise exc
        translated = self._translate_driver_error(exc)
        if translated is not exc:
            raise translated from exc
        if cleanup_error is not None:
            translated_cleanup = self._translate_driver_error(cleanup_error)
            if translated_cleanup is not cleanup_error:
                raise translated_cleanup from cleanup_error
        raise exc

    def _translate_driver_error(self, exc: BaseException) -> BaseException:
        if isinstance(exc, PersistenceUnavailable):
            return exc
        if self._is_unavailable_error(exc):
            return PersistenceUnavailable(
                "La base de datos no está disponible."
            )
        return exc

    def _open_connection(self) -> Any:
        timeout = self._target.acquire_timeout
        if not self._semaphore.acquire(timeout=timeout):
            raise PersistenceUnavailable(
                "No se pudo obtener una conexión a la base de datos a tiempo."
            )
        try:
            return self._connect_factory(self._target)
        except BaseException as exc:
            self._semaphore.release()
            translated = self._translate_driver_error(exc)
            if translated is not exc:
                raise translated from exc
            raise

    def _close_connection(self, connection: Any) -> None:
        try:
            connection.close()
        except Exception:
            # Closing is best-effort; the permit must still be released.
            pass
        finally:
            self._semaphore.release()

    def _is_unavailable_error(self, exc: BaseException) -> bool:
        if self._driver_errors and isinstance(exc, self._driver_errors):
            return True
        return is_persistence_unavailable(exc)

    def _get_request_state(self) -> _RequestState | None:
        states = getattr(g, _REQUEST_STATES_ATTR, None)
        if not isinstance(states, dict):
            return None
        return states.get(id(self))

    def _set_request_state(self, state: _RequestState) -> None:
        states = getattr(g, _REQUEST_STATES_ATTR, None)
        if not isinstance(states, dict):
            states = {}
            setattr(g, _REQUEST_STATES_ATTR, states)
        states[id(self)] = state

    def _pop_request_state(self) -> _RequestState | None:
        states = getattr(g, _REQUEST_STATES_ATTR, None)
        if not isinstance(states, dict):
            return None
        return states.pop(id(self), None)


def _default_connect(target: DatabaseTarget) -> Any:
    """Open a connection using the configured backend.

    PostgreSQL imports ``psycopg`` lazily so importing this module never
    requires libpq to be available (tests and the SQLite route keep working).
    """
    if target.backend == "sqlite":
        if target.sqlite_path is None:
            raise PersistenceUnavailable(
                "No se ha configurado la base de datos SQLite."
            )
        connection = sqlite3.connect(
            str(target.sqlite_path), timeout=target.connect_timeout
        )
        connection.row_factory = sqlite3.Row
        return connection

    if not target.dsn:
        raise PersistenceUnavailable("No se ha configurado DATABASE_URL.")

    try:
        import psycopg
        from psycopg.rows import dict_row
    except ImportError as exc:  # pragma: no cover - depends on local libpq
        raise PersistenceUnavailable(
            "El driver PostgreSQL no está disponible."
        ) from exc

    connect_kwargs: dict[str, Any] = {
        "connect_timeout": target.connect_timeout,
        "autocommit": False,
        "row_factory": dict_row,
        "application_name": "consultorio-web",
    }
    options: list[str] = []
    if target.statement_timeout_ms > 0:
        options.append(
            f"-c statement_timeout={target.statement_timeout_ms}"
        )
    if target.schema:
        # Test-only isolated schema. Production leaves ``schema`` as None.
        if not _is_valid_schema_identifier(target.schema):
            raise ValueError(
                "DatabaseTarget.schema debe ser un identificador SQL simple."
            )
        options.append(f"-c search_path={target.schema}")
    if options:
        connect_kwargs["options"] = " ".join(options)
    return psycopg.connect(target.dsn, **connect_kwargs)
