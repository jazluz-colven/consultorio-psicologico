from flask import Flask, render_template
from werkzeug.exceptions import HTTPException


class PersistenceUnavailable(Exception):
    """The persistence backend cannot serve the current operation (RF-22/23).

    This is a domain error, deliberately *not* an ``HTTPException``: the HTTP
    503 mapping and its user-facing message belong to T9 (Spec 019). Driver
    failures (``OperationalError``, ``InterfaceError``, connection/acquire
    timeouts, connection limit) are translated to this type so callers never
    confuse an outage with a booking conflict such as ``SLOT_TAKEN``.
    """


def handle_not_found(exception: HTTPException) -> tuple[str, int]:
    return render_template("errors/404.html"), 404


def handle_method_not_allowed(exception: HTTPException) -> tuple[str, int]:
    return render_template("errors/405.html"), 405


def handle_internal_error(exception: Exception) -> tuple[str, int]:
    return render_template("errors/500.html"), 500


def register_error_handlers(app: Flask) -> None:
    app.register_error_handler(404, handle_not_found)
    app.register_error_handler(405, handle_method_not_allowed)
    app.register_error_handler(500, handle_internal_error)
