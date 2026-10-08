import sys
from pathlib import Path
from typing import Iterator

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from consultorio import create_app
from consultorio.config import TestConfig
from consultorio.persistence.database import init_db


@pytest.fixture()
def app(tmp_path: Path) -> Iterator:
    class TempConfig(TestConfig):
        DATABASE_PATH: Path = tmp_path / "consultorio.db"

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
