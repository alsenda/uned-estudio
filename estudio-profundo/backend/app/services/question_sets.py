"""Importing question sets and selecting questions for a session
(vendored from quiz-app's app/services/question_sets.py, unchanged)."""

import random

from sqlalchemy import exists, select
from sqlalchemy.orm import Session

from app.models import Answer, Question, QuestionSet, QuestionSource
from app.schemas import QuestionOut, QuestionSetFile, QuestionSourceFile, QuestionTags, TypicalityTag


def qualified_question_id(set_id: str, question_id: str) -> str:
    return f"{set_id}::{question_id}"


def upsert_question_set(session: Session, data: QuestionSetFile) -> QuestionSet:
    question_set = session.get(QuestionSet, data.id)
    if question_set is None:
        question_set = QuestionSet(id=data.id)
        session.add(question_set)
    question_set.title = data.title
    question_set.track = data.track
    question_set.level = data.level
    question_set.description = data.description

    incoming_ids = {qualified_question_id(data.id, q.id) for q in data.questions}
    existing = {
        q.id: q
        for q in session.execute(select(Question).where(Question.set_id == data.id)).scalars()
    }
    for removed_id in existing.keys() - incoming_ids:
        has_answers = session.execute(
            select(exists().where(Answer.question_id == removed_id))
        ).scalar_one()
        if not has_answers:
            session.delete(existing[removed_id])

    for file_question in data.questions:
        question_id = qualified_question_id(data.id, file_question.id)
        question = existing.get(question_id) or Question(id=question_id, set_id=data.id)
        question.type = file_question.type
        question.topic = file_question.topic
        question.prompt = file_question.prompt
        question.options = file_question.options
        question.correct_index = file_question.correct_index
        question.answer_notes = file_question.answer_notes
        question.difficulty_rationale = file_question.difficulty_rationale
        question.difficulty_tag = file_question.tags.difficulty
        question.typicality_tag = file_question.tags.typicality
        question.topic_tags = file_question.tags.topics
        ref = file_question.source
        if ref is None:
            question.source = None
        else:
            question.source = QuestionSource(
                question_id=question_id,
                document_id=ref.document_id or data.id,
                passage_id=ref.passage_id,
                entity_id=ref.entity_id,
            )
        session.add(question)

    session.commit()
    return question_set


def select_questions(
    session: Session,
    track: str,
    level: int | None,
    typicality: list[TypicalityTag] | None,
    latest_scores: dict[str, float],
    limit: int,
    rng: random.Random | None = None,
) -> list[Question]:
    rng = rng or random.Random()
    query = (
        select(Question)
        .join(QuestionSet, Question.set_id == QuestionSet.id)
        .where(QuestionSet.track == track)
    )
    if level is not None:
        query = query.where(QuestionSet.level == level)
    if typicality:
        query = query.where(Question.typicality_tag.in_([t.value for t in typicality]))
    candidates = list(session.execute(query).scalars())
    rng.shuffle(candidates)
    candidates.sort(key=lambda q: latest_scores.get(q.id, -1.0))
    return candidates[:limit]


def tags_of(question: Question) -> QuestionTags:
    return QuestionTags.model_validate(
        {
            "difficulty": question.difficulty_tag,
            "typicality": question.typicality_tag,
            "topics": question.topic_tags,
        }
    )


def question_out(question: Question) -> QuestionOut:
    """Shared DTO mapper — used by both routers/quiz.py (practice sessions)
    and routers/review.py (the cross-track due-today queue)."""
    return QuestionOut(
        id=question.id,
        set_id=question.set_id,
        type=question.type,  # type: ignore[arg-type]
        topic=question.topic,
        prompt=question.prompt,
        options=question.options,
        correct_index=question.correct_index,
        answer_notes=question.answer_notes,
        difficulty_rationale=question.difficulty_rationale,
        tags=tags_of(question),
        source=None
        if question.source is None
        else QuestionSourceFile(
            document_id=question.source.document_id,
            passage_id=question.source.passage_id,
            entity_id=question.source.entity_id,
        ),
    )
