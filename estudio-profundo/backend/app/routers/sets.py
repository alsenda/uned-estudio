"""Question-set endpoints (vendored from quiz-app's app/routers/sets.py, unchanged)."""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Question, QuestionSet
from app.schemas import QuestionOut, QuestionSetFile, QuestionSetSummary
from app.services import question_sets

router = APIRouter(prefix="/api/sets", tags=["question-sets"])


@router.get("")
def list_sets(session: Session = Depends(get_session)) -> list[QuestionSetSummary]:
    rows = session.execute(
        select(QuestionSet, func.count(Question.id))
        .outerjoin(Question, Question.set_id == QuestionSet.id)
        .group_by(QuestionSet.id)
        .order_by(QuestionSet.track, QuestionSet.level, QuestionSet.id)
    ).all()
    return [
        QuestionSetSummary(
            id=qs.id,
            title=qs.title,
            track=qs.track,
            level=qs.level,
            description=qs.description,
            question_count=count,
        )
        for qs, count in rows
    ]


@router.get("/{set_id}/questions")
def list_set_questions(set_id: str, session: Session = Depends(get_session)) -> list[QuestionOut]:
    """Solo lectura: las preguntas de un cuestionario, para hojearlas sin abrir una sesión de
    práctica (una sesión registraría respuestas y movería el progreso). Lo usa la web de UNED."""
    rows = session.execute(select(Question).where(Question.set_id == set_id).order_by(Question.id)).scalars().all()
    if not rows:
        raise HTTPException(status_code=404, detail="cuestionario no encontrado")
    return [question_sets.question_out(q) for q in rows]


@router.post("/import")
def import_set(
    data: QuestionSetFile, session: Session = Depends(get_session)
) -> QuestionSetSummary:
    question_set = question_sets.upsert_question_set(session, data)
    return QuestionSetSummary(
        id=question_set.id,
        title=question_set.title,
        track=question_set.track,
        level=question_set.level,
        description=question_set.description,
        question_count=len(data.questions),
    )
