from dataclasses import dataclass

from consultorio.content.services_catalog import (
    DEFAULT_SERVICES_CATALOG,
    SERVICES_CATALOG,
    SERVICES_PAGE_TITLE,
)


@dataclass(frozen=True)
class ServiceItem:
    key: str
    name: str
    description: str
    benefits: list[str]


@dataclass(frozen=True)
class ServicesView:
    title: str
    items: list[ServiceItem]
    fallback_active: bool


def _resolve_text(value: object, default: str) -> tuple[str, bool]:
    if isinstance(value, str) and value.strip():
        return value, False
    return default, True


def _resolve_benefits(value: object, default: list[str]) -> tuple[list[str], bool]:
    if isinstance(value, list) and any(
        isinstance(item, str) and item.strip() for item in value
    ):
        return list(value), False
    return list(default), True


def validate_services() -> tuple[list[ServiceItem], bool]:
    resolved: list[ServiceItem] = []
    fallback_active = False
    for key in DEFAULT_SERVICES_CATALOG:
        default = DEFAULT_SERVICES_CATALOG[key]
        current = SERVICES_CATALOG.get(key, {})
        name, name_fallback = _resolve_text(current.get("name"), str(default["name"]))
        description, description_fallback = _resolve_text(
            current.get("description"), str(default["description"])
        )
        benefits, benefits_fallback = _resolve_benefits(
            current.get("benefits"), list(default["benefits"])
        )
        fallback_active = (
            fallback_active or name_fallback or description_fallback or benefits_fallback
        )
        resolved.append(
            ServiceItem(
                key=key,
                name=name,
                description=description,
                benefits=benefits,
            )
        )
    return resolved, fallback_active


def get_services_view() -> ServicesView:
    items, fallback = validate_services()
    return ServicesView(
        title=SERVICES_PAGE_TITLE,
        items=items,
        fallback_active=fallback,
    )
