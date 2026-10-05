"""Pydantic schemas.

Two import contracts, both plain JSON files under ``content/<slug>/``:

- ``quiz.json`` validates against :class:`QuestionSetFile` — vendored
  verbatim from ``quiz-app``, so its ``scripts/seed.py``-style tooling and
  this engine's stay interchangeable.
- ``document.json`` validates against :class:`DocumentFile` — the annotated
  reader's contract: passages of simplified Spanish text, character-offset
  spans pointing at entities, entities whose own description is itself
  annotated text (recursion, not a fixed depth), relationships (possibly
  cross-document), external references, and images (from the source PDF or
  pending confirmation from the internet).
"""

from datetime import datetime
from enum import StrEnum

from pydantic import BaseModel, Field, model_validator

# ---------------------------------------------------------------------------
# Quiz / flashcards (vendored from quiz-app)
# ---------------------------------------------------------------------------


class QuestionType(StrEnum):
    MC = "mc"
    FLASHCARD = "flashcard"


class DifficultyTag(StrEnum):
    BASIC = "basic"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"
    ULTRA_EXPERT = "ultra-expert"


class TypicalityTag(StrEnum):
    """How central this question is to understanding the document."""

    STAPLE = "staple"  # core idea, must know
    COMMON = "common"
    OCCASIONAL = "occasional"
    CURVEBALL = "curveball"  # rare/tricky detail


class SelfRating(StrEnum):
    """Matches fsrs.Rating's own four-way scale (see services/scheduling.py) so
    a flashcard self-rating feeds the spaced-repetition scheduler directly,
    with no separate mapping table between two different vocabularies."""

    AGAIN = "again"
    HARD = "hard"
    GOOD = "good"
    EASY = "easy"


SELF_RATING_SCORES: dict[SelfRating, float] = {
    SelfRating.AGAIN: 0.0,
    SelfRating.HARD: 0.4,
    SelfRating.GOOD: 0.8,
    SelfRating.EASY: 1.0,
}

DIFFICULTY_FOR_LEVEL: dict[int, DifficultyTag] = {
    1: DifficultyTag.BASIC,
    2: DifficultyTag.INTERMEDIATE,
    3: DifficultyTag.ADVANCED,
    4: DifficultyTag.EXPERT,
    5: DifficultyTag.ULTRA_EXPERT,
}


class QuestionTags(BaseModel):
    difficulty: DifficultyTag
    typicality: TypicalityTag
    topics: list[str] = Field(default_factory=list, max_length=8)


class QuestionFile(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,60}$")
    type: QuestionType
    topic: str = Field(min_length=2, max_length=120)
    prompt: str = Field(min_length=10)
    options: list[str] | None = Field(default=None, min_length=2, max_length=6)
    correct_index: int | None = None
    answer_notes: str = Field(min_length=10)
    difficulty_rationale: str = Field(min_length=5)
    tags: QuestionTags

    @model_validator(mode="after")
    def check_type_consistency(self) -> "QuestionFile":
        if self.type is QuestionType.MC:
            if self.options is None or self.correct_index is None:
                raise ValueError(f"question {self.id!r}: mc requires options and correct_index")
            if not 0 <= self.correct_index < len(self.options):
                raise ValueError(f"question {self.id!r}: correct_index out of range")
        elif self.options is not None or self.correct_index is not None:
            raise ValueError(f"question {self.id!r}: flashcard must not have options/correct_index")
        return self


class QuestionSetFile(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,80}$")
    title: str = Field(min_length=3, max_length=200)
    track: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,80}$")
    level: int = Field(ge=1, le=5)
    description: str | None = None
    questions: list[QuestionFile] = Field(min_length=1)

    @model_validator(mode="after")
    def check_unique_question_ids(self) -> "QuestionSetFile":
        seen: set[str] = set()
        for question in self.questions:
            if question.id in seen:
                raise ValueError(f"duplicate question id {question.id!r} in set {self.id!r}")
            seen.add(question.id)
        return self


class QuestionOut(BaseModel):
    id: str
    set_id: str
    type: QuestionType
    topic: str
    prompt: str
    options: list[str] | None
    correct_index: int | None
    answer_notes: str
    difficulty_rationale: str
    tags: QuestionTags


class QuestionSetSummary(BaseModel):
    id: str
    title: str
    track: str
    level: int
    description: str | None
    question_count: int


class SessionStartRequest(BaseModel):
    # Optional because "review" mode spans every track (interleaved daily
    # review queue) rather than practicing one document at a time — see
    # services/scheduling.due_questions().
    track: str | None = None
    level: int | None = Field(default=None, ge=1, le=5)
    mode: str = Field(default="level", pattern=r"^(level|typical-drill|custom|review)$")
    typicality: list[TypicalityTag] | None = None
    limit: int = Field(default=20, ge=1, le=100)

    @model_validator(mode="after")
    def check_track_required_unless_review(self) -> "SessionStartRequest":
        if self.mode != "review" and not self.track:
            raise ValueError(f"mode {self.mode!r} requires a track")
        return self


class SessionOut(BaseModel):
    id: str
    track: str
    level: int | None
    mode: str
    questions: list[QuestionOut]


class DueQueueOut(BaseModel):
    count_due: int
    questions: list[QuestionOut]


class AnswerRequest(BaseModel):
    session_id: str
    question_id: str
    chosen_index: int | None = None
    self_rating: SelfRating | None = None

    @model_validator(mode="after")
    def check_exactly_one_answer_kind(self) -> "AnswerRequest":
        if (self.chosen_index is None) == (self.self_rating is None):
            raise ValueError("provide exactly one of chosen_index or self_rating")
        return self


class AnswerResult(BaseModel):
    question_id: str
    score: float
    correct: bool
    correct_index: int | None
    answer_notes: str


class LevelProgress(BaseModel):
    level: int
    difficulty: DifficultyTag
    total_questions: int
    attempted_questions: int
    accuracy: float | None
    unlocked: bool
    passed: bool


class TrackProgress(BaseModel):
    track: str
    levels: list[LevelProgress]
    highest_unlocked: int


class TopicStat(BaseModel):
    topic: str
    attempts: int
    accuracy: float


class ExportSummary(BaseModel):
    generated_at: datetime
    total_answers: int
    tracks: list[TrackProgress]
    weak_topics: list[TopicStat]
    strong_topics: list[TopicStat]


# ---------------------------------------------------------------------------
# Annotated reader — import contract (document.json)
# ---------------------------------------------------------------------------


class SpanFile(BaseModel):
    start: int = Field(ge=0)
    end: int = Field(gt=0)
    entity_id: str

    @model_validator(mode="after")
    def check_order(self) -> "SpanFile":
        if self.end <= self.start:
            raise ValueError("span end must be greater than start")
        return self


class PassageFile(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,80}$")
    heading: str | None = None
    text_es: str = Field(min_length=1)
    spans: list[SpanFile] = Field(default_factory=list)
    image_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_spans_in_range(self) -> "PassageFile":
        length = len(self.text_es)
        for span in self.spans:
            if span.end > length:
                raise ValueError(
                    f"passage {self.id!r}: span {span.start}-{span.end} out of range "
                    f"(text is {length} chars)"
                )
        return self


class RelationshipFile(BaseModel):
    target_entity_id: str
    target_document_id: str
    label: str = Field(min_length=1, max_length=200)


class ExternalReferenceFile(BaseModel):
    label: str = Field(min_length=1, max_length=300)
    url: str = Field(pattern=r"^https?://")


class EntityFile(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,80}$")
    name: str = Field(min_length=1, max_length=200)
    level: int = Field(default=1, ge=1)
    description_es: str = Field(min_length=1)
    description_spans: list[SpanFile] = Field(default_factory=list)
    relationships: list[RelationshipFile] = Field(default_factory=list)
    external_references: list[ExternalReferenceFile] = Field(default_factory=list)
    image_ids: list[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_description_spans_in_range(self) -> "EntityFile":
        length = len(self.description_es)
        for span in self.description_spans:
            if span.end > length:
                raise ValueError(
                    f"entity {self.id!r}: description span {span.start}-{span.end} out of range "
                    f"(text is {length} chars)"
                )
        return self


class ImageSource(StrEnum):
    DOCUMENT = "document"  # extracted from the source PDF, no confirmation needed
    EXTERNAL_PENDING = "external_pending"  # from the internet, awaiting user confirmation


class ImageFile(BaseModel):
    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,80}$")
    source: ImageSource
    caption: str | None = None
    # "document" images ship as a local file already placed under content/<slug>/images/
    local_filename: str | None = None
    # "external_pending" images carry only a URL — nothing is downloaded until confirmed
    url: str | None = None

    @model_validator(mode="after")
    def check_source_fields(self) -> "ImageFile":
        if self.source is ImageSource.DOCUMENT and not self.local_filename:
            raise ValueError(f"image {self.id!r}: source=document requires local_filename")
        if self.source is ImageSource.EXTERNAL_PENDING and not self.url:
            raise ValueError(f"image {self.id!r}: source=external_pending requires url")
        return self


class InconsistencyFile(BaseModel):
    """A contradiction found between two mentions of the same entity while
    authoring — cross-checking every mention against every other, not just
    proofreading each passage in isolation."""

    entity_id: str
    summary: str = Field(min_length=5)
    mention_a_location: str = Field(min_length=1, max_length=200)
    mention_a_quote: str = Field(min_length=1)
    mention_b_location: str = Field(min_length=1, max_length=200)
    mention_b_quote: str = Field(min_length=1)


class DocumentFile(BaseModel):
    """A ``document.json`` file — the annotated-reader import contract."""

    id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]{1,80}$")
    title: str = Field(min_length=3, max_length=200)
    source_path: str = Field(min_length=1)
    passages: list[PassageFile] = Field(min_length=1)
    entities: list[EntityFile] = Field(default_factory=list)
    images: list[ImageFile] = Field(default_factory=list)
    inconsistencies: list[InconsistencyFile] = Field(default_factory=list)

    @model_validator(mode="after")
    def check_references_resolve(self) -> "DocumentFile":
        entity_ids = {e.id for e in self.entities}
        image_ids = {i.id for i in self.images}
        for passage in self.passages:
            for span in passage.spans:
                if span.entity_id not in entity_ids:
                    raise ValueError(
                        f"passage {passage.id!r} references unknown entity {span.entity_id!r}"
                    )
            for image_id in passage.image_ids:
                if image_id not in image_ids:
                    raise ValueError(f"passage {passage.id!r} references unknown image {image_id!r}")
        for entity in self.entities:
            for span in entity.description_spans:
                if span.entity_id not in entity_ids:
                    raise ValueError(
                        f"entity {entity.id!r} references unknown entity {span.entity_id!r}"
                    )
            for image_id in entity.image_ids:
                if image_id not in image_ids:
                    raise ValueError(f"entity {entity.id!r} references unknown image {image_id!r}")
        for inconsistency in self.inconsistencies:
            if inconsistency.entity_id not in entity_ids:
                raise ValueError(
                    f"inconsistency references unknown entity {inconsistency.entity_id!r}"
                )
        return self


# ---------------------------------------------------------------------------
# Annotated reader — API DTOs
# ---------------------------------------------------------------------------


class ImageOut(BaseModel):
    id: str
    source: str
    caption: str | None
    # Always a usable <img src>: /api/images/{id}/file for document/confirmed
    # images (served from local disk), or the raw external URL — hotlinked,
    # not yet downloaded — while a pending image awaits confirmation.
    display_url: str
    pending: bool


class SpanOut(BaseModel):
    start: int
    end: int
    entity_id: str
    entity_name: str


class PassageOut(BaseModel):
    id: str
    heading: str | None
    text_es: str
    spans: list[SpanOut]
    images: list[ImageOut]


class RelationshipOut(BaseModel):
    target_entity_id: str
    target_entity_name: str
    target_document_id: str
    target_document_title: str
    label: str


class ExternalReferenceOut(BaseModel):
    label: str
    url: str


class EntityOut(BaseModel):
    id: str
    name: str
    level: int
    document_id: str
    document_title: str
    description: PassageOut
    relationships: list[RelationshipOut]
    external_references: list[ExternalReferenceOut]


class DocumentSummary(BaseModel):
    id: str
    title: str
    source_path: str
    passage_count: int
    entity_count: int
    mastery: float | None  # from the paired QuestionSet's track progress, if any
    open_inconsistencies: int


class InconsistencyOut(BaseModel):
    id: int
    entity_id: str
    entity_name: str
    summary: str
    mention_a_location: str
    mention_a_quote: str
    mention_b_location: str
    mention_b_quote: str
    status: str
    resolution_note: str | None


class ResolveInconsistencyRequest(BaseModel):
    resolution: str = Field(pattern=r"^(a|b|ai|dismiss)$")
    note: str | None = None

    @model_validator(mode="after")
    def check_ai_requires_note(self) -> "ResolveInconsistencyRequest":
        if self.resolution == "ai" and not self.note:
            raise ValueError("resolution 'ai' requires a note explaining the resolution")
        return self


class DocumentOut(BaseModel):
    id: str
    title: str
    source_path: str
    passages: list[PassageOut]


class AccessLogRequest(BaseModel):
    item_type: str = Field(pattern=r"^(document)$")
    item_id: str


class RecentItem(BaseModel):
    item_type: str
    item_id: str
    title: str
    viewed_at: datetime


class RecentPage(BaseModel):
    items: list[RecentItem]
    page: int
    page_size: int
    total: int


# ---------------------------------------------------------------------------
# Engagement layer (streak, XP, badges, progress breakdown) — see
# routers/engagement.py. Deliberately positive-framed only: a badge simply
# appears once its condition is true, there is no "you lost your streak"
# state to represent or punish.
# ---------------------------------------------------------------------------


class ProgressBuckets(BaseModel):
    new: int
    learning: int
    review: int
    mastered: int


class Badge(BaseModel):
    id: str
    label: str
    subject: str | None


class EngagementSummary(BaseModel):
    streak_days: int
    xp: int
    daily_goal: int
    reviewed_today: int
    buckets: ProgressBuckets
    badges: list[Badge]


class DailyGoalRequest(BaseModel):
    value: int = Field(ge=1, le=200)
