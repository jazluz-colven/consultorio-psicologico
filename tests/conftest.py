import sys
from pathlib import Path
from typing import Iterator

import pytest

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from consultorio import create_app
from consultorio.config import TestConfig


@pytest.fixture()
def app() -> Iterator:
    application = create_app(TestConfig)
    application.config.update(TESTING=True)
    yield application


@pytest.fixture()
def client(app) -> object:
    return app.test_client()
