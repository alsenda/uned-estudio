"""Validating and storing a ``document.json`` (see schemas.DocumentFile).

Ids as authored in JSON (entity/passage/image ids) are only unique *within*
one document's file — ``qid()`` qualifies them as ``"<document_id>::<id>"``
before they touch the database, so two documents can each define an entity
called e.g. ``impact`` without colliding.

Import is a full replace of the document's passages/entities/spans/
relationships/external references/images — safe because nothing else holds a
foreign key into them (quiz answer history lives in a separate table keyed by
``document_id`` as ``track``, untouched by re-importing a document).

Cross-document ``EntityRelationship`` rows may point at an entity that has not
been imported yet (documents are authored and imported one at a time). SQLite
does not enforce foreign keys unless explicitly turned on, and this project
doesn't, so this is safe to store; the entities router simply skips a
relationship whose target isn't resolvable yet.
"""

import hashlib

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import Document as DocumentModel
from app.models import Entity, EntityRelationship, ExternalReference, Image, Inconsistency, Passage, Span
from app.schemas import DocumentFile, PassageFile, SpanFile


def qid(document_id: str, raw_id: str) -> str:
    """Qualify a bare id (as authored in document.json) with its document id."""
    return f"{document_id}::{raw_id}"


def upsert_document(session: Session, data: DocumentFile) -> DocumentModel:
    content_hash = hashlib.sha256(data.model_dump_json().encode("utf-8")).hexdigest()

    document = session.get(DocumentModel, data.id)
    if document is None:
        document = DocumentModel(
            id=data.id, title=data.title, source_path=data.source_path, content_hash=content_hash
        )
        session.add(document)
    else:
        entity_id_subquery = session.query(Entity.id).filter(Entity.document_id == data.id)
        passage_id_subquery = session.query(Passage.id).filter(Passage.document_id == data.id)
        # Span has no FK cascade (SQLite doesn't enforce them here), and
        # passage/entity ids are deterministic (qid()), so without this
        # explicit delete, re-importing the same document over and over
        # would silently accumulate duplicate spans on every re-seed.
        session.execute(delete(Span).where(Span.passage_id.in_(passage_id_subquery)))
        session.execute(delete(Image).where(Image.document_id == data.id))
        session.execute(delete(Inconsistency).where(Inconsistency.document_id == data.id))
        session.execute(
            delete(EntityRelationship).where(EntityRelationship.entity_id.in_(entity_id_subquery))
        )
        session.execute(
            delete(ExternalReference).where(ExternalReference.entity_id.in_(entity_id_subquery))
        )
        session.execute(delete(Entity).where(Entity.document_id == data.id))
        session.execute(delete(Passage).where(Passage.document_id == data.id))
        document.title = data.title
        document.source_path = data.source_path
        document.content_hash = content_hash
    session.flush()

    # Entities (+ their description passages) first, so cross-document
    # relationships have a stable id to point at regardless of import order.
    for entity_file in data.entities:
        entity_id = qid(data.id, entity_file.id)
        desc_passage_id = qid(data.id, f"entity::{entity_file.id}")
        session.add(
            Passage(
                id=desc_passage_id,
                document_id=data.id,
                kind="entity_description",
                order=0,
                heading=None,
                text_es=entity_file.description_es,
                image_ids=[qid(data.id, i) for i in entity_file.image_ids],
            )
        )
        session.add(
            Entity(
                id=entity_id,
                document_id=data.id,
                name=entity_file.name,
                level=entity_file.level,
                description_passage_id=desc_passage_id,
            )
        )
        for span in entity_file.description_spans:
            session.add(_span_row(data.id, desc_passage_id, span))
        for ref in entity_file.external_references:
            session.add(ExternalReference(entity_id=entity_id, label=ref.label, url=ref.url))
        for rel in entity_file.relationships:
            session.add(
                EntityRelationship(
                    entity_id=entity_id,
                    target_entity_id=qid(rel.target_document_id, rel.target_entity_id),
                    target_document_id=rel.target_document_id,
                    label=rel.label,
                )
            )
    session.flush()

    for image_file in data.images:
        local_path = (
            f"{data.id}/images/{image_file.local_filename}" if image_file.local_filename else None
        )
        session.add(
            Image(
                id=qid(data.id, image_file.id),
                document_id=data.id,
                source=image_file.source,
                url=image_file.url,
                local_path=local_path,
                caption=image_file.caption,
            )
        )

    for order, passage_file in enumerate(data.passages):
        _add_content_passage(session, data.id, order, passage_file)

    for inconsistency in data.inconsistencies:
        session.add(
            Inconsistency(
                document_id=data.id,
                entity_id=qid(data.id, inconsistency.entity_id),
                summary=inconsistency.summary,
                mention_a_location=inconsistency.mention_a_location,
                mention_a_quote=inconsistency.mention_a_quote,
                mention_b_location=inconsistency.mention_b_location,
                mention_b_quote=inconsistency.mention_b_quote,
            )
        )

    session.commit()
    return document


def _add_content_passage(
    session: Session, document_id: str, order: int, passage_file: PassageFile
) -> None:
    passage_id = qid(document_id, passage_file.id)
    session.add(
        Passage(
            id=passage_id,
            document_id=document_id,
            kind="content",
            order=order,
            heading=passage_file.heading,
            text_es=passage_file.text_es,
            image_ids=[qid(document_id, i) for i in passage_file.image_ids],
        )
    )
    for span in passage_file.spans:
        session.add(_span_row(document_id, passage_id, span))


def _span_row(document_id: str, passage_id: str, span: SpanFile) -> Span:
    return Span(
        passage_id=passage_id, start=span.start, end=span.end, entity_id=qid(document_id, span.entity_id)
    )
