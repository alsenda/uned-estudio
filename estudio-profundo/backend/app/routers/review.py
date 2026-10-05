"""The daily review queue — how many questions are due across every track
right now, for the home-page "hoy toca repasar" badge (see
services/scheduling.due_questions() for the interleaving logic)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import DueQueueOut
from app.services import question_sets, scheduling

router = APIRouter(prefix="/api/review", tags=["review"])


@router.get("/due")
def get_due_queue(
    limit: int = 20, track: str | None = None, session: Session = Depends(get_session)
) -> DueQueueOut:
    count_due, questions = scheduling.due_questions(session, limit=limit, track=track)
    return DueQueueOut(
        count_due=count_due,
        questions=[question_sets.question_out(q) for q in questions],
    )
