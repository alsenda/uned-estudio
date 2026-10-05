"""Entity detail endpoint — what a highlighted term's modal renders.

The description is itself a :class:`Passage`, rendered by the exact same
``documents.passage_out`` helper as any other passage, so its own highlighted
spans are just as clickable — this is what gives the reader unbounded nesting
depth instead of a single fixed-depth modal.
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Document, Entity, EntityRelationship, ExternalReference, Passage
from app.routers.documents import passage_out
from app.schemas import EntityOut, ExternalReferenceOut, RelationshipOut

router = APIRouter(prefix="/api/entities", tags=["entities"])


@router.get("/{entity_id}")
def get_entity(entity_id: str, session: Session = Depends(get_session)) -> EntityOut:
    entity = session.get(Entity, entity_id)
    if entity is None:
        raise HTTPException(status_code=404, detail="Unknown entity.")

    description_passage = session.get(Passage, entity.description_passage_id)
    document = session.get(Document, entity.document_id)

    relationships_out: list[RelationshipOut] = []
    for rel in session.execute(
        select(EntityRelationship).where(EntityRelationship.entity_id == entity_id)
    ).scalars():
        target = session.get(Entity, rel.target_entity_id)
        target_document = session.get(Document, rel.target_document_id)
        if target is None or target_document is None:
            continue  # target not imported yet — skip rather than break the modal
        relationships_out.append(
            RelationshipOut(
                target_entity_id=target.id,
                target_entity_name=target.name,
                target_document_id=target_document.id,
                target_document_title=target_document.title,
                label=rel.label,
            )
        )

    external_refs = [
        ExternalReferenceOut(label=r.label, url=r.url)
        for r in session.execute(
            select(ExternalReference).where(ExternalReference.entity_id == entity_id)
        ).scalars()
    ]

    return EntityOut(
        id=entity.id,
        name=entity.name,
        level=entity.level,
        document_id=entity.document_id,
        document_title=document.title if document else "",
        description=passage_out(session, description_passage),
        relationships=relationships_out,
        external_references=external_refs,
    )
