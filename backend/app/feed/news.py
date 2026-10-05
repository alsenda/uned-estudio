import json

import feedparser
import yaml

from ..config import NEWS_SEEN_PATH, SOURCES_PATH
from . import store


def _load_sources() -> list[dict]:
    if not SOURCES_PATH.exists():
        return []
    with open(SOURCES_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f) or []
    return data


def _load_seen() -> set[str]:
    if not NEWS_SEEN_PATH.exists():
        return set()
    with open(NEWS_SEEN_PATH, "r", encoding="utf-8") as f:
        return set(json.load(f))


def _save_seen(seen: set[str]) -> None:
    NEWS_SEEN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(NEWS_SEEN_PATH, "w", encoding="utf-8") as f:
        json.dump(sorted(seen), f, ensure_ascii=False, indent=2)


def refresh_news() -> dict:
    sources = _load_sources()
    seen = _load_seen()
    added = 0
    errors = []

    for source in sources:
        rss_url = source.get("rss_url")
        if not rss_url:
            continue
        parsed = feedparser.parse(rss_url)
        if parsed.bozo and not parsed.entries:
            errors.append(f"{source.get('name', rss_url)}: no se pudo leer el feed")
            continue

        for item in parsed.entries:
            link = item.get("link")
            if not link or link in seen:
                continue
            title = item.get("title", "(sin título)")
            summary = item.get("summary", "")
            published = item.get("published", "") or item.get("updated", "")
            store.create_entry(
                title=title,
                content=f"{summary}\n\n[Leer más]({link})",
                type_="noticia",
                subject=source.get("subject"),
                source_url=link,
                entry_date=_parse_date(item) or None,
            )
            seen.add(link)
            added += 1

    _save_seen(seen)
    return {"added": added, "sources_checked": len(sources), "errors": errors}


def _parse_date(item) -> str | None:
    parsed_time = item.get("published_parsed") or item.get("updated_parsed")
    if not parsed_time:
        return None
    return f"{parsed_time.tm_year:04d}-{parsed_time.tm_mon:02d}-{parsed_time.tm_mday:02d}"
