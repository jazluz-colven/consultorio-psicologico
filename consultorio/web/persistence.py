"""Application-scoped persistence resource for the web layer (plan D13).

``create_app()`` builds the single :class:`Database` instance from
``DATABASE_URL`` and registers it under ``DATABASE_EXTENSION_KEY``. Routes
resolve it here instead of building their own connections.
"""

from flask import current_app

from consultorio import DATABASE_EXTENSION_KEY
from consultorio.persistence.database import Database


def get_database() -> Database:
    """Return the ``Database`` built by ``create_app()`` for this application."""
    return current_app.extensions[DATABASE_EXTENSION_KEY]
