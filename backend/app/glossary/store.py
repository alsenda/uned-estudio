import re
import unicodedata
from pathlib import Path

import frontmatter

from ..config import GLOSSARY_TERMS_DIR


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "termino"


def _find(id_: str) -> Path:
    path = GLOSSARY_TERMS_DIR / f"{id_}.md"
    if not path.exists():
        raise FileNotFoundError(id_)
    return path


def _unique_path(base: str) -> Path:
    path = GLOSSARY_TERMS_DIR / f"{base}.md"
    counter = 2
    while path.exists():
        path = GLOSSARY_TERMS_DIR / f"{base}-{counter}.md"
        counter += 1
    return path


def list_terms(subject: str | None = None, tag: str | None = None, q: str | None = None) -> list[dict]:
    GLOSSARY_TERMS_DIR.mkdir(parents=True, exist_ok=True)
    terms = []
    for path in GLOSSARY_TERMS_DIR.glob("*.md"):
        post = frontmatter.load(path)
        term = dict(post.metadata)
        term["definition"] = post.content
        term["id"] = path.stem
        term.setdefault("tags", [])
        terms.append(term)

    if subject:
        terms = [t for t in terms if t.get("subject") == subject]
    if tag:
        terms = [t for t in terms if tag in (t.get("tags") or [])]
    if q:
        needle = q.lower()
        terms = [t for t in terms if needle in str(t.get("term", "")).lower() or needle in t["definition"].lower()]

    terms.sort(key=lambda t: str(t.get("term", "")).lower())
    return terms


def list_tags() -> list[str]:
    tags = set()
    for term in list_terms():
        tags.update(term.get("tags") or [])
    return sorted(tags)


def create_term(term: str, definition: str = "", subject: str | None = None, tags: list[str] | None = None) -> dict:
    GLOSSARY_TERMS_DIR.mkdir(parents=True, exist_ok=True)
    path = _unique_path(slugify(term))

    metadata = {"term": term}
    if subject:
        metadata["subject"] = subject
    if tags:
        metadata["tags"] = tags

    post = frontmatter.Post(definition, **metadata)
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    result = dict(metadata)
    result["definition"] = definition
    result["id"] = path.stem
    return result


def update_term(id_: str, **fields) -> dict:
    path = _find(id_)
    post = frontmatter.load(path)
    definition = fields.pop("definition", None)
    for key, value in fields.items():
        if value is None:
            post.metadata.pop(key, None)
        else:
            post.metadata[key] = value
    if definition is not None:
        post.content = definition
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    result = dict(post.metadata)
    result["definition"] = post.content
    result["id"] = id_
    return result


def delete_term(id_: str) -> None:
    _find(id_).unlink()
