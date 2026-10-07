SERVICES_HIGHLIGHT: list[dict[str, str]] = [
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

DEFAULT_SERVICES_HIGHLIGHT: list[dict[str, str]] = [
    {**item} for item in SERVICES_HIGHLIGHT
]
