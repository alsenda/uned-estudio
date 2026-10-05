from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from . import store

router = APIRouter(prefix="/api/glossary", tags=["glossary"])


class NewTerm(BaseModel):
    term: str
    definition: str = ""
    subject: str | None = None
    tags: list[str] | None = None


class UpdateTerm(BaseModel):
    term: str | None = None
    definition: str | None = None
    subject: str | None = None
    tags: list[str] | None = None


@router.get("/terms")
def get_terms(subject: str | None = None, tag: str | None = None, q: str | None = None):
    return store.list_terms(subject=subject, tag=tag, q=q)


@router.post("/terms")
def add_term(term: NewTerm):
    return store.create_term(term=term.term, definition=term.definition, subject=term.subject, tags=term.tags)


@router.patch("/terms/{term_id}")
def edit_term(term_id: str, term: UpdateTerm):
    try:
        return store.update_term(term_id, **term.model_dump(exclude_unset=True))
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="término no encontrado")


@router.delete("/terms/{term_id}", status_code=204)
def remove_term(term_id: str):
    try:
        store.delete_term(term_id)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="término no encontrado")


@router.get("/tags")
def get_tags():
    return store.list_tags()
