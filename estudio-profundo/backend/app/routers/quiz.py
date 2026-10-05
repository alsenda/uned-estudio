"""Quiz-session endpoints (vendored from quiz-app's app/routers/quiz.py, unchanged)."""

import uuid

import fsrs
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Answer, Question, QuizSession, utcnow
from app.schemas import (
    AnswerRequest,
    AnswerResult,
    QuestionType,
    SelfRating,
    SessionOut,
    SessionStartRequest,
)
from app.services import grading, question_sets, scheduling, stats

router = APIRouter(prefix="/api/quiz", tags=["quiz"])

# SelfRating's own values (schemas.py) already match fsrs.Rating's vocabulary
# 1:1 — again/hard/good/easy — so this is just a case-mapping, not a
# judgment call between two different vocabularies.
_FSRS_RATING_FOR_SELF_RATING: dict[SelfRating, fsrs.Rating] = {
    SelfRating.AGAIN: fsrs.Rating.Again,
    SelfRating.HARD: fsrs.Rating.Hard,
    SelfRating.GOOD: fsrs.Rating.Good,
    SelfRating.EASY: fsrs.Rating.Easy,
}


def _fsrs_rating_for_answer(
    question: Question, chosen_index: int | None, self_rating: SelfRating | None
) -> fsrs.Rating:
    if question.type == QuestionType.MC:
        return fsrs.Rating.Good if chosen_index == question.correct_index else fsrs.Rating.Again
    assert self_rating is not None  # enforced by grading.score_answer already
    return _FSRS_RATING_FOR_SELF_RATING[self_rating]


@router.post("/start")
def start_session(
    request: SessionStartRequest, session: Session = Depends(get_session)
) -> SessionOut:
    if request.mode == "review":
        # Interleaved daily review queue, spans every track by design (see
        # services/scheduling.due_questions()) unless the caller filtered to
        # one via `request.track`.
        _total, questions = scheduling.due_questions(
            session, limit=request.limit, track=request.track
        )
        if not questions:
            raise HTTPException(status_code=404, detail="No questions match this selection.")
        session_track = request.track or "__review__"
        quiz_session = QuizSession(
            id=str(uuid.uuid4()), track=session_track, level=None, mode=request.mode
        )
        session.add(quiz_session)
        session.commit()
        return SessionOut(
            id=quiz_session.id,
            track=quiz_session.track,
            level=quiz_session.level,
            mode=quiz_session.mode,
            questions=[question_sets.question_out(q) for q in questions],
        )

    assert request.track is not None  # enforced by SessionStartRequest's validator

    if request.mode == "level":
        if request.level is None:
            raise HTTPException(status_code=422, detail="mode 'level' requires a level")
        progress = stats.track_progress(session, request.track)
        level_info = next(lp for lp in progress.levels if lp.level == request.level)
        if not level_info.unlocked:
            raise HTTPException(
                status_code=403,
                detail=f"Level {request.level} is locked — pass level {request.level - 1} "
                f"(>={int(grading.PASS_THRESHOLD * 100)}% on at least "
                f"{int(grading.MIN_COVERAGE * 100)}% of its questions) first.",
            )

    latest = grading.latest_scores_by_question(session, request.track)
    questions = question_sets.select_questions(
        session=session,
        track=request.track,
        level=request.level,
        typicality=request.typicality,
        latest_scores=latest,
        limit=request.limit,
    )
    if not questions:
        raise HTTPException(status_code=404, detail="No questions match this selection.")

    quiz_session = QuizSession(
        id=str(uuid.uuid4()), track=request.track, level=request.level, mode=request.mode
    )
    session.add(quiz_session)
    session.commit()
    return SessionOut(
        id=quiz_session.id,
        track=quiz_session.track,
        level=quiz_session.level,
        mode=quiz_session.mode,
        questions=[question_sets.question_out(q) for q in questions],
    )


@router.post("/answer")
def submit_answer(request: AnswerRequest, session: Session = Depends(get_session)) -> AnswerResult:
    quiz_session = session.get(QuizSession, request.session_id)
    if quiz_session is None:
        raise HTTPException(status_code=404, detail="Unknown session.")
    question = session.get(Question, request.question_id)
    if question is None:
        raise HTTPException(status_code=404, detail="Unknown question.")

    try:
        score = grading.score_answer(question, request.chosen_index, request.self_rating)
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error

    session.add(
        Answer(
            session_id=quiz_session.id,
            question_id=question.id,
            score=score,
            chosen_index=request.chosen_index,
            self_rating=request.self_rating,
        )
    )
    rating = _fsrs_rating_for_answer(question, request.chosen_index, request.self_rating)
    scheduling.record_review(session, question.id, rating, utcnow())
    session.commit()
    return AnswerResult(
        question_id=question.id,
        score=score,
        correct=score >= 1.0,
        correct_index=question.correct_index,
        answer_notes=question.answer_notes,
    )


@router.post("/{session_id}/finish")
def finish_session(session_id: str, session: Session = Depends(get_session)) -> dict[str, str]:
    quiz_session = session.get(QuizSession, session_id)
    if quiz_session is None:
        raise HTTPException(status_code=404, detail="Unknown session.")
    quiz_session.finished_at = utcnow()
    session.commit()
    return {"status": "finished"}
