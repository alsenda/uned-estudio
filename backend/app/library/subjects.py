"""Lista de asignaturas del grado, leída de docs/asignaturas/README.md (el índice que ya se
mantiene a mano por curso y semestre), con el número de documentos de cada una.

No hay base de datos: el README es la fuente. Formato que se espera de cada línea:

    - [Nombre](71031027-slug/README.md) (6 ECTS, Formación básica) *(nota opcional)*
"""

import re
from pathlib import Path

from ..config import DOCS_DIR

SUBJECTS_DIR = DOCS_DIR / "asignaturas"
CURRENT = (1, 1)  # (curso, semestre) que se está estudiando ahora: sus asignaturas van primero

_COURSE = re.compile(r"^##\s+Curso\s+(\d+)")
_SEMESTER = re.compile(r"^###\s+Semestre\s+(\d+)")
_ITEM = re.compile(
    r"^-\s+(?P<anual>\*\*Anual\*\*\s+—\s+)?\[(?P<name>[^\]]+)\]\((?P<folder>[^/]+)/README\.md\)"
    r"\s+\((?P<ects>[\d.]+)\s+ECTS,\s+(?P<tipo>[^)]+)\)(?:\s+\*\((?P<note>[^)]+)\)\*)?"
)
_DOC_EXTENSIONS = {".md", ".txt", ".pdf"}


def _count_documents(folder: str) -> int:
    base = SUBJECTS_DIR / folder
    if not base.is_dir():
        return 0
    return sum(1 for p in base.rglob("*") if p.is_file() and p.suffix.lower() in _DOC_EXTENSIONS and p.name != "README.md")


def list_subjects() -> list[dict]:
    index = SUBJECTS_DIR / "README.md"
    if not index.exists():
        return []
    course, semester = None, None
    subjects = []
    for line in index.read_text(encoding="utf-8", errors="ignore").splitlines():
        if m := _COURSE.match(line):
            course, semester = int(m.group(1)), None
        elif m := _SEMESTER.match(line):
            semester = int(m.group(1))
        elif (m := _ITEM.match(line)) and course is not None:
            folder = m.group("folder")
            sem = "anual" if m.group("anual") else semester
            subjects.append(
                {
                    "folder": folder,
                    "code": folder.split("-")[0] or folder,
                    "name": m.group("name"),
                    "course": course,
                    "semester": sem,
                    "ects": float(m.group("ects")),
                    "type": m.group("tipo"),
                    "note": m.group("note"),
                    "document_count": _count_documents(folder),
                    "current": (course, sem) == CURRENT,
                }
            )
    return subjects
