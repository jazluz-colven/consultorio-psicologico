from typing import Any

from flask import Flask

from consultorio.config import Config

# Stable extension key so tests, blueprints and future tasks can reach the
# persistence facade without importing a global/worker connection.
DATABASE_EXTENSION_KEY = "consultorio.database"


def create_app(settings: Any = None) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(Config.STATIC_DIR),
        template_folder=str(Config.TEMPLATES_DIR),
    )
    app.config.from_object(Config)
    if settings is not None:
        app.config.from_object(settings)

    from consultorio.errors import PersistenceUnavailable, register_error_handlers
    from consultorio.persistence.database import (
        Database,
        DatabaseTarget,
        init_db,
    )
    from consultorio.web.about import bp as about_bp
    from consultorio.web.admin import bp as admin_bp
    from consultorio.web.appointments import bp as appointments_bp
    from consultorio.web.cancellation import bp as cancellation_bp
    from consultorio.web.contact import bp as contact_bp
    from consultorio.web.home import bp as home_bp
    from consultorio.web.placeholders import bp as sections_bp
    from consultorio.web.search import bp as search_bp
    from consultorio.web.services import bp as services_bp

    app.register_blueprint(about_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(appointments_bp)
    app.register_blueprint(cancellation_bp)
    app.register_blueprint(contact_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(sections_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(services_bp)

    # HU-019 T3: side-effect free facade. No connection is opened here, so the
    # app still starts when PostgreSQL/DSN is unavailable (RF-22). The real
    # migration of repositories to this object happens in T4/T5.
    database = Database(DatabaseTarget.from_config(app.config))
    app.extensions[DATABASE_EXTENSION_KEY] = database

    def _close_request_database(_exception: BaseException | None = None) -> None:
        configured = app.extensions.get(DATABASE_EXTENSION_KEY)
        if configured is not None:
            configured.close_request()

    app.teardown_appcontext(_close_request_database)

    register_error_handlers(app)

    # Transitional coexistence (Spec 019, until T5/T6): the current
    # repositories and services still use DATABASE_PATH/SQLite, so its schema
    # keeps being initialized. The PostgreSQL DDL does not replace it.
    init_db(app.config["DATABASE_PATH"])

    # Spec 019 D14/RF-22: try the PostgreSQL bootstrap at startup but never
    # abort the process if the database is unavailable. ``ensure_schema`` is
    # lazy too, so the next persistence operation retries without a restart.
    try:
        database.ensure_schema()
    except PersistenceUnavailable:
        # Constant message: no DSN, credentials or PII in the log.
        app.logger.warning(
            "No se pudo inicializar el esquema de PostgreSQL al arrancar; "
            "se reintentará en la primera operación de persistencia."
        )

    return app
