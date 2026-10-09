"""Appointment booking literals for the booking flow (HU-004)."""

BOOKING_PAGE_TITLE: str = "Agendar cita"

# 30-minute slots; morning block ends at 12:00, afternoon starts at 14:00.
BOOKING_HOURS: list[str] = [
    "08:00", "08:30", "09:00", "09:30",
    "10:00", "10:30", "11:00", "11:30",
    "14:00", "14:30", "15:00", "15:30",
    "16:00", "16:30",
]

DOCUMENT_TYPES: list[tuple[str, str]] = [
    ("CC", "Cédula de ciudadanía"),
    ("TI", "Tarjeta de identidad"),
    ("CE", "Cédula de extranjería"),
    ("PASSPORT", "Pasaporte"),
    ("RC", "Registro civil"),
]

MSG_REQUIRED_SERVICE: str = "Selecciona un servicio."
MSG_INVALID_SERVICE: str = "Selecciona un servicio válido."
MSG_REQUIRED_DATE: str = "Selecciona una fecha."
MSG_INVALID_DATE: str = (
    "Selecciona una fecha válida de lunes a viernes, no anterior a hoy."
)
MSG_REQUIRED_TIME: str = "Selecciona una hora."
MSG_INVALID_TIME: str = "Selecciona una hora válida."
MSG_REQUIRED_DOC_TYPE: str = "Selecciona un tipo de documento."
MSG_REQUIRED_DOC_NUMBER: str = "Ingresa el número de documento."
MSG_INVALID_DOC_NUMBER: str = (
    "El número de documento debe tener entre 4 y 20 dígitos."
)
MSG_REQUIRED_NAME: str = "Ingresa tu nombre y apellidos."
MSG_INVALID_NAME: str = "El nombre debe tener entre 3 y 120 caracteres."
MSG_REQUIRED_EMAIL: str = "Ingresa tu correo electrónico."
MSG_INVALID_EMAIL: str = "Ingresa un correo electrónico válido."
MSG_REQUIRED_PHONE: str = "Ingresa tu celular."
MSG_INVALID_PHONE: str = "Ingresa un celular válido (entre 7 y 15 dígitos)."
MSG_SLOT_TAKEN: str = "Ese horario ya no está disponible. Selecciona otro horario."
MSG_NO_HOURS: str = "No hay horarios disponibles para esta fecha."
MSG_INVALID_PARAMS: str = "Parámetros inválidos."
MSG_SELECT_DATE_HINT: str = "Selecciona una fecha para ver las horas disponibles."

BOOKING_BLOCK_MORNING: str = "Mañana"
BOOKING_BLOCK_AFTERNOON: str = "Tarde"

BOOKING_PATIENT_SECTION_TITLE: str = "Datos del paciente"
BOOKING_SCHEDULE_SECTION_TITLE: str = "Fecha y hora"

CONFIRMATION_TITLE: str = "Cita registrada"
STATUS_PENDING: str = "pending"
STATUS_PENDING_LABEL: str = "Pendiente"

BOOKING_HELPER: str = (
    "Si el paciente es menor de edad, registra los datos del "
    "representante con su documento; si es extranjero, puede usar "
    "pasaporte o cédula de extranjería."
)

# HU-005: availability states (spec 005 «Literales y contrato»)
MSG_OCCUPIED_HOUR: str = "Ocupado"
MSG_CHECKING_HOURS: str = "Consultando disponibilidad…"
CALENDAR_LEGEND_FREE: str = "Con horarios disponibles"
CALENDAR_LEGEND_FULL: str = "Sin horarios disponibles"
DAY_LABEL_NO_HOURS: str = ", sin horarios disponibles"
