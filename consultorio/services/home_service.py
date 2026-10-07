from collections.abc import Mapping, Sequence
from dataclasses import dataclass, fields
from pathlib import Path

from consultorio.config import Config
from consultorio.content.hero_image import DEFAULT_HERO_IMAGE, HERO_IMAGE
from consultorio.content.home_content import (
    DEFAULT_HOME_CONTENT,
    DEFAULT_SECONDARY_BRAND,
    DEFAULT_TRUST_LINE,
    HOME_CONTENT,
    SECONDARY_BRAND,
    TRUST_LINE,
)
from consultorio.content.nav_links import NAV_LINKS
from consultorio.content.services_highlights import (
    DEFAULT_SERVICES_HIGHLIGHT,
    SERVICES_HIGHLIGHT,
)

PLACEHOLDER_IMAGE: str = "img/placeholder.svg"
FALLBACK_NAV_ITEM = {"label": "Inicio", "url": "/"}
REQUIRED_SERVICE_FIELDS: tuple[str, ...] = ("name", "summary", "url")


class ContentError(RuntimeError):
    """Raised when the institutional content cannot be built."""


@dataclass(frozen=True)
class HeroImage:
    src: str
    alt: str
    available: bool


@dataclass(frozen=True)
class NavItem:
    label: str
    url: str


@dataclass(frozen=True)
class ServiceHighlight:
    name: str
    summary: str
    url: str


@dataclass(frozen=True)
class HomeContent:
    secondary_brand: str
    brand_name: str
    tagline: str
    intro: str
    services_title: str
    services_link_label: str
    services_link_url: str
    trust_line: str


@dataclass(frozen=True)
class HomeView(HomeContent):
    services: list[ServiceHighlight]
    hero: HeroImage
    nav: list[NavItem]
    fallback_active: bool


def _resolve_text(value: str | None, default: str) -> tuple[str, bool]:
    if isinstance(value, str) and value.strip():
        return value, False
    return default, True


def validate_content() -> tuple[HomeContent, bool]:
    fallback_active = False
    resolved: dict[str, str] = {}
    for key, default_value in DEFAULT_HOME_CONTENT.items():
        text, used_default = _resolve_text(HOME_CONTENT.get(key), default_value)
        resolved[key] = text
        fallback_active = fallback_active or used_default

    secondary_brand, used_default = _resolve_text(
        SECONDARY_BRAND, DEFAULT_SECONDARY_BRAND
    )
    fallback_active = fallback_active or used_default

    trust_line, used_default = _resolve_text(TRUST_LINE, DEFAULT_TRUST_LINE)
    fallback_active = fallback_active or used_default

    content = HomeContent(
        secondary_brand=secondary_brand,
        brand_name=resolved["brand_name"],
        tagline=resolved["tagline"],
        intro=resolved["intro"],
        services_title=resolved["services_title"],
        services_link_label=resolved["services_link_label"],
        services_link_url=resolved["services_link_url"],
        trust_line=trust_line,
    )
    return content, fallback_active


def _to_service(item: Mapping[str, str]) -> ServiceHighlight | None:
    values = {
        field: (item.get(field) or "").strip() for field in REQUIRED_SERVICE_FIELDS
    }
    if any(not value for value in values.values()):
        return None
    return ServiceHighlight(**values)


def validate_services(
    services: Sequence[Mapping[str, str]] | None = None,
) -> tuple[list[ServiceHighlight], bool]:
    source = SERVICES_HIGHLIGHT if services is None else services
    valid_items = [item for item in (_to_service(raw) for raw in source) if item]
    if len(valid_items) >= len(DEFAULT_SERVICES_HIGHLIGHT):
        return valid_items, False

    default_items = [
        ServiceHighlight(
            name=item["name"], summary=item["summary"], url=item["url"]
        )
        for item in DEFAULT_SERVICES_HIGHLIGHT
    ]
    return default_items, True


def resolve_hero_image(
    image: Mapping[str, str | None] | None = None,
    static_dir: Path | None = None,
) -> HeroImage:
    source = HERO_IMAGE if image is None else image
    root = Config.STATIC_DIR if static_dir is None else static_dir
    alt, _ = _resolve_text(source.get("alt"), DEFAULT_HERO_IMAGE["alt"] or "")
    path = source.get("path")
    available = bool(path) and _asset_exists(Path(str(path)), root)
    if available:
        return HeroImage(src=str(path), alt=alt, available=True)
    return HeroImage(src=PLACEHOLDER_IMAGE, alt=alt, available=False)


def _asset_exists(relative_path: Path, static_dir: Path) -> bool:
    if relative_path.is_absolute() or ".." in relative_path.parts:
        return False
    return (static_dir / relative_path).is_file()


def build_navigation(
    links: Sequence[Mapping[str, str]] | None = None,
) -> list[NavItem]:
    source = NAV_LINKS if links is None else links
    items: list[NavItem] = []
    seen_urls: set[str] = set()
    for raw in source:
        label = (raw.get("label") or "").strip()
        url = (raw.get("url") or "").strip()
        if not label or not url or url in seen_urls:
            continue
        seen_urls.add(url)
        items.append(NavItem(label=label, url=url))

    if not items:
        return [
            NavItem(label=FALLBACK_NAV_ITEM["label"], url=FALLBACK_NAV_ITEM["url"])
        ]
    return items


def find_nav_item(url: str) -> NavItem | None:
    for item in build_navigation():
        if item.url == url:
            return item
    return None


def get_home_view() -> HomeView:
    content, content_fallback = validate_content()
    services, services_fallback = validate_services()
    hero = resolve_hero_image()
    nav = build_navigation()

    values = {field.name: getattr(content, field.name) for field in fields(HomeContent)}
    return HomeView(
        **values,
        services=services,
        hero=hero,
        nav=nav,
        fallback_active=content_fallback or services_fallback,
    )
