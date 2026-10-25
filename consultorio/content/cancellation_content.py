"""Patient cancellation flow literals (HU-017, spec 017 RF-1..RF-13).

Contractual copy from the «Textos de interfaz (contractuales)» table of
spec 017; identifiers in English, texts in Spanish. Mirrored in
tests/expected_content.py (changing copy requires a spec PR first).
No logic, no database access here.
"""

from consultorio.content.appointment_content import STATUS_CANCELLED_LABEL

# Verification step (RF-1..RF-4): page title and previous notice
CANCEL_PAGE_TITLE: str = "Cancelar cita"
CANCEL_NOTICE: str = (
    "Si cancelas tu cita, este horario quedará libre y no podrás "
    "recuperarlo desde aquí."
)

# Summary step (RF-3): confirmation buttons (Q-D: back goes to the appointment page)
CANCEL_CONFIRM_BUTTON: str = "Sí, cancelar mi cita"
CANCEL_BACK_BUTTON: str = "No, volver"

# Success screen (RF-7); the shown status reuses STATUS_CANCELLED_LABEL (D5)
CANCEL_SUCCESS_TITLE: str = "Cita cancelada"
CANCEL_SUCCESS_MESSAGE: str = (
    "Tu cita ha sido cancelada. El horario ya está disponible para "
    "otra persona."
)

# Verification / conflict / restriction messages (RF-2, RF-4, RF-9)
MSG_VERIFICATION_FAILED: str = (
    "No pudimos verificar tu cita. Revisa los datos e inténtalo de nuevo."
)
MSG_ALREADY_CANCELLED: str = "Esta cita ya fue cancelada."
MSG_NOTICE_PERIOD: str = (
    "Solo puedes cancelar tu cita desde el sitio con al menos 3 horas "
    "de anticipación. Si necesitas cancelar con menos tiempo, "
    "contáctate con el consultorio."
)

# Entry points: button on the confirmed-appointment page (RF-12) and the
# confirmation-e-mail link label (RF-13, D9). Same text, two literals.
CANCEL_BUTTON_LABEL: str = "Cancelar cita"
EMAIL_CANCEL_LINK_LABEL: str = "Cancelar cita"

# Functional labels of the verification form and the summary/success screens (D5)
LABEL_REFERENCE: str = "Referencia de la cita"
LABEL_DOCUMENT_NUMBER: str = "Número de documento"
LABEL_SERVICE: str = "Servicio"
LABEL_DATE: str = "Fecha"
LABEL_TIME: str = "Hora"
LABEL_STATUS: str = "Estado"
