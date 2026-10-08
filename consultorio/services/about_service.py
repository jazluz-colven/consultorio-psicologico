from dataclasses import dataclass, fields

from consultorio.content.about_content import (
    ABOUT_CONTENT,
    BLOCK_TITLES,
    DEFAULT_ABOUT_CONTENT,
    DEFAULT_BLOCK_TITLES,
)

ABOUT_BLOCK_KEYS: tuple[str, ...] = ("mission", "vision", "experience", "values")


@dataclass(frozen=True)
class AboutContent:
    mission: str
    vision: str
    experience: str
    values: str


@dataclass(frozen=True)
class AboutView(AboutContent):
    titles: dict[str, str]
    fallback_active: bool


def _resolve_text(value: str | None, default: str) -> tuple[str, bool]:
    if isinstance(value, str) and value.strip():
        return value, False
    return default, True


def validate_about() -> tuple[AboutContent, bool]:
    fallback_active = False
    resolved: dict[str, str] = {}
    for key in ABOUT_BLOCK_KEYS:
        text, used_default = _resolve_text(
            ABOUT_CONTENT.get(key), DEFAULT_ABOUT_CONTENT[key]
        )
        resolved[key] = text
        fallback_active = fallback_active or used_default

    content = AboutContent(
        mission=resolved["mission"],
        vision=resolved["vision"],
        experience=resolved["experience"],
        values=resolved["values"],
    )
    return content, fallback_active


def resolve_block_titles() -> dict[str, str]:
    titles: dict[str, str] = {}
    for key in ABOUT_BLOCK_KEYS:
        title, _ = _resolve_text(BLOCK_TITLES.get(key), DEFAULT_BLOCK_TITLES[key])
        titles[key] = title
    return titles


def get_about_view() -> AboutView:
    content, fallback = validate_about()
    values = {field.name: getattr(content, field.name) for field in fields(AboutContent)}
    return AboutView(
        **values,
        titles=resolve_block_titles(),
        fallback_active=fallback,
    )
