"""Automation event constants (HU-007); identifiers in English, texts in Spanish."""

EVENT_TYPE: str = "appointment.confirmed"
EVENT_VERSION: int = 1

CANCELLED_EVENT_TYPE: str = "appointment.cancelled"
CANCELLED_EVENT_VERSION: int = 1

DETAIL_NOT_CONFIGURED: str = "Automatización no configurada."
DETAIL_UNAVAILABLE: str = "Servicio de automatización no disponible."
DETAIL_TIMEOUT: str = "Tiempo de espera agotado (timeout)."
DETAIL_INVALID_RESPONSE_TEMPLATE: str = (
    "Respuesta no válida del servicio (HTTP {status_code})."
)
DETAIL_UNEXPECTED: str = "Error inesperado durante la automatización."

# D-010-01 (DP-02): retryability patterns are DERIVED from the single literal
# above on purpose. The persisted `detail` is the only classification input, so
# the prefix and the LIKE patterns must never be retyped by hand: a copy change
# in `DETAIL_INVALID_RESPONSE_TEMPLATE` would otherwise break the policy
# silently. `4__` is an intentional LIKE wildcard for 400-499 (permanent 4xx);
# 5xx and 429 do not match the permanent pattern.
# Test anchor only, NOT used by production logic: derived from the template
# above so a copy change cannot slip through unnoticed. Its consumer is the
# DP-02 binding test `test_tc_d010_dp02_patrones_derivados_del_template`.
DETAIL_INVALID_RESPONSE_PREFIX: str = DETAIL_INVALID_RESPONSE_TEMPLATE.split(
    "{status_code}"
)[0]
DETAIL_PERMANENT_REJECTION_PATTERN: str = DETAIL_INVALID_RESPONSE_TEMPLATE.format(
    status_code="4__"
)
DETAIL_RETRYABLE_REJECTION_PATTERN: str = DETAIL_INVALID_RESPONSE_TEMPLATE.format(
    status_code="429"
)
