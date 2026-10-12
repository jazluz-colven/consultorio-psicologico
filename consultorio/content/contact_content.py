import copy

CONTACT_PAGE_TITLE: str = "Contacto"

ADDRESS_LINES: list[str] = [
    "Calle 34 #29-18",
    "Mejoras Públicas",
    "Bucaramanga, Colombia",
]

PHONE: str = ""

WHATSAPP: str = "+573168756020"

EMAIL: str = "caritogomez26@gmail.com"

OFFICE_HOURS: list[dict[str, str]] = [
    {"label": "Mañana", "days": "Lunes a viernes", "hours": "8:00 a. m. – 11:30 a. m."},
    {"label": "Tarde", "days": "Lunes a viernes", "hours": "2:00 p. m. – 4:30 p. m."},
]

SOCIAL_LINKS: list[dict[str, str]] = [
    {
        "platform": "instagram",
        "label": "Instagram",
        "url": "https://www.instagram.com/psi.carolinagomez/",
    },
]

CONTACT_BLOCK_LABELS: dict[str, str] = {
    "address": "Dirección",
    "phone": "Teléfono",
    "whatsapp": "WhatsApp",
    "email": "Correo electrónico",
    "hours": "Horarios de atención",
    "social": "Redes sociales",
}

DEFAULT_ADDRESS_LINES: list[str] = copy.deepcopy(ADDRESS_LINES)
DEFAULT_PHONE: str = PHONE
DEFAULT_WHATSAPP: str = WHATSAPP
DEFAULT_EMAIL: str = EMAIL
DEFAULT_OFFICE_HOURS: list[dict[str, str]] = copy.deepcopy(OFFICE_HOURS)
DEFAULT_SOCIAL_LINKS: list[dict[str, str]] = copy.deepcopy(SOCIAL_LINKS)
DEFAULT_CONTACT_BLOCK_LABELS: dict[str, str] = copy.deepcopy(CONTACT_BLOCK_LABELS)
