"""Automation event constants (HU-007); identifiers in English, texts in Spanish."""

EVENT_TYPE: str = "appointment.confirmed"
EVENT_VERSION: int = 1

DETAIL_NOT_CONFIGURED: str = "Automatización no configurada."
DETAIL_UNAVAILABLE: str = "Servicio de automatización no disponible."
DETAIL_TIMEOUT: str = "Tiempo de espera agotado (timeout)."
DETAIL_INVALID_RESPONSE_TEMPLATE: str = (
    "Respuesta no válida del servicio (HTTP {status_code})."
)
DETAIL_UNEXPECTED: str = "Error inesperado durante la automatización."
