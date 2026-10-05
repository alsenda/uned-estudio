"""Engagement layer: streak, XP, per-subject badges and a new/learning/
review/mastered progress breakdown — all derived at query time from
Answer/CardState, no persisted "unlocked" state. A badge simply appears once
its underlying condition is true (and would disappear if it stopped being
true) — nothing to get out of sync, nothing to punish. The only thing
actually persisted is the user's daily review goal (see Setting)."""

from datetime import UTC, date, datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Answer, CardState, Question, QuestionSet, Setting
from app.schemas import Badge, DailyGoalRequest, EngagementSummary, ProgressBuckets

router = APIRouter(prefix="/api/engagement", tags=["engagement"])

DEFAULT_DAILY_GOAL = 15
MASTERED_STABILITY_DAYS = 21.0
MASTERY_BADGE_THRESHOLDS = (50, 25, 10)
STREAK_BADGE_THRESHOLDS = (30, 14, 7)
_DAILY_GOAL_KEY = "daily_goal"


def get_daily_goal(session: Session) -> int:
    row = session.get(Setting, _DAILY_GOAL_KEY)
    if row is None:
        return DEFAULT_DAILY_GOAL
    try:
        return int(row.value)
    except ValueError:
        return DEFAULT_DAILY_GOAL


def set_daily_goal(session: Session, value: int) -> None:
    row = session.get(Setting, _DAILY_GOAL_KEY)
    if row is None:
        row = Setting(key=_DAILY_GOAL_KEY, value=str(value))
        session.add(row)
    else:
        row.value = str(value)
    session.commit()


def _answers_per_day(session: Session) -> dict[date, int]:
    rows = session.execute(
        select(func.date(Answer.answered_at), func.count(Answer.id)).group_by(func.date(Answer.answered_at))
    ).all()
    return {datetime.strptime(d, "%Y-%m-%d").date(): c for d, c in rows if d}


def _streak_days(counts: dict[date, int], daily_goal: int, today: date) -> int:
    # Today doesn't have to be "done" yet to keep the streak alive — the day
    # isn't over. Positive framing on purpose: nothing here ever shows a
    # broken/lost streak, it just quietly starts counting from 0 again.
    day = today if counts.get(today, 0) >= daily_goal else today - timedelta(days=1)
    streak = 0
    while counts.get(day, 0) >= daily_goal:
        streak += 1
        day -= timedelta(days=1)
    return streak


def _progress_buckets(session: Session) -> ProgressBuckets:
    total_questions = session.execute(select(func.count(Question.id))).scalar_one()
    rows = session.execute(select(CardState.state, CardState.stability)).all()
    learning = review = mastered = 0
    for state, stability in rows:
        if state == "review" and (stability or 0) >= MASTERED_STABILITY_DAYS:
            mastered += 1
        elif state == "review":
            review += 1
        else:
            learning += 1
    new = max(0, total_questions - len(rows))
    return ProgressBuckets(new=new, learning=learning, review=review, mastered=mastered)


def _badges(session: Session, streak: int) -> list[Badge]:
    badges: list[Badge] = []
    for track, title in session.execute(select(QuestionSet.track, QuestionSet.title).distinct()).all():
        answered = session.execute(
            select(func.count(Answer.id))
            .join(Question, Answer.question_id == Question.id)
            .join(QuestionSet, Question.set_id == QuestionSet.id)
            .where(QuestionSet.track == track)
        ).scalar_one()
        if answered > 0:
            badges.append(Badge(id=f"{track}-first-session", label=f"Primera sesión: {title}", subject=title))

        mastered_count = session.execute(
            select(func.count(CardState.question_id))
            .join(Question, CardState.question_id == Question.id)
            .join(QuestionSet, Question.set_id == QuestionSet.id)
            .where(
                QuestionSet.track == track,
                CardState.state == "review",
                CardState.stability >= MASTERED_STABILITY_DAYS,
            )
        ).scalar_one()
        for threshold in MASTERY_BADGE_THRESHOLDS:
            if mastered_count >= threshold:
                badges.append(
                    Badge(id=f"{track}-mastered-{threshold}", label=f"{threshold} dominadas: {title}", subject=title)
                )
                break

    for threshold in STREAK_BADGE_THRESHOLDS:
        if streak >= threshold:
            badges.append(Badge(id=f"streak-{threshold}", label=f"Racha de {threshold} días", subject=None))
            break

    return badges


@router.get("/summary")
def get_summary(session: Session = Depends(get_session)) -> EngagementSummary:
    daily_goal = get_daily_goal(session)
    today = datetime.now(UTC).date()
    counts = _answers_per_day(session)
    streak = _streak_days(counts, daily_goal, today)
    total_answers = session.execute(select(func.count(Answer.id))).scalar_one()
    return EngagementSummary(
        streak_days=streak,
        xp=total_answers * 10 + streak * 5,
        daily_goal=daily_goal,
        reviewed_today=counts.get(today, 0),
        buckets=_progress_buckets(session),
        badges=_badges(session, streak),
    )


@router.put("/daily-goal")
def put_daily_goal(request: DailyGoalRequest, session: Session = Depends(get_session)) -> dict[str, int]:
    set_daily_goal(session, request.value)
    return {"daily_goal": request.value}
