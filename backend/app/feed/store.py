import re
import unicodedata
from datetime import date
from pathlib import Path

import frontmatter

from ..config import FEED_ENTRIES_DIR


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "entrada"


def list_entries(type_: str | None = None, subject: str | None = None, limit: int | None = None) -> list[dict]:
    FEED_ENTRIES_DIR.mkdir(parents=True, exist_ok=True)
    entries = []
    for path in FEED_ENTRIES_DIR.glob("*.md"):
        post = frontmatter.load(path)
        entry = dict(post.metadata)
        entry["content"] = post.content
        entry["id"] = path.stem
        entry.setdefault("date", "")
        entry.setdefault("type", "diario")
        entries.append(entry)

    if type_:
        entries = [e for e in entries if e.get("type") == type_]
    if subject:
        entries = [e for e in entries if e.get("subject") == subject]

    entries.sort(key=lambda e: str(e.get("date", "")), reverse=True)

    if limit:
        entries = entries[:limit]
    return entries


def create_entry(
    title: str,
    content: str,
    type_: str = "diario",
    subject: str | None = None,
    tags: list[str] | None = None,
    source_url: str | None = None,
    entry_date: str | None = None,
) -> dict:
    FEED_ENTRIES_DIR.mkdir(parents=True, exist_ok=True)
    entry_date = entry_date or date.today().isoformat()
    slug = slugify(title)
    filename = f"{entry_date}-{slug}.md"
    path = FEED_ENTRIES_DIR / filename

    counter = 2
    while path.exists():
        path = FEED_ENTRIES_DIR / f"{entry_date}-{slug}-{counter}.md"
        counter += 1

    metadata = {"title": title, "date": entry_date, "type": type_}
    if subject:
        metadata["subject"] = subject
    if tags:
        metadata["tags"] = tags
    if source_url:
        metadata["source_url"] = source_url

    post = frontmatter.Post(content, **metadata)
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    result = dict(metadata)
    result["content"] = content
    result["id"] = path.stem
    return result
