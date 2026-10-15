SECONDARY_BRAND = "Contenidas"

BRAND_NAME = "Carolina Gómez"

TAGLINE = "Acompañamiento psicológico y nutricional con calidez profesional"

INTRO = (
    "Un espacio de atención personalizada donde la salud mental y el "
    "bienestar alimentario se abordan con evidencia, escucha y respeto. "
    "Te acompañamos en cada etapa con un trato cercano, profesional y "
    "confidencial."
)

SERVICES_TITLE = "Nuestros servicios"

SERVICES_LINK_LABEL = "Ver todos los servicios"

SERVICES_LINK_URL = "/servicios"

TRUST_LINE = (
    "Acompañamos con profesionalismo, empatía y confidencialidad. "
    "Nuestro compromiso es tu bienestar en un espacio seguro y sin juicios."
)

HERO_SRC = "img/hero-presentacion.png"

HERO_ALT = "Retrato de Carolina Gómez en su consultorio con la leyenda «Salud mental»"

HEADER_LOGO_SRC = "img/hero-contenidas.png"

HEADER_LOGO_ALT = "Contenidas"

SEARCH_URL = "/buscar"

SEARCH_QUERY_PARAM = "q"

SEARCH_LABEL = "Buscar en el sitio"

SEARCH_PLACEHOLDER = "Buscar en el sitio…"

SEARCH_EMPTY_MESSAGE = "Escribe un término para buscar en el sitio."

SEARCH_NO_RESULTS_PREFIX = "No se encontraron resultados para «"

SEARCH_RESULTS_TITLE = "Resultados de búsqueda"

SEARCH_RESULTS_STATUS = "para «"

PLACEHOLDER_SRC = "img/placeholder.svg"

HOME_CONTENT = {
    "brand_name": BRAND_NAME,
    "tagline": TAGLINE,
    "intro": INTRO,
    "services_title": SERVICES_TITLE,
    "services_link_label": SERVICES_LINK_LABEL,
    "services_link_url": SERVICES_LINK_URL,
}

SERVICES = [
    {
        "name": "Psicología Integral",
        "summary": (
            "Acompañamiento terapéutico para personas, parejas y familias, "
            "con un enfoque integral y basado en evidencia."
        ),
        "url": "/servicios",
    },
    {
        "name": "Psiconutrición",
        "summary": (
            "Integración de salud mental y alimentación para construir hábitos "
            "sostenibles y una relación saludable con la comida."
        ),
        "url": "/servicios",
    },
]

NAV_LINKS = [
    {"label": "Inicio", "url": "/"},
    {"label": "Nosotros", "url": "/nosotros"},
    {"label": "Servicios", "url": "/servicios"},
    {"label": "Blog", "url": "/articulos"},
    {"label": "Contacto", "url": "/contacto"},
    {"label": "Agendar cita", "url": "/citas"},
]

PLACEHOLDER_SECTIONS = ["/articulos"]

ABOUT_CONTENT = {
    "mission": (
        "Acompañar a cada persona, pareja o familia en el cuidado de su salud mental "
        "y su bienestar alimentario, ofreciendo atención personalizada basada en "
        "evidencia, con un trato cercano, respetuoso y confidencial en un espacio "
        "seguro y sin juicios."
    ),
    "vision": (
        "Ser un espacio de confianza donde cada persona encuentre las herramientas "
        "para comprenderse, cuidarse y sostener cambios duraderos en su bienestar, "
        "reconocido por la calidez humana y la solidez profesional con la que "
        "acompaña a su comunidad."
    ),
    "experience": (
        "Soy profesional en el área de la Psicología, diplomada en primeros auxilios "
        "psicológicos, psiconutrición, y a través de esta formación me he dedicado a "
        "brindar acompañamiento y herramientas de apoyo emocional y espiritual."
    ),
    "values": (
        "Profesionalismo basado en evidencia. Escucha empática y sin juicios. "
        "Confidencialidad y respeto en cada proceso. Calidez humana y compromiso con "
        "el bienestar de cada persona."
    ),
}

ABOUT_BLOCK_TITLES = {
    "mission": "Misión",
    "vision": "Visión",
    "experience": "Experiencia profesional",
    "values": "Valores",
}

SERVICES_PAGE_TITLE = "Servicios"

SERVICES_CATALOG = {
    "psychology_integral": {
        "name": "Psicología Integral",
        "description": (
            "Un proceso terapéutico para personas, parejas y familias que "
            "busca comprender lo que estás viviendo, aliviar el malestar y "
            "construir herramientas concretas para el día a día, con un "
            "enfoque basado en evidencia y un trato cercano, respetuoso y "
            "confidencial."
        ),
        "benefits": [
            "Comprensión más clara de tus emociones, relaciones y patrones de conducta.",
            "Herramientas prácticas para manejar el estrés y el malestar cotidiano.",
            "Acompañamiento personalizado: individual, de pareja o familiar.",
            "Un espacio seguro, sin juicios y confidencial para hablar abiertamente.",
        ],
        "image": "img/servicios/psicologia-integral.webp",
        "image_alt": "Sesión de acompañamiento terapéutico en el consultorio",
    },
    "nutrition": {
        "name": "Psiconutrición",
        "description": (
            "Un acompañamiento que integra la salud mental con la alimentación "
            "para construir hábitos sostenibles y una relación más tranquila y "
            "consciente con la comida, sin dietas restrictivas ni culpa, "
            "respetando tu historia, tu ritmo y tus metas."
        ),
        "benefits": [
            "Hábitos alimentarios sostenibles, sin restricciones impuestas.",
            "Una relación más saludable y consciente con la comida.",
            "Vinculación entre lo emocional y lo alimentario en un mismo proceso.",
            "Planes personalizados adaptados a tu realidad y tus objetivos.",
        ],
        "image": "img/servicios/psiconutricion.webp",
        "image_alt": "Sesión de acompañamiento nutricional con plan alimentario personalizado",
    },
}

PALETTE = {
    "#789B8A",
    "#B8D8CE",
    "#F7F3EA",
    "#D99A7A",
    "#E8D5B5",
    "#30454B",
    # Tonos funcionales derivados (docs/design-contrast.md, 2026-10-12):
    # accesibilidad WCAG AA, no son colores de marca nuevos.
    "#3D5A4E",
    "#7F4527",
}

# --- HU-004: Agendar cita (espejo único de la spec 004) ---

BOOKING_PAGE_TITLE = "Agendar cita"

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

MSG_REQUIRED_SERVICE = "Selecciona un servicio."
MSG_INVALID_SERVICE = "Selecciona un servicio válido."
MSG_REQUIRED_DATE = "Selecciona una fecha."
MSG_INVALID_DATE = "Selecciona una fecha válida de lunes a viernes, no anterior a hoy."
MSG_REQUIRED_TIME = "Selecciona una hora."
MSG_INVALID_TIME = "Selecciona una hora válida."
MSG_REQUIRED_DOC_TYPE = "Selecciona un tipo de documento."
MSG_REQUIRED_DOC_NUMBER = "Ingresa el número de documento."
MSG_INVALID_DOC_NUMBER = "El número de documento debe tener entre 4 y 20 dígitos."
MSG_REQUIRED_NAME = "Ingresa tu nombre y apellidos."
MSG_INVALID_NAME = "El nombre debe tener entre 3 y 120 caracteres."
MSG_REQUIRED_EMAIL = "Ingresa tu correo electrónico."
MSG_INVALID_EMAIL = "Ingresa un correo electrónico válido."
MSG_REQUIRED_PHONE = "Ingresa tu celular."
MSG_INVALID_PHONE = "Ingresa un celular válido (entre 7 y 15 dígitos)."
MSG_SLOT_TAKEN = "Ese horario ya no está disponible. Selecciona otro horario."
MSG_NO_HOURS = "No hay horarios disponibles para esta fecha."
MSG_INVALID_PARAMS = "Parámetros inválidos."
MSG_SELECT_DATE_HINT = "Selecciona una fecha para ver las horas disponibles."

BOOKING_BLOCK_MORNING = "Mañana"
BOOKING_BLOCK_AFTERNOON = "Tarde"

BOOKING_PATIENT_SECTION_TITLE = "Datos del paciente"
BOOKING_SCHEDULE_SECTION_TITLE = "Fecha y hora"
CONFIRMATION_TITLE = "Cita registrada"
STATUS_CONFIRMED_LABEL = "Confirmada"
BOOKING_HELPER = (
    "Si el paciente es menor de edad, registra los datos del "
    "representante con su documento; si es extranjero, puede usar "
    "pasaporte o cédula de extranjería."
)

# --- HU-005: Validar disponibilidad de horarios (espejo único de la spec 005) ---

MSG_OCCUPIED_HOUR = "Ocupado"

MSG_CHECKING_HOURS = "Consultando disponibilidad…"

CALENDAR_LEGEND_FREE = "Con horarios disponibles"

CALENDAR_LEGEND_FULL = "Sin horarios disponibles"

DAY_LABEL_NO_HOURS = ", sin horarios disponibles"

# --- HU-006: Evitar doble reserva (espejo único de la spec 006) ---
# MSG_SLOT_TAKEN (spec 004) y MSG_OCCUPIED_HOUR (spec 005) se reutilizan sin cambio.

MSG_SUBMITTING = "Registrando tu cita…"

# --- HU-008: Enviar confirmación por correo (espejo único de la spec 008) ---

EMAIL_SUBJECT_TEMPLATE = (
    "Confirmación de tu cita — {service_name} · {date_label} · {time}"
)

EMAIL_SENDER_NAME = "Carolina Gómez"

EMAIL_BODY_HEADER = (
    "Tu cita ha sido registrada. Estos son los datos de la reserva:"
)

EMAIL_LABEL_SERVICE = "Servicio"

EMAIL_LABEL_DATE = "Fecha"

EMAIL_LABEL_TIME = "Hora"

EMAIL_LABEL_STATUS = "Estado"

EMAIL_LABEL_REFERENCE = "Referencia de la reserva"

EMAIL_FOOTER = (
    "Guarda este correo como comprobante de tu reserva. "
    "Si necesitas modificar o cancelar tu cita, "
    "contáctate con el consultorio."
)

MSG_APPOINTMENT_INCOMPLETE = "Datos de la cita incompletos."

DETAIL_EMAIL_NOT_CONFIGURED = "Envío de correo no configurado."

DETAIL_INVALID_RECIPIENT = (
    "Dirección de correo del paciente ausente o no válida."
)

# --- HU-015: Consultar información de contacto (espejo único de la spec 015) ---

CONTACT_PAGE_TITLE = "Contacto"

CONTACT_ADDRESS_LINES = [
    "Calle 34 #29-18",
    "Mejoras Públicas",
    "Bucaramanga, Colombia",
]

CONTACT_PHONE = ""

CONTACT_WHATSAPP = "+573168756020"

CONTACT_EMAIL = "caritogomez26@gmail.com"

CONTACT_OFFICE_HOURS = [
    {"label": "Mañana", "days": "Lunes a viernes", "hours": "8:00 a. m. – 11:30 a. m."},
    {"label": "Tarde", "days": "Lunes a viernes", "hours": "2:00 p. m. – 4:30 p. m."},
]

CONTACT_SOCIAL_LINKS = [
    {
        "platform": "instagram",
        "label": "Instagram",
        "url": "https://www.instagram.com/psi.carolinagomez/",
    },
]

CONTACT_BLOCK_LABELS = {
    "address": "Dirección",
    "phone": "Teléfono",
    "whatsapp": "WhatsApp",
    "email": "Correo electrónico",
    "hours": "Horarios de atención",
    "social": "Redes sociales",
}

# --- Ampliación 2026-10-12 (RF-7): mapa de ubicación ---

CONTACT_MAP_QUERY = "Calle 34 #29-18, Mejoras Públicas, Bucaramanga, Colombia"

CONTACT_MAP_EMBED_URL = (
    "https://www.google.com/maps?q="
    "Calle%2034%20%2329-18%2C%20Mejoras%20P%C3%BAblicas%2C%20Bucaramanga%2C%20Colombia"
    "&output=embed"
)

CONTACT_MAP_LINK_URL = (
    "https://www.google.com/maps/search/?api=1&query="
    "Calle%2034%20%2329-18%2C%20Mejoras%20P%C3%BAblicas%2C%20Bucaramanga%2C%20Colombia"
)

CONTACT_MAP_LINK_LABEL = "Abrir en Google Maps"

CONTACT_MAP_FRAME_TITLE = "Ubicación del consultorio en Google Maps"

# --- HU-010: Notificar la cancelación de una cita (espejo único de la spec 010) ---

STATUS_CANCELLED = "cancelled"

STATUS_CANCELLED_LABEL = "Cancelada"

CANCELLATION_EMAIL_SUBJECT_TEMPLATE = (
    "Cita cancelada — {service_name} · {date_label} · {time}"
)

CANCELLATION_EMAIL_BODY_HEADER = (
    "Tu cita ha sido cancelada. Estos son los datos de la cita cancelada:"
)

CANCELLATION_EMAIL_FOOTER = (
    "Si deseas agendar una nueva cita, puedes hacerlo desde la página "
    "del consultorio o contactándote con nosotros."
)

DETAIL_CANCELLATION_NOT_CONFIGURED = "Envío de correo no configurado."
