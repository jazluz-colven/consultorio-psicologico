import re
from dataclasses import dataclass

from consultorio.content.contact_content import (
    ADDRESS_LINES,
    CONTACT_BLOCK_LABELS,
    CONTACT_PAGE_TITLE,
    DEFAULT_ADDRESS_LINES,
    DEFAULT_CONTACT_BLOCK_LABELS,
    DEFAULT_EMAIL,
    DEFAULT_OFFICE_HOURS,
    DEFAULT_PHONE,
    DEFAULT_WHATSAPP,
    EMAIL,
    OFFICE_HOURS,
    PHONE,
    SOCIAL_LINKS,
    WHATSAPP,
)

CONTACT_BLOCK_KEYS: tuple[str, ...] = (
    "address",
    "phone",
    "whatsapp",
    "email",
    "hours",
    "social",
)

_PHONE_RE = re.compile(r"^\+?[0-9]{7,}$")
_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass(frozen=True)
class ContactChannel:
    key: str
    value: str = ""
    href: str = ""
    lines: tuple[str, ...] = ()


@dataclass(frozen=True)
class OfficeHour:
    label: str
    days: str
    hours: str


@dataclass(frozen=True)
class SocialLink:
    platform: str
    label: str
    url: str


@dataclass(frozen=True)
class ContactView:
    title: str
    channels: tuple[ContactChannel, ...]
    hours: tuple[OfficeHour, ...]
    socials: tuple[SocialLink, ...]
    titles: dict[str, str]
    fallback_active: bool


def _clean_phone(value: object) -> str:
    if isinstance(value, str) and _PHONE_RE.match(value.strip()):
        return value.strip()
    return ""


def _clean_email(value: object) -> str:
    if isinstance(value, str) and _EMAIL_RE.match(value.strip()):
        return value.strip()
    return ""


def _non_empty_lines(values: object) -> tuple[str, ...]:
    if not isinstance(values, (list, tuple)):
        return ()
    return tuple(v.strip() for v in values if isinstance(v, str) and v.strip())


def _valid_hours(values: object) -> tuple[OfficeHour, ...]:
    if not isinstance(values, (list, tuple)):
        return ()
    resolved: list[OfficeHour] = []
    for item in values:
        if not isinstance(item, dict):
            continue
        label = item.get("label")
        days = item.get("days")
        hours = item.get("hours")
        if not all(isinstance(x, str) and x.strip() for x in (label, days, hours)):
            continue
        resolved.append(
            OfficeHour(label=label.strip(), days=days.strip(), hours=hours.strip())
        )
    return tuple(resolved)


def _valid_socials(values: object) -> tuple[tuple[SocialLink, ...], bool]:
    if not isinstance(values, (list, tuple)):
        return (), True
    resolved: list[SocialLink] = []
    dropped = False
    seen: set[str] = set()
    for item in values:
        if not isinstance(item, dict):
            dropped = True
            continue
        platform = item.get("platform")
        label = item.get("label")
        url = item.get("url")
        is_valid = (
            isinstance(platform, str)
            and bool(platform.strip())
            and isinstance(label, str)
            and bool(label.strip())
            and isinstance(url, str)
            and url.strip().startswith("https://")
            and platform.strip() not in seen
        )
        if not is_valid:
            dropped = True
            continue
        seen.add(platform.strip())
        resolved.append(
            SocialLink(
                platform=platform.strip(),
                label=label.strip(),
                url=url.strip(),
            )
        )
    return tuple(resolved), dropped


def _resolve(live: str, default: str) -> tuple[str, bool]:
    if live:
        return live, False
    return default, bool(default)


def resolve_block_titles() -> dict[str, str]:
    titles: dict[str, str] = {}
    for key in CONTACT_BLOCK_KEYS:
        live = CONTACT_BLOCK_LABELS.get(key)
        if isinstance(live, str) and live.strip():
            titles[key] = live.strip()
            continue
        default = DEFAULT_CONTACT_BLOCK_LABELS.get(key)
        titles[key] = default.strip() if isinstance(default, str) else ""
    return titles


def validate_contact() -> (
    tuple[tuple[ContactChannel, ...], tuple[OfficeHour, ...], tuple[SocialLink, ...], bool]
):
    fallback = False
    channels: list[ContactChannel] = []

    addr = _non_empty_lines(ADDRESS_LINES)
    if not addr:
        addr = _non_empty_lines(DEFAULT_ADDRESS_LINES)
        fallback = True
    if addr:
        channels.append(ContactChannel(key="address", lines=addr))

    channel_specs = (
        ("phone", PHONE, DEFAULT_PHONE, _clean_phone, lambda v: f"tel:+{v}"),
        (
            "whatsapp",
            WHATSAPP,
            DEFAULT_WHATSAPP,
            _clean_phone,
            lambda v: f"https://wa.me/{v.lstrip('+')}",
        ),
        ("email", EMAIL, DEFAULT_EMAIL, _clean_email, lambda v: f"mailto:{v}"),
    )
    for key, live, default, clean, href_for in channel_specs:
        value, used_default = _resolve(clean(live), clean(default))
        fallback = fallback or used_default
        if value:
            channels.append(
                ContactChannel(key=key, value=value, href=href_for(value))
            )

    hours = _valid_hours(OFFICE_HOURS)
    if not hours:
        hours = _valid_hours(DEFAULT_OFFICE_HOURS)
        fallback = fallback or bool(hours)

    socials, dropped = _valid_socials(SOCIAL_LINKS)
    fallback = fallback or dropped

    return tuple(channels), hours, socials, fallback


def get_contact_view() -> ContactView:
    channels, hours, socials, fallback = validate_contact()
    return ContactView(
        title=CONTACT_PAGE_TITLE,
        channels=channels,
        hours=hours,
        socials=socials,
        titles=resolve_block_titles(),
        fallback_active=fallback,
    )
