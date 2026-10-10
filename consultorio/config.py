import os
from pathlib import Path

_DEFAULT_AUTOMATION_TIMEOUT_SECONDS: float = 3.0


def _parse_timeout_seconds(raw: str) -> float:
    try:
        parsed = float(raw)
    except ValueError:
        return _DEFAULT_AUTOMATION_TIMEOUT_SECONDS
    return parsed if parsed > 0 else _DEFAULT_AUTOMATION_TIMEOUT_SECONDS


class Config:
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STATIC_DIR: Path = BASE_DIR / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    DATA_DIR: Path = BASE_DIR / "data"
    DATABASE_PATH: Path = DATA_DIR / "consultorio.db"
    SITE_NAME: str = "Carolina Gómez"
    TESTING: bool = False
    DEBUG: bool = False
    # HU-007: n8n automation; empty URL = automation disabled (RF-2)
    AUTOMATION_WEBHOOK_URL: str = os.environ.get("AUTOMATION_WEBHOOK_URL", "")
    AUTOMATION_TIMEOUT_SECONDS: float = _parse_timeout_seconds(
        os.environ.get("AUTOMATION_TIMEOUT_SECONDS", "")
    )


class TestConfig(Config):
    TESTING: bool = True
    DEBUG: bool = False
