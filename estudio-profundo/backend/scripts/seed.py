"""Validate and load content/<slug>/{document,quiz}.json into the database.

Usage (from the backend/ directory):

    python scripts/seed.py                 # validate + load every content/<slug>/
    python scripts/seed.py --validate       # validate only, touch nothing
    python scripts/seed.py mitre-attack     # validate + load one slug

Exit code is non-zero if any file fails validation.
"""

import argparse
import json
import sys
from pathlib import Path

from pydantic import ValidationError

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from app.config import get_settings  # noqa: E402
from app.schemas import DocumentFile, QuestionSetFile  # noqa: E402


def _load(path: Path, model: type) -> object | None:
    if not path.exists():
        return None
    try:
        return model.model_validate(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as error:
        print(f"FAIL  {path}: invalid JSON — {error}")
        return "error"
    except ValidationError as error:
        print(f"FAIL  {path}:\n{error}")
        return "error"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("slugs", nargs="*", help="specific content slugs (default: all)")
    parser.add_argument("--validate", action="store_true", help="validate only, do not load")
    args = parser.parse_args()

    content_dir = get_settings().content_path
    slugs = args.slugs or sorted(p.name for p in content_dir.iterdir() if p.is_dir())
    if not slugs:
        print(f"No content found in {content_dir}")
        return 1

    documents: list[DocumentFile] = []
    quizzes: list[QuestionSetFile] = []
    failed = False

    for slug in slugs:
        folder = content_dir / slug
        doc = _load(folder / "document.json", DocumentFile)
        if doc == "error":
            failed = True
        elif doc is not None:
            documents.append(doc)
            print(f"ok    {slug}/document.json: {doc.title} — {len(doc.passages)} passages, {len(doc.entities)} entities")

        quiz = _load(folder / "quiz.json", QuestionSetFile)
        if quiz == "error":
            failed = True
        elif quiz is not None:
            quizzes.append(quiz)
            print(f"ok    {slug}/quiz.json: {len(quiz.questions)} questions")

        if doc is None and quiz is None:
            print(f"skip  {slug}: no document.json or quiz.json found")

    docs_by_id = {d.id: d for d in documents}
    for quiz in quizzes:
        for question in quiz.questions:
            ref = question.source
            if ref is None:
                continue
            doc = docs_by_id.get(ref.document_id or quiz.id)
            if doc is None:
                print(f"FAIL  {quiz.id}/{question.id}: source points to unknown document {ref.document_id or quiz.id!r}")
                failed = True
                continue
            if ref.passage_id not in {p.id for p in doc.passages}:
                print(f"FAIL  {quiz.id}/{question.id}: unknown passage {ref.passage_id!r}")
                failed = True
            if ref.entity_id is not None and ref.entity_id not in {e.id for e in doc.entities}:
                print(f"FAIL  {quiz.id}/{question.id}: unknown entity {ref.entity_id!r}")
                failed = True

    if failed:
        return 1
    if args.validate:
        print(f"All content valid ({len(documents)} document(s), {len(quizzes)} quiz set(s)).")
        return 0

    from app.db import get_session_factory, init_db
    from app.services.content_import import upsert_document
    from app.services.question_sets import upsert_question_set

    init_db()
    with get_session_factory()() as session:
        for doc in documents:
            upsert_document(session, doc)
        for quiz in quizzes:
            upsert_question_set(session, quiz)
    print(f"Loaded {len(documents)} document(s) and {len(quizzes)} quiz set(s).")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
