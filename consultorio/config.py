import os
from pathlib import Path
from urllib.parse import parse_qs, urlsplit

_DEFAULT_AUTOMATION_TIMEOUT_SECONDS: float = 3.0
_DEFAULT_DATABASE_MAX_CONNECTIONS: int = 5
_DEFAULT_DATABASE_CONNECT_TIMEOUT: float = 10.0
_DEFAULT_DATABASE_ACQUIRE_TIMEOUT: float = 5.0
_DEFAULT_DATABASE_STATEMENT_TIMEOUT_MS: int = 15000

_PERSISTENCE_BACKENDS: frozenset[str] = frozenset({"postgres", "sqlite"})
_LOCAL_DATABASE_HOSTS: frozenset[str] = frozenset(
    {"localhost", "127.0.0.1", "::1"}
)
_REQUIRED_TLS_SSLMODES: frozenset[str] = frozenset(
    {"require", "verify-ca", "verify-full"}
)


def _parse_timeout_seconds(raw: str) -> float:
    try:
        parsed = float(raw)
    except ValueError:
        return _DEFAULT_AUTOMATION_TIMEOUT_SECONDS
    return parsed if parsed > 0 else _DEFAULT_AUTOMATION_TIMEOUT_SECONDS


def _parse_database_path(raw: str, default: Path) -> Path:
    if not raw:
        return default
    path = Path(raw)
    return path if path.is_absolute() else Path.cwd() / path


def _parse_persistence_backend(raw: str) -> str:
    """Validate the persistence switch; only postgres/sqlite are accepted."""
    backend = raw.strip().lower()
    if backend not in _PERSISTENCE_BACKENDS:
        raise ValueError(
            "PERSISTENCE_BACKEND debe ser 'postgres' o 'sqlite'; "
            f"valor recibido: {raw!r}"
        )
    return backend


def _parse_positive_int(raw: str, default: int) -> int:
    """Fall back to a safe default for invalid or non-positive limits."""
    try:
        parsed = int(raw.strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _parse_positive_float(raw: str, default: float) -> float:
    """Fall back to a safe default for invalid or non-positive timeouts."""
    try:
        parsed = float(raw.strip())
    except (TypeError, ValueError):
        return default
    return parsed if parsed > 0 else default


def _validate_postgres_tls(backend: str, database_url: str) -> None:
    """Require TLS for non-local PostgreSQL DSNs without exposing the DSN."""
    if backend != "postgres" or not database_url:
        return
    try:
        parsed = urlsplit(database_url)
    except ValueError as exc:
        raise ValueError("DATABASE_URL no es una URL válida.") from exc
    if parsed.scheme not in {"postgresql", "postgres"}:
        raise ValueError(
            "DATABASE_URL debe usar el esquema postgresql:// o postgres://."
        )
    if parsed.hostname in _LOCAL_DATABASE_HOSTS:
        return
    sslmode = parse_qs(parsed.query).get("sslmode", [""])[0].strip().lower()
    if sslmode not in _REQUIRED_TLS_SSLMODES:
        raise ValueError(
            "DATABASE_URL de un host no local exige sslmode=require, "
            "verify-ca o verify-full."
        )


class Config:
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STATIC_DIR: Path = BASE_DIR / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    DATA_DIR: Path = BASE_DIR / "data"
    # HU-019 D2: PostgreSQL es el backend por defecto. Un valor distinto de
    # postgres/sqlite es un error de configuración, para no volver en silencio
    # al almacenamiento anterior ni dividir los datos.
    PERSISTENCE_BACKEND: str = _parse_persistence_backend(
        os.environ.get("PERSISTENCE_BACKEND", "postgres")
    )
    # HU-019 D2: DSN por entorno; nunca se registra ni se expone. Vacío no
    # aborta el arranque (RF-22): las rutas de persistencia responderán
    # indisponibilidad en tareas posteriores.
    DATABASE_URL: str = os.environ.get("DATABASE_URL", "")
    # HU-019 D10: DATABASE_PATH se conserva solo para el rollback temporal con
    # PERSISTENCE_BACKEND=sqlite. No es la configuración principal.
    DATABASE_PATH: Path = _parse_database_path(
        os.environ.get("DATABASE_PATH", ""),
        DATA_DIR / "consultorio.db",
    )
    # HU-019 D2/D3: protecciones operativas, no umbrales de negocio. Un valor
    # inválido o no positivo cae al default seguro (misma estrategia que
    # AUTOMATION_TIMEOUT_SECONDS) para no impedir el arranque por una variable
    # operativa mal escrita.
    DATABASE_MAX_CONNECTIONS: int = _parse_positive_int(
        os.environ.get("DATABASE_MAX_CONNECTIONS", ""),
        _DEFAULT_DATABASE_MAX_CONNECTIONS,
    )
    DATABASE_CONNECT_TIMEOUT: float = _parse_positive_float(
        os.environ.get("DATABASE_CONNECT_TIMEOUT", ""),
        _DEFAULT_DATABASE_CONNECT_TIMEOUT,
    )
    DATABASE_ACQUIRE_TIMEOUT: float = _parse_positive_float(
        os.environ.get("DATABASE_ACQUIRE_TIMEOUT", ""),
        _DEFAULT_DATABASE_ACQUIRE_TIMEOUT,
    )
    DATABASE_STATEMENT_TIMEOUT_MS: int = _parse_positive_int(
        os.environ.get("DATABASE_STATEMENT_TIMEOUT_MS", ""),
        _DEFAULT_DATABASE_STATEMENT_TIMEOUT_MS,
    )
    # Valida TLS al importar el módulo. Con backend sqlite se ignora.
    _validate_postgres_tls(PERSISTENCE_BACKEND, DATABASE_URL)
    SITE_NAME: str = "Carolina Gómez"
    TESTING: bool = False
    DEBUG: bool = False
    # HU-007: n8n automation; empty URL = automation disabled (RF-2)
    AUTOMATION_WEBHOOK_URL: str = os.environ.get("AUTOMATION_WEBHOOK_URL", "")
    AUTOMATION_TIMEOUT_SECONDS: float = _parse_timeout_seconds(
        os.environ.get("AUTOMATION_TIMEOUT_SECONDS", "")
    )
    # HU-007 enmienda 2 (Q7/D14): optional auth header "Name: value"; empty = none.
    # The token is an environment secret: never commit it to the repository.
    AUTOMATION_WEBHOOK_AUTH_HEADER: str = os.environ.get(
        "AUTOMATION_WEBHOOK_AUTH_HEADER", ""
    )
    # HU-018 (spec 018, D9): admin token only by environment variable; empty
    # disables the admin surface. Never commit a real token to the repository.
    CONSULTORIO_ADMIN_TOKEN: str = os.environ.get(
        "CONSULTORIO_ADMIN_TOKEN", ""
    )


class TestConfig(Config):
    TESTING: bool = True
    DEBUG: bool = False
    # Spec 019 T6: the general suite stays on SQLite during the transition;
    # PostgreSQL is exercised explicitly in the dedicated tests.
    PERSISTENCE_BACKEND: str = "sqlite"
