"""SQLAlchemy ORM models.

Two families of tables:

- ``question_sets`` / ``questions`` / ``quiz_sessions`` / ``answers``: the quiz
  and flashcard engine, vendored near-verbatim from ``quiz-app`` (same schema,
  same grading/progress rules — see ``app/services/``). One ``QuestionSet`` per
  document, always at ``level=1`` (the level-gate ladder is unused here, we
  just get a free "mastery %" per document out of ``track_progress``).

- ``documents`` / ``passages`` / ``spans`` / ``entities`` / ...: the annotated
  reader. The key idea that makes nested modals possible: an entity's
  description is *itself* a ``Passage`` (``kind="entity_description"``) with
  its own ``Span`` rows, so opening a highlighted term always means "fetch an
  entity, then render its description passage the same way as any other
  passage" — recursively, with no fixed depth limit.
"""

from datetime import UTC, datetime

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Declarative base for all models."""


# ---------------------------------------------------------------------------
# Quiz / flashcard engine (vendored from quiz-app)
# ---------------------------------------------------------------------------


class QuestionSet(Base):
    __tablename__ = "question_sets"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)
    title: Mapped[str] = mapped_column(String(200))
    track: Mapped[str] = mapped_column(String(120), index=True)  # = document_id here
    level: Mapped[int] = mapped_column(Integer, index=True)  # always 1 in this engine
    description: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    questions: Mapped[list["Question"]] = relationship(
        back_populates="question_set", cascade="all, delete-orphan"
    )


class Question(Base):
    __tablename__ = "questions"

    id: Mapped[str] = mapped_column(String(200), primary_key=True)
    set_id: Mapped[str] = mapped_column(ForeignKey("question_sets.id"), index=True)
    type: Mapped[str] = mapped_column(String(20))  # "mc" | "flashcard"
    topic: Mapped[str] = mapped_column(String(120), index=True)
    prompt: Mapped[str] = mapped_column(Text)
    options: Mapped[list[str] | None] = mapped_column(JSON, default=None)
    correct_index: Mapped[int | None] = mapped_column(Integer, default=None)
    answer_notes: Mapped[str] = mapped_column(Text)
    difficulty_rationale: Mapped[str] = mapped_column(Text)
    difficulty_tag: Mapped[str] = mapped_column(String(20), index=True)
    typicality_tag: Mapped[str] = mapped_column(String(20), index=True)
    topic_tags: Mapped[list[str]] = mapped_column(JSON, default=list)

    question_set: Mapped[QuestionSet] = relationship(back_populates="questions")
    source: Mapped["QuestionSource | None"] = relationship(
        uselist=False, lazy="joined", cascade="all, delete-orphan"
    )


class QuestionSource(Base):
    """Where in the annotated document a question comes from (optional): the
    passage to scroll to and, if any, the entity card to open. A sibling table,
    not columns on ``Question``, for the same no-migrations reason as
    ``CardState`` below: ``create_all`` adds new tables to an existing DB."""

    __tablename__ = "question_sources"

    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), primary_key=True)
    document_id: Mapped[str] = mapped_column(String(200))
    passage_id: Mapped[str] = mapped_column(String(200))
    entity_id: Mapped[str | None] = mapped_column(String(200), default=None)


class CardState(Base):
    """FSRS scheduling state for one question — one row per ``Question``, created
    lazily the first time it's reviewed (see ``services/scheduling.py``). A
    question with no row here is treated as new/due-now, exactly like a fresh
    ``fsrs.Card()`` — so pre-existing questions need no backfill to enter the
    review queue. Kept as a sibling table rather than new columns on
    ``Question``/``Answer`` because this project has no migration tooling
    (``init_db`` only calls ``Base.metadata.create_all``, which creates new
    tables but never alters existing ones)."""

    __tablename__ = "card_states"

    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), primary_key=True)
    state: Mapped[str] = mapped_column(String(12))  # "learning" | "review" | "relearning"
    step: Mapped[int | None] = mapped_column(Integer, default=None)
    stability: Mapped[float | None] = mapped_column(Float, default=None)
    difficulty: Mapped[float | None] = mapped_column(Float, default=None)
    due_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    last_reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
    reps: Mapped[int] = mapped_column(Integer, default=0)
    lapses: Mapped[int] = mapped_column(Integer, default=0)
    last_rating: Mapped[int | None] = mapped_column(Integer, default=None)  # fsrs.Rating value, 1-4


class QuizSession(Base):
    __tablename__ = "quiz_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True)  # uuid4
    track: Mapped[str] = mapped_column(String(120), index=True)
    level: Mapped[int | None] = mapped_column(Integer, default=None)
    mode: Mapped[str] = mapped_column(String(30))  # "level" | "typical-drill" | "custom"
    started_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    finished_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)

    answers: Mapped[list["Answer"]] = relationship(
        back_populates="session", cascade="all, delete-orphan"
    )


class Answer(Base):
    __tablename__ = "answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    session_id: Mapped[str] = mapped_column(ForeignKey("quiz_sessions.id"), index=True)
    question_id: Mapped[str] = mapped_column(ForeignKey("questions.id"), index=True)
    score: Mapped[float] = mapped_column(Float)
    chosen_index: Mapped[int | None] = mapped_column(Integer, default=None)
    self_rating: Mapped[str | None] = mapped_column(String(10), default=None)
    answered_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)

    session: Mapped[QuizSession] = relationship(back_populates="answers")


# ---------------------------------------------------------------------------
# Annotated reader
# ---------------------------------------------------------------------------


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[str] = mapped_column(String(120), primary_key=True)  # slug
    title: Mapped[str] = mapped_column(String(200))
    source_path: Mapped[str] = mapped_column(String(400))  # relative path in the source docs/ tree
    content_hash: Mapped[str] = mapped_column(String(64))  # sha256 of the imported JSON
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    passages: Mapped[list["Passage"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )
    entities: Mapped[list["Entity"]] = relationship(
        back_populates="document", cascade="all, delete-orphan"
    )


class Passage(Base):
    __tablename__ = "passages"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    kind: Mapped[str] = mapped_column(String(20))  # "content" | "entity_description"
    order: Mapped[int] = mapped_column(Integer, default=0)  # reading order within the document
    heading: Mapped[str | None] = mapped_column(String(200), default=None)
    text_es: Mapped[str] = mapped_column(Text)
    image_ids: Mapped[list[str]] = mapped_column(JSON, default=list)  # qualified Image.id values

    document: Mapped[Document] = relationship(back_populates="passages")
    spans: Mapped[list["Span"]] = relationship(
        back_populates="passage", cascade="all, delete-orphan", order_by="Span.start"
    )


class Entity(Base):
    __tablename__ = "entities"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)  # slug, unique across documents
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    name: Mapped[str] = mapped_column(String(200))
    level: Mapped[int] = mapped_column(Integer, default=1)  # 1 = highlighted directly in the text
    description_passage_id: Mapped[str] = mapped_column(ForeignKey("passages.id"))

    document: Mapped[Document] = relationship(back_populates="entities")
    description_passage: Mapped[Passage] = relationship(foreign_keys=[description_passage_id])
    relationships_out: Mapped[list["EntityRelationship"]] = relationship(
        back_populates="entity",
        cascade="all, delete-orphan",
        foreign_keys="EntityRelationship.entity_id",
    )
    external_references: Mapped[list["ExternalReference"]] = relationship(
        back_populates="entity", cascade="all, delete-orphan"
    )


class Span(Base):
    __tablename__ = "spans"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    passage_id: Mapped[str] = mapped_column(ForeignKey("passages.id"), index=True)
    start: Mapped[int] = mapped_column(Integer)  # character offset into passage.text_es
    end: Mapped[int] = mapped_column(Integer)
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)

    passage: Mapped[Passage] = relationship(back_populates="spans")


class EntityRelationship(Base):
    __tablename__ = "entity_relationships"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    target_entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    target_document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"))
    label: Mapped[str] = mapped_column(String(200))

    entity: Mapped[Entity] = relationship(
        back_populates="relationships_out", foreign_keys=[entity_id]
    )


class ExternalReference(Base):
    __tablename__ = "external_references"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    label: Mapped[str] = mapped_column(String(300))
    url: Mapped[str] = mapped_column(String(600))

    entity: Mapped[Entity] = relationship(back_populates="external_references")


class Image(Base):
    """An image belongs to whichever Passage(s) list its id in ``image_ids`` —
    no FK here, since one image can illustrate both a content passage and an
    entity's description passage."""

    __tablename__ = "images"

    id: Mapped[str] = mapped_column(String(160), primary_key=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    # "document" (extracted from the source PDF) | "external_pending" (awaiting
    # user confirmation, not yet downloaded) | "external_confirmed" (downloaded
    # and persisted after confirmation)
    source: Mapped[str] = mapped_column(String(20))
    url: Mapped[str | None] = mapped_column(String(600), default=None)
    local_path: Mapped[str | None] = mapped_column(String(400), default=None)
    caption: Mapped[str | None] = mapped_column(String(300), default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)


class Setting(Base):
    """A tiny key-value store for the handful of user preferences this app
    needs (currently just the daily review goal) — this repo is entirely
    SQLAlchemy/SQLite internally (unlike UNED, which mixes in JSONL files),
    so a settings table fits its own conventions better than a JSON file."""

    __tablename__ = "settings"

    key: Mapped[str] = mapped_column(String(60), primary_key=True)
    value: Mapped[str] = mapped_column(String(200))


class AccessLog(Base):
    __tablename__ = "access_log"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    item_type: Mapped[str] = mapped_column(String(20))  # "document"
    item_id: Mapped[str] = mapped_column(String(160), index=True)
    viewed_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)


class Inconsistency(Base):
    """A contradiction between two mentions of the same entity within one
    document, found while authoring (cross-checking every mention against
    every other, not just proofreading each in isolation). ``mention_a`` /
    ``mention_b`` are free-text location + quote pairs rather than FKs to a
    passage, so a mention can point at a content passage, an entity's own
    description, or a quiz question — anywhere the claim was made."""

    __tablename__ = "inconsistencies"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    document_id: Mapped[str] = mapped_column(ForeignKey("documents.id"), index=True)
    entity_id: Mapped[str] = mapped_column(ForeignKey("entities.id"), index=True)
    summary: Mapped[str] = mapped_column(Text)
    mention_a_location: Mapped[str] = mapped_column(String(200))
    mention_a_quote: Mapped[str] = mapped_column(Text)
    mention_b_location: Mapped[str] = mapped_column(String(200))
    mention_b_quote: Mapped[str] = mapped_column(Text)
    # "open" | "resolved_a" | "resolved_b" | "resolved_ai" | "dismissed"
    status: Mapped[str] = mapped_column(String(20), default="open", index=True)
    resolution_note: Mapped[str | None] = mapped_column(Text, default=None)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime, default=None)
