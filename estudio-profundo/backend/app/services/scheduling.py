"""FSRS-based spaced-repetition scheduling.

Layered on top of the existing Answer log, not a replacement for it: ``Answer``
stays the immutable raw record ``grading.py``/``stats.py`` already use
unchanged. ``CardState`` is the *derived*, incrementally-updated "current
scheduling position" for a question — recomputing it from scratch by
replaying the full ``Answer`` history through FSRS's stateful recurrence on
every ``/api/review/due`` call would get slower every year as the degree's
content grows; updating it once per answer, in the same transaction, is O(1)
instead. A question with no ``CardState`` row is treated as new/due-now
(equivalent to a fresh ``fsrs.Card()``), so pre-existing content needs no
backfill to enter the review queue.

SQLite has no real datetime type, so SQLAlchemy round-trips naive datetimes
here even though the rest of the app writes timezone-aware UTC values; fsrs,
on the other hand, requires timezone-aware datetimes internally for its
elapsed-time math. ``_to_naive``/``_to_aware`` are the seam between the two.
"""

import random
from datetime import UTC, datetime

import fsrs
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models import CardState, Question, QuestionSet

_scheduler = fsrs.Scheduler()

_STATE_BY_NAME: dict[str, fsrs.State] = {
    "learning": fsrs.State.Learning,
    "review": fsrs.State.Review,
    "relearning": fsrs.State.Relearning,
}
_NAME_BY_STATE = {v: k for k, v in _STATE_BY_NAME.items()}


def _to_naive(dt: datetime) -> datetime:
    return dt.astimezone(UTC).replace(tzinfo=None) if dt.tzinfo else dt


def _to_aware(dt: datetime) -> datetime:
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def _card_from_state(card_state: CardState | None) -> fsrs.Card:
    if card_state is None:
        return fsrs.Card()
    return fsrs.Card(
        state=_STATE_BY_NAME[card_state.state],
        step=card_state.step,
        stability=card_state.stability,
        difficulty=card_state.difficulty,
        due=_to_aware(card_state.due_at),
        last_review=_to_aware(card_state.last_reviewed_at) if card_state.last_reviewed_at else None,
    )


def record_review(
    session: Session, question_id: str, rating: fsrs.Rating, now: datetime
) -> CardState:
    """Advance (or create) ``question_id``'s scheduling state per ``rating``."""
    card_state = session.get(CardState, question_id)
    card = _card_from_state(card_state)
    card, _log = _scheduler.review_card(card, rating, review_datetime=_to_aware(now))

    if card_state is None:
        card_state = CardState(question_id=question_id, reps=0, lapses=0)
        session.add(card_state)
    card_state.state = _NAME_BY_STATE[card.state]
    card_state.step = card.step
    card_state.stability = card.stability
    card_state.difficulty = card.difficulty
    card_state.due_at = _to_naive(card.due)
    card_state.last_reviewed_at = _to_naive(card.last_review) if card.last_review else None
    card_state.reps += 1
    if rating == fsrs.Rating.Again:
        card_state.lapses += 1
    card_state.last_rating = int(rating)
    return card_state


def due_questions(
    session: Session, limit: int, track: str | None = None, now: datetime | None = None
) -> tuple[int, list[Question]]:
    """Cross-track by design (interleaving) unless ``track`` filters to one.
    Returns ``(total_due_count, capped_question_list)`` — the total is
    unbounded (for a home-page badge), the list is capped at ``limit``."""
    now_naive = _to_naive(now or datetime.now(UTC))
    query = (
        select(Question)
        .join(QuestionSet, Question.set_id == QuestionSet.id)
        .outerjoin(CardState, Question.id == CardState.question_id)
        .where(or_(CardState.question_id.is_(None), CardState.due_at <= now_naive))
    )
    if track:
        query = query.where(QuestionSet.track == track)
    candidates = list(session.execute(query).scalars())
    random.shuffle(candidates)  # break same-day-due ties so items don't cluster by document
    return len(candidates), candidates[:limit]
