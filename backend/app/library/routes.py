import mimetypes
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel

from ..config import DOCS_DIR
from . import access, subjects

router = APIRouter(prefix="/api/library", tags=["library"])


class AccessRequest(BaseModel):
    path: str
    title: str

TEXT_EXTENSIONS = {".md", ".txt"}
VIEWABLE_EXTENSIONS = TEXT_EXTENSIONS | {".pdf"}


def _build_tree(path: Path) -> dict:
    rel = path.relative_to(DOCS_DIR)
    if path.is_dir():
        children = sorted(
            path.iterdir(), key=lambda p: (p.is_file(), p.name.lower())
        )
        return {
            "name": path.name if rel != Path(".") else "docs",
            "path": "" if rel == Path(".") else rel.as_posix(),
            "type": "dir",
            "children": [
                _build_tree(child)
                for child in children
                if not child.name.startswith(".")
            ],
        }
    return {
        "name": path.name,
        "path": rel.as_posix(),
        "type": "file",
        "ext": path.suffix.lower(),
        "viewable": path.suffix.lower() in VIEWABLE_EXTENSIONS,
        "size": path.stat().st_size,
    }


def _resolve_safe_path(rel_path: str) -> Path:
    if not rel_path or Path(rel_path).is_absolute():
        raise HTTPException(status_code=400, detail="ruta invalida")
    docs_root = DOCS_DIR.resolve()
    target = (docs_root / rel_path).resolve()
    if target != docs_root and docs_root not in target.parents:
        raise HTTPException(status_code=403, detail="fuera de docs/")
    if not target.is_file():
        raise HTTPException(status_code=404, detail="no encontrado")
    return target


@router.get("/tree")
def get_tree():
    return _build_tree(DOCS_DIR)


@router.get("/subjects")
def get_subjects():
    return subjects.list_subjects()


@router.get("/file")
def get_file(path: str):
    target = _resolve_safe_path(path)
    media_type = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
    return FileResponse(target, media_type=media_type)


@router.get("/text")
def get_text(path: str):
    target = _resolve_safe_path(path)
    if target.suffix.lower() not in TEXT_EXTENSIONS:
        raise HTTPException(status_code=415, detail="no es un fichero de texto")
    return {"content": target.read_text(encoding="utf-8", errors="ignore")}


@router.post("/access")
def log_access(request: AccessRequest):
    _resolve_safe_path(request.path)  # valida que el path es real y esta dentro de docs/
    access.log_access(request.path, request.title)
    return {"status": "logged"}


@router.get("/recent")
def get_recent(page: int = 1, page_size: int = 10):
    return access.recent(page=page, page_size=page_size)
