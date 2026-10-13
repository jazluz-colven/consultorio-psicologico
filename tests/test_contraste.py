"""Contraste WCAG 2.1 AA de los pares de color documentados (docs/design-contrast.md)."""

import re
from pathlib import Path

from consultorio.config import Config

MAIN_CSS = (Config.STATIC_DIR / "css" / "main.css").read_text(encoding="utf-8")


def _luminance(hex_color: str) -> float:
    hex_color = hex_color.lstrip("#")
    channels = [int(hex_color[i:i + 2], 16) / 255 for i in (0, 2, 4)]

    def to_linear(channel: float) -> float:
        if channel <= 0.03928:
            return channel / 12.92
        return ((channel + 0.055) / 1.055) ** 2.4

    r, g, b = (to_linear(c) for c in channels)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(color_a: str, color_b: str) -> float:
    lum_a, lum_b = _luminance(color_a), _luminance(color_b)
    lighter, darker = max(lum_a, lum_b), min(lum_a, lum_b)
    return (lighter + 0.05) / (darker + 0.05)


def _css_variables() -> dict[str, str]:
    root_block = re.search(r":root\s*\{[^}]+\}", MAIN_CSS).group(0)
    return dict(re.findall(r"(--[a-z-]+):\s*(#[0-9A-Fa-f]{6})", root_block))


VARIABLES = _css_variables()

# (variable color, variable fondo, ratio mínimo, descripción)
TEXT_PAIRS = [
    ("--color-text", "--color-background", 4.5, "texto sobre marfil"),
    ("--color-primary-dark", "--color-background", 4.5, "salvia oscura sobre marfil"),
    ("--color-primary-dark", "--color-secondary", 4.5, "salvia oscura sobre verde agua"),
    ("--color-accent-dark", "--color-background", 4.5, "terracota oscura sobre marfil"),
    ("--color-accent-dark", "--color-secondary", 4.5, "terracota oscura sobre verde agua"),
    ("--color-background", "--color-primary-dark", 4.5, "texto de botón sobre salvia oscura"),
    ("--color-background", "--color-accent-dark", 4.5, "badge «Ocupado» sobre terracota oscura"),
    ("--color-background", "--color-text", 4.5, "texto marfil sobre azul grisáceo"),
    ("--color-text", "--color-secondary", 4.5, "texto sobre verde agua"),
    ("--color-text", "--color-support", 4.5, "texto sobre arena"),
]

BORDER_PAIRS = [
    ("--color-primary-dark", "--color-background", 3.0, "borde de input sobre marfil"),
    ("--color-primary-dark", "--color-secondary", 3.0, "borde de día agendable sobre verde agua"),
    ("--color-text", "--color-secondary", 3.0, "foco del calendario sobre verde agua"),
    ("--color-text", "--color-background", 3.0, "foco global sobre marfil"),
]


def test_variables_de_contraste_definidas_en_root() -> None:
    for name in ("--color-primary-dark", "--color-accent-dark"):
        assert name in VARIABLES, name


def test_pares_de_texto_cumplen_wcag_aa() -> None:
    for fg, bg, minimum, label in TEXT_PAIRS:
        ratio = contrast_ratio(VARIABLES[fg], VARIABLES[bg])
        assert ratio >= minimum, f"{label}: {fg} sobre {bg} = {ratio:.2f} (< {minimum})"


def test_bordes_y_focos_cumplen_wcag_3_a_1() -> None:
    for fg, bg, minimum, label in BORDER_PAIRS:
        ratio = contrast_ratio(VARIABLES[fg], VARIABLES[bg])
        assert ratio >= minimum, f"{label}: {fg} sobre {bg} = {ratio:.2f} (< {minimum})"


def test_calendario_sin_outline_none() -> None:
    assert "outline: none" not in MAIN_CSS


def test_hoja_usa_solo_colores_de_la_paleta_ampliada() -> None:
    from tests import expected_content as expected

    used = set(re.findall(r"#[0-9a-fA-F]{6}", MAIN_CSS))

    assert used
    assert used <= expected.PALETTE
