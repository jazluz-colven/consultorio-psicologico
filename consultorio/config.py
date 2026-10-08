from pathlib import Path


class Config:
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    STATIC_DIR: Path = BASE_DIR / "static"
    TEMPLATES_DIR: Path = BASE_DIR / "templates"
    DATA_DIR: Path = BASE_DIR / "data"
    DATABASE_PATH: Path = DATA_DIR / "consultorio.db"
    SITE_NAME: str = "Carolina Gómez"
    TESTING: bool = False
    DEBUG: bool = False


class TestConfig(Config):
    TESTING: bool = True
    DEBUG: bool = False
