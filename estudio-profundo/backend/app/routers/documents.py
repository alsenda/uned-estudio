"""Document listing, reading, import, and deletion endpoints."""

import shutil

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.config import get_settings
from app.db import get_session
from app.models import Document, Entity, Image, Inconsistency, Passage, Span
from app.schemas import DocumentFile, DocumentOut, DocumentSummary, ImageOut, PassageOut, SpanOut
from app.services import content_import, deletion, stats

router = APIRouter(prefix="/api/documents", tags=["documents"])


def images_out(session: Session, image_ids: list[str]) -> list[ImageOut]:
    if not image_ids:
        return []
    images = {img.id: img for img in session.execute(select(Image).where(Image.id.in_(image_ids))).scalars()}
    out = []
    for image_id in image_ids:
        image = images.get(image_id)
        if image is None:
            continue
        pending = image.source == "external_pending"
        display_url = image.url if pending else f"/api/images/{image.id}/file"
        out.append(
            ImageOut(
                id=image.id,
                source=image.source,
                caption=image.caption,
                display_url=display_url or "",
                pending=pending,
            )
        )
    return out


def passage_out(session: Session, passage: Passage) -> PassageOut:
    spans = session.execute(select(Span).where(Span.passage_id == passage.id).order_by(Span.start)).scalars().all()
    entity_ids = {s.entity_id for s in spans}
    entities = {
        e.id: e for e in session.execute(select(Entity).where(Entity.id.in_(entity_ids))).scalars()
    }
    span_outs = [
        SpanOut(start=s.start, end=s.end, entity_id=s.entity_id, entity_name=entities[s.entity_id].name)
        for s in spans
        if s.entity_id in entities
    ]
    return PassageOut(
        id=passage.id,
        heading=passage.heading,
        text_es=passage.text_es,
        spans=span_outs,
        images=images_out(session, passage.image_ids),
    )


def _document_summary(session: Session, document: Document, passage_count: int, entity_count: int) -> DocumentSummary:
    open_inconsistencies = session.execute(
        select(func.count(Inconsistency.id)).where(
            Inconsistency.document_id == document.id, Inconsistency.status == "open"
        )
    ).scalar_one()
    return DocumentSummary(
        id=document.id,
        title=document.title,
        source_path=document.source_path,
        passage_count=passage_count,
        entity_count=entity_count,
        mastery=stats.document_mastery(session, document.id),
        open_inconsistencies=open_inconsistencies,
    )


@router.get("")
def list_documents(session: Session = Depends(get_session)) -> list[DocumentSummary]:
    documents = session.execute(select(Document).order_by(Document.title)).scalars().all()
    out = []
    for document in documents:
        passage_count = session.execute(
            select(func.count(Passage.id)).where(Passage.document_id == document.id, Passage.kind == "content")
        ).scalar_one()
        entity_count = session.execute(
            select(func.count(Entity.id)).where(Entity.document_id == document.id)
        ).scalar_one()
        out.append(_document_summary(session, document, passage_count, entity_count))
    return out


@router.get("/{document_id}")
def get_document(document_id: str, session: Session = Depends(get_session)) -> DocumentOut:
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Unknown document.")
    passages = (
        session.execute(
            select(Passage)
            .where(Passage.document_id == document_id, Passage.kind == "content")
            .order_by(Passage.order)
        )
        .scalars()
        .all()
    )
    return DocumentOut(
        id=document.id,
        title=document.title,
        source_path=document.source_path,
        passages=[passage_out(session, p) for p in passages],
    )


@router.post("/import")
def import_document(data: DocumentFile, session: Session = Depends(get_session)) -> DocumentSummary:
    document = content_import.upsert_document(session, data)
    entity_count = session.execute(
        select(func.count(Entity.id)).where(Entity.document_id == document.id)
    ).scalar_one()
    return _document_summary(session, document, len(data.passages), entity_count)


@router.delete("/{document_id}")
def delete_document(document_id: str, session: Session = Depends(get_session)) -> dict[str, str]:
    """Remove a document completely — DB rows and its content/<slug>/ folder.

    For when a document turns out to rest on an unreliable source or a wrong
    premise: not an edit, a full removal (reader content, quiz/flashcards and
    all its answer history, images, inconsistencies)."""
    document = session.get(Document, document_id)
    if document is None:
        raise HTTPException(status_code=404, detail="Unknown document.")
    deletion.delete_document(session, document_id)

    settings = get_settings()
    content_root = settings.content_path.resolve()
    folder = (content_root / document_id).resolve()
    if folder.is_dir() and folder.parent == content_root:
        shutil.rmtree(folder)

    return {"status": "deleted"}
