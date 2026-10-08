from __future__ import annotations

import unicodedata
from dataclasses import dataclass

from consultorio.content.about_content import ABOUT_CONTENT, BLOCK_TITLES
from consultorio.content.home_content import HOME_CONTENT, TRUST_LINE
from consultorio.content.nav_links import NAV_LINKS
from consultorio.content.services_catalog import SERVICES_CATALOG
from consultorio.content.services_highlights import SERVICES_HIGHLIGHT

SNIPPET_WIDTH = 120

STATUS_EMPTY = "empty"
STATUS_OK = "ok"


@dataclass(frozen=True)
class IndexEntry:
    title: str
    text: str
    url: str


@dataclass(frozen=True)
class SearchResult:
    title: str
    url: str
    snippet: str


def _normalize(value: str) -> str:
    """Lowercase + strip accents so the search is case/accent insensitive."""
    decomposed = unicodedata.normalize("NFKD", value)
    unaccented = "".join(
        char for char in decomposed if not unicodedata.combining(char)
    )
    return unaccented.lower()


def _snippet(text: str, needle: str) -> str:
    if not text:
        return ""
    position = _normalize(text).find(needle)
    if position < 0 or position >= len(text):
        start = 0
    else:
        start = max(0, position - SNIPPET_WIDTH // 3)
    fragment = text[start : start + SNIPPET_WIDTH].strip()
    if start > 0:
        fragment = f"…{fragment}"
    if start + SNIPPET_WIDTH < len(text):
        fragment = f"{fragment}…"
    return fragment


def build_index() -> list[IndexEntry]:
    entries: list[IndexEntry] = [
        IndexEntry(
            title="Presentación",
            text=f"{HOME_CONTENT.get('tagline', '')} {HOME_CONTENT.get('intro', '')}".strip(),
            url="/",
        ),
    ]

    for item in SERVICES_HIGHLIGHT:
        entries.append(
            IndexEntry(
                title=item["name"],
                text=f"{item['name']} {item['summary']}".strip(),
                url=item["url"],
            )
        )

    entries.append(IndexEntry(title="Frase de valores", text=TRUST_LINE, url="/"))

    for key, text in ABOUT_CONTENT.items():
        entries.append(
            IndexEntry(
                title=BLOCK_TITLES.get(key, key.title()),
                text=f"{BLOCK_TITLES.get(key, key.title())} {text}".strip(),
                url="/nosotros",
            )
        )

    for item in SERVICES_CATALOG.values():
        benefits = " ".join(str(benefit) for benefit in item.get("benefits", []))
        entries.append(
            IndexEntry(
                title=str(item["name"]),
                text=f"{item['name']} {item['description']} {benefits}".strip(),
                url="/servicios",
            )
        )

    for link in NAV_LINKS:
        entries.append(
            IndexEntry(title=link["label"], text=link["label"], url=link["url"])
        )

    seen: set[tuple[str, str]] = set()
    unique: list[IndexEntry] = []
    for entry in entries:
        key = (entry.title, entry.url)
        if key in seen:
            continue
        seen.add(key)
        unique.append(entry)
    return unique


def search(query: str) -> tuple[list[SearchResult], str]:
    """Return matching results plus a status: STATUS_EMPTY or STATUS_OK."""
    needle = _normalize(query.strip())
    if not needle:
        return [], STATUS_EMPTY

    results: list[SearchResult] = []
    for entry in build_index():
        if needle in _normalize(entry.title) or needle in _normalize(entry.text):
            results.append(
                SearchResult(
                    title=entry.title,
                    url=entry.url,
                    snippet=_snippet(entry.text, needle),
                )
            )
    return results, STATUS_OK
