import copy

SERVICES_PAGE_TITLE = "Servicios"

SERVICES_CATALOG: dict[str, dict[str, object]] = {
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

DEFAULT_SERVICES_CATALOG: dict[str, dict[str, object]] = copy.deepcopy(SERVICES_CATALOG)
