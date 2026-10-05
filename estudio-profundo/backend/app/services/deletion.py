"""Deleting a document completely from the system.

Unlike a re-import (which replaces a document's own content but leaves quiz
answer history alone), this removes *everything* tied to the document: its
reader content, its quiz/flashcard set and all answer history for it, its
access log entries, and any inconsistency records — for when a document turns
out to rest on an unreliable source or a wrong premise and should simply stop
existing, not just be edited.
"""

from sqlalchemy import delete
from sqlalchemy.orm import Session

from app.models import (
    AccessLog,
    Answer,
    Document,
    Entity,
    EntityRelationship,
    ExternalReference,
    Image,
    Inconsistency,
    Passage,
    Question,
    QuestionSet,
    QuestionSource,
    QuizSession,
)


def delete_document(session: Session, document_id: str) -> None:
    entity_id_subquery = session.query(Entity.id).filter(Entity.document_id == document_id)

    session.execute(delete(Inconsistency).where(Inconsistency.document_id == document_id))
    session.execute(delete(Image).where(Image.document_id == document_id))
    session.execute(
        delete(EntityRelationship).where(
            (EntityRelationship.entity_id.in_(entity_id_subquery))
            | (EntityRelationship.target_document_id == document_id)
        )
    )
    session.execute(delete(ExternalReference).where(ExternalReference.entity_id.in_(entity_id_subquery)))
    session.execute(delete(Entity).where(Entity.document_id == document_id))
    session.execute(delete(Passage).where(Passage.document_id == document_id))
    session.execute(
        delete(AccessLog).where(AccessLog.item_type == "document", AccessLog.item_id == document_id)
    )

    # Quiz side: a document's QuestionSet.id == document_id (see track = document_id).
    question_set = session.get(QuestionSet, document_id)
    if question_set is not None:
        question_id_subquery = session.query(Question.id).filter(Question.set_id == document_id)
        session.execute(delete(Answer).where(Answer.question_id.in_(question_id_subquery)))
        session.execute(delete(QuestionSource).where(QuestionSource.question_id.in_(question_id_subquery)))
        session.execute(delete(QuizSession).where(QuizSession.track == document_id))
        session.execute(delete(Question).where(Question.set_id == document_id))
        session.delete(question_set)

    session.execute(delete(Document).where(Document.id == document_id))
    session.commit()
