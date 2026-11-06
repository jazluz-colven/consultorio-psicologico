"""Admin appointment management literals (HU-018, spec 018).

Contractual copy from the «Textos de interfaz (contractuales)» table of
spec 018 plus the functional labels of the admin screens. Mirrored in
tests/expected_content.py (changing copy requires a spec PR first).
The «Confirmada»/«Cancelada» labels are reused from appointment_content;
they are not duplicated here. No logic, no database access.
"""

from consultorio.content.appointment_content import (
    STATUS_CANCELLED_LABEL,
    STATUS_CONFIRMED_LABEL,
)

# 14 contractual literals (spec 018 table, amended 2026-11-05)
ADMIN_PAGE_TITLE: str = "Gestión de citas"
ADMIN_CANCEL_TITLE: str = "Cancelar cita"
ADMIN_CANCEL_NOTICE: str = (
    "La cita quedará Cancelada, el horario se liberará y el paciente "
    "recibirá la notificación."
)
ADMIN_CANCEL_BUTTON: str = "Sí, cancelar cita"
ADMIN_RESCHEDULE_TITLE: str = "Reprogramar cita"
ADMIN_RESCHEDULE_NOTICE: str = (
    "Se cancelará la cita actual y se registrará una nueva. El paciente "
    "recibirá la cancelación y la nueva confirmación."
)
ADMIN_RESCHEDULE_BUTTON: str = "Sí, reprogramar"
ADMIN_BACK_BUTTON: str = "Volver"
ADMIN_CANCEL_SUCCESS: str = "Cita cancelada."
ADMIN_RESCHEDULE_SUCCESS_TEMPLATE: str = "Cita reprogramada. Nueva cita #{id}."
ADMIN_ACCESS_DENIED: str = "No tienes acceso a la gestión de citas."
ADMIN_APPOINTMENT_NOT_FOUND: str = (
    "No encontramos esa cita. Revisa la referencia."
)
ADMIN_MSG_ALREADY_CANCELLED: str = "La cita ya estaba cancelada."
ADMIN_SLOT_TAKEN: str = "Ese horario ya está ocupado. Elige otro."

# 6 functional labels (plan 018, D6); not contractual copy
ADMIN_LABEL_SERVICE: str = "Servicio"
ADMIN_LABEL_NEW_DATE: str = "Nueva fecha"
ADMIN_LABEL_TIME: str = "Hora"
ADMIN_LABEL_SUMMARY: str = "Resumen de la cita"
ADMIN_LABEL_PATIENT: str = "Paciente"
ADMIN_LABEL_STATUS: str = "Estado"
