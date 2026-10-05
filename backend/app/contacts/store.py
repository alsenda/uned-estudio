import re
import unicodedata
from datetime import date
from pathlib import Path

import frontmatter

from ..config import CONTACTS_INTERACTIONS_DIR, CONTACTS_PEOPLE_DIR


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "contacto"


def _find(dir_: Path, id_: str) -> Path:
    path = dir_ / f"{id_}.md"
    if not path.exists():
        raise FileNotFoundError(id_)
    return path


def _unique_path(dir_: Path, base: str) -> Path:
    path = dir_ / f"{base}.md"
    counter = 2
    while path.exists():
        path = dir_ / f"{base}-{counter}.md"
        counter += 1
    return path


def _apply_fields(post: frontmatter.Post, fields: dict) -> None:
    notes = fields.pop("notes", None)
    for key, value in fields.items():
        if value is None:
            post.metadata.pop(key, None)
        else:
            post.metadata[key] = value
    if notes is not None:
        post.content = notes


# ---- personas ----

def list_people(role: str | None = None, subject: str | None = None, q: str | None = None) -> list[dict]:
    CONTACTS_PEOPLE_DIR.mkdir(parents=True, exist_ok=True)
    people = []
    for path in CONTACTS_PEOPLE_DIR.glob("*.md"):
        post = frontmatter.load(path)
        person = dict(post.metadata)
        person["notes"] = post.content
        person["id"] = path.stem
        people.append(person)

    if role:
        people = [p for p in people if p.get("role") == role]
    if subject:
        people = [p for p in people if p.get("subject") == subject]
    if q:
        needle = q.lower()
        people = [p for p in people if needle in str(p.get("name", "")).lower()]

    people.sort(key=lambda p: str(p.get("name", "")).lower())
    return people


def create_person(
    name: str,
    role: str | None = None,
    subject: str | None = None,
    email: str | None = None,
    phone: str | None = None,
    notes: str = "",
) -> dict:
    CONTACTS_PEOPLE_DIR.mkdir(parents=True, exist_ok=True)
    path = _unique_path(CONTACTS_PEOPLE_DIR, slugify(name))

    metadata = {"name": name, "created": date.today().isoformat()}
    if role:
        metadata["role"] = role
    if subject:
        metadata["subject"] = subject
    if email:
        metadata["email"] = email
    if phone:
        metadata["phone"] = phone

    post = frontmatter.Post(notes, **metadata)
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    result = dict(metadata)
    result["notes"] = notes
    result["id"] = path.stem
    return result


def update_person(id_: str, **fields) -> dict:
    path = _find(CONTACTS_PEOPLE_DIR, id_)
    post = frontmatter.load(path)
    _apply_fields(post, fields)
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    result = dict(post.metadata)
    result["notes"] = post.content
    result["id"] = id_
    return result


def delete_person(id_: str) -> None:
    _find(CONTACTS_PEOPLE_DIR, id_).unlink()
    for path in CONTACTS_INTERACTIONS_DIR.glob("*.md"):
        post = frontmatter.load(path)
        if post.metadata.get("person_id") == id_:
            path.unlink()


# ---- interacciones ----

def list_interactions(person_id: str) -> list[dict]:
    CONTACTS_INTERACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    interactions = []
    for path in CONTACTS_INTERACTIONS_DIR.glob("*.md"):
        post = frontmatter.load(path)
        if post.metadata.get("person_id") != person_id:
            continue
        interaction = dict(post.metadata)
        interaction["detail"] = post.content
        interaction["id"] = path.stem
        interactions.append(interaction)

    interactions.sort(key=lambda i: str(i.get("date", "")), reverse=True)
    return interactions


def create_interaction(
    person_id: str,
    title: str,
    interaction_date: str | None = None,
    channel: str | None = None,
    detail: str = "",
) -> dict:
    CONTACTS_INTERACTIONS_DIR.mkdir(parents=True, exist_ok=True)
    interaction_date = interaction_date or date.today().isoformat()
    slug = slugify(title)
    path = _unique_path(CONTACTS_INTERACTIONS_DIR, f"{interaction_date}-{person_id}-{slug}")

    metadata = {"person_id": person_id, "title": title, "date": interaction_date}
    if channel:
        metadata["channel"] = channel

    post = frontmatter.Post(detail, **metadata)
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    result = dict(metadata)
    result["detail"] = detail
    result["id"] = path.stem
    return result


def delete_interaction(id_: str) -> None:
    _find(CONTACTS_INTERACTIONS_DIR, id_).unlink()
