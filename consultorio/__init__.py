from typing import Any

from flask import Flask

from consultorio.config import Config


def create_app(settings: Any = None) -> Flask:
    app = Flask(
        __name__,
        static_folder=str(Config.STATIC_DIR),
        template_folder=str(Config.TEMPLATES_DIR),
    )
    app.config.from_object(Config)
    if settings is not None:
        app.config.from_object(settings)

    from consultorio.errors import register_error_handlers
    from consultorio.web.about import bp as about_bp
    from consultorio.web.home import bp as home_bp
    from consultorio.web.placeholders import bp as sections_bp
    from consultorio.web.search import bp as search_bp
    from consultorio.web.services import bp as services_bp

    app.register_blueprint(about_bp)
    app.register_blueprint(home_bp)
    app.register_blueprint(sections_bp)
    app.register_blueprint(search_bp)
    app.register_blueprint(services_bp)
    register_error_handlers(app)

    return app
