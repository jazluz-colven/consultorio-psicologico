"""Application-scoped persistence resource for the web layer (plan D13).

``create_app()`` builds the single :class:`Database` instance from
``PERSISTENCE_BACKEND`` and registers it under ``DATABASE_EXTENSION_KEY``.
Routes resolve it here instead of rebuilding a path from ``DATABASE_PATH``,
which keeps SQLite as a test/rollback option while production uses PostgreSQL.
"""

from flask import current_app

from consultorio import DATABASE_EXTENSION_KEY
from consultorio.persistence.database import Database


def get_database() -> Database:
    """Return the ``Database`` built by ``create_app()`` for this application."""
    return current_app.extensions[DATABASE_EXTENSION_KEY]
