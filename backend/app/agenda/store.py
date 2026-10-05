import re
import unicodedata
from datetime import date
from pathlib import Path

import frontmatter

from ..config import AGENDA_EVENTS_DIR, AGENDA_TODOS_DIR


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^a-zA-Z0-9]+", "-", text).strip("-").lower()
    return text or "item"


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
    description = fields.pop("description", None)
    for key, value in fields.items():
        if value is None:
            post.metadata.pop(key, None)
        else:
            post.metadata[key] = value
    if description is not None:
        post.content = description


# ---- eventos ----

def list_events(start: str | None = None, end: str | None = None, subject: str | None = None) -> list[dict]:
    AGENDA_EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    events = []
    for path in AGENDA_EVENTS_DIR.glob("*.md"):
        post = frontmatter.load(path)
        event = dict(post.metadata)
        event["description"] = post.content
        event["id"] = path.stem
        event.setdefault("type", "otro")
        events.append(event)

    if start:
        events = [e for e in events if str(e.get("date", "")) >= start]
    if end:
        events = [e for e in events if str(e.get("date", "")) <= end]
    if subject:
        events = [e for e in events if e.get("subject") == subject]

    events.sort(key=lambda e: (str(e.get("date", "")), str(e.get("time", ""))))
    return events


def create_event(
    title: str,
    date_: str,
    time: str | None = None,
    type_: str = "otro",
    subject: str | None = None,
    links: list[str] | None = None,
    description: str = "",
) -> dict:
    AGENDA_EVENTS_DIR.mkdir(parents=True, exist_ok=True)
    slug = slugify(title)
    path = _unique_path(AGENDA_EVENTS_DIR, f"{date_}-{slug}")

    metadata = {"title": title, "date": date_, "type": type_}
    if time:
        metadata["time"] = time
    if subject:
        metadata["subject"] = subject
    if links:
        metadata["links"] = links

    post = frontmatter.Post(description, **metadata)
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    result = dict(metadata)
    result["description"] = description
    result["id"] = path.stem
    return result


def update_event(id_: str, **fields) -> dict:
    path = _find(AGENDA_EVENTS_DIR, id_)
    post = frontmatter.load(path)
    _apply_fields(post, fields)
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    result = dict(post.metadata)
    result["description"] = post.content
    result["id"] = id_
    return result


def delete_event(id_: str) -> None:
    _find(AGENDA_EVENTS_DIR, id_).unlink()


# ---- todos ----

def list_todos(done: bool | None = None, subject: str | None = None) -> list[dict]:
    AGENDA_TODOS_DIR.mkdir(parents=True, exist_ok=True)
    todos = []
    for path in AGENDA_TODOS_DIR.glob("*.md"):
        post = frontmatter.load(path)
        todo = dict(post.metadata)
        todo["description"] = post.content
        todo["id"] = path.stem
        todo.setdefault("done", False)
        todos.append(todo)

    if done is not None:
        todos = [t for t in todos if bool(t.get("done")) == done]
    if subject:
        todos = [t for t in todos if t.get("subject") == subject]

    todos.sort(key=lambda t: (t.get("due_date") is None, str(t.get("due_date", "")), str(t.get("created", ""))))
    return todos


def create_todo(
    title: str,
    due_date: str | None = None,
    subject: str | None = None,
    links: list[str] | None = None,
    description: str = "",
) -> dict:
    AGENDA_TODOS_DIR.mkdir(parents=True, exist_ok=True)
    created = date.today().isoformat()
    slug = slugify(title)
    path = _unique_path(AGENDA_TODOS_DIR, f"{due_date or created}-{slug}")

    metadata = {"title": title, "done": False, "created": created}
    if due_date:
        metadata["due_date"] = due_date
    if subject:
        metadata["subject"] = subject
    if links:
        metadata["links"] = links

    post = frontmatter.Post(description, **metadata)
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    result = dict(metadata)
    result["description"] = description
    result["id"] = path.stem
    return result


def update_todo(id_: str, **fields) -> dict:
    path = _find(AGENDA_TODOS_DIR, id_)
    post = frontmatter.load(path)

    if "done" in fields and fields["done"] is not None:
        done = fields.pop("done")
        post.metadata["done"] = done
        if done:
            post.metadata["done_at"] = date.today().isoformat()
        else:
            post.metadata.pop("done_at", None)

    _apply_fields(post, fields)
    path.write_bytes(frontmatter.dumps(post).encode("utf-8"))

    result = dict(post.metadata)
    result["description"] = post.content
    result["id"] = id_
    return result


def delete_todo(id_: str) -> None:
    _find(AGENDA_TODOS_DIR, id_).unlink()
