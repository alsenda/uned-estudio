"""Scoring and progress rules (vendored from quiz-app's app/services/grading.py).

In this engine ``track`` is always a document id and there is only ever
``level=1`` per document — the level ladder is unused machinery kept as-is
so :mod:`stats` can hand back a ready-made "mastery %" per document for free.
"""

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import Answer, Question, QuestionSet
from app.schemas import SELF_RATING_SCORES, QuestionType, SelfRating

PASS_THRESHOLD = 0.8
MIN_COVERAGE = 0.5


def score_answer(
    question: Question,
    chosen_index: int | None,
    self_rating: SelfRating | None,
) -> float:
    if question.type == QuestionType.MC:
        if chosen_index is None:
            raise ValueError("multiple-choice questions require chosen_index")
        return 1.0 if chosen_index == question.correct_index else 0.0
    if self_rating is None:
        raise ValueError("flashcard questions require self_rating")
    return SELF_RATING_SCORES[self_rating]


def latest_scores_by_question(session: Session, track: str) -> dict[str, float]:
    rows = session.execute(
        select(Answer.question_id, Answer.score)
        .join(Question, Answer.question_id == Question.id)
        .join(QuestionSet, Question.set_id == QuestionSet.id)
        .where(QuestionSet.track == track)
        .order_by(Answer.answered_at, Answer.id)
    ).all()
    return {question_id: score for question_id, score in rows}


def level_question_ids(session: Session, track: str, level: int) -> list[str]:
    rows = session.execute(
        select(Question.id)
        .join(QuestionSet, Question.set_id == QuestionSet.id)
        .where(QuestionSet.track == track, QuestionSet.level == level)
    ).all()
    return [row[0] for row in rows]


def level_stats(
    question_ids: list[str], latest_scores: dict[str, float]
) -> tuple[int, float | None, bool]:
    attempted = [latest_scores[qid] for qid in question_ids if qid in latest_scores]
    if not attempted:
        return 0, None, False
    accuracy = sum(attempted) / len(attempted)
    coverage = len(attempted) / len(question_ids) if question_ids else 0.0
    passed = coverage >= MIN_COVERAGE and accuracy >= PASS_THRESHOLD
    return len(attempted), accuracy, passed
