from fastapi import APIRouter
from pydantic import BaseModel

from . import news, store

router = APIRouter(prefix="/api/feed", tags=["feed"])


class NewEntry(BaseModel):
    title: str
    content: str
    type: str = "diario"
    subject: str | None = None
    tags: list[str] | None = None
    source_url: str | None = None


@router.get("")
def get_feed(type: str | None = None, subject: str | None = None, limit: int = 50):
    return store.list_entries(type_=type, subject=subject, limit=limit)


@router.post("/entries")
def add_entry(entry: NewEntry):
    return store.create_entry(
        title=entry.title,
        content=entry.content,
        type_=entry.type,
        subject=entry.subject,
        tags=entry.tags,
        source_url=entry.source_url,
    )


@router.post("/refresh-news")
def refresh_news():
    return news.refresh_news()
