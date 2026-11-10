"""HTTP error handlers.

``PersistenceUnavailable`` is a domain error raised when the database cannot
serve the operation (Spec 019, D6). It is mapped to HTTP 503 with the approved
literal; it must never be presented as a business result (busy slot, missing
appointment or cancelled appointment).
"""

from flask import (
    Flask,
    Response,
    current_app,
    jsonify,
    render_template,
    request,
)
from werkzeug.exceptions import HTTPException

from consultorio.content.admin_content import ADMIN_BACK_BUTTON
from consultorio.content.appointment_content import MSG_PERSISTENCE_UNAVAILABLE

# JSON consumers of the availability endpoints (``availability.js``). The
# decision is based on the endpoint name, not on the ``Accept`` header, so it
# is deterministic for both tests and browsers.
_JSON_ENDPOINTS: frozenset[str] = frozenset(
    {"appointments.horarios", "appointments.disponibilidad"}
)


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


def handle_persistence_unavailable(
    exception: PersistenceUnavailable,
) -> tuple[Response | str, int]:
    """Map a database outage to 503 without leaking DSN or patient data.

    The log message is constant: the exception text, the request body and the
    target DSN are never written (RNF-6). HTML surfaces render the approved
    literal and a link back to the booking page; the two availability JSON
    endpoints keep their JSON contract.
    """
    current_app.logger.warning(
        "Solicitud no atendida: la base de datos no está disponible."
    )
    if request.endpoint in _JSON_ENDPOINTS:
        return jsonify({"error": MSG_PERSISTENCE_UNAVAILABLE}), 503
    return (
        render_template(
            "errors/persistence_unavailable.html",
            message=MSG_PERSISTENCE_UNAVAILABLE,
            back_label=ADMIN_BACK_BUTTON,
        ),
        503,
    )


def register_error_handlers(app: Flask) -> None:
    app.register_error_handler(404, handle_not_found)
    app.register_error_handler(405, handle_method_not_allowed)
    app.register_error_handler(500, handle_internal_error)
    app.register_error_handler(
        PersistenceUnavailable, handle_persistence_unavailable
    )
