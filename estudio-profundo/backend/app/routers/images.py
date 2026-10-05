"""Image confirm/discard workflow and file serving.

Images with ``source=external_pending`` are never written to disk until the
user explicitly confirms them (the frontend just hotlinks ``Image.url`` for
preview inside the confirmation banner). Confirming downloads the bytes once
and flips the row to ``external_confirmed``; discarding deletes the row and
touches no file at all — nothing was ever fetched.
"""

import mimetypes
from pathlib import Path
from urllib.parse import urlparse

import requests
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse

from app.config import get_settings
from app.db import get_session
from app.models import Image
from sqlalchemy.orm import Session

router = APIRouter(prefix="/api/images", tags=["images"])

MAX_DOWNLOAD_BYTES = 15 * 1024 * 1024  # 15 MB — generous for an illustrative diagram/photo


def _resolve_local_path(local_path: str) -> Path:
    settings = get_settings()
    target = (settings.content_path / local_path).resolve()
    content_root = settings.content_path.resolve()
    if target != content_root and content_root not in target.parents:
        raise HTTPException(status_code=403, detail="ruta fuera de content/")
    return target


@router.post("/{image_id}/confirm")
def confirm_image(image_id: str, session: Session = Depends(get_session)) -> dict[str, str]:
    image = session.get(Image, image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Unknown image.")
    if image.source != "external_pending":
        raise HTTPException(status_code=409, detail="Image is not pending confirmation.")
    if not image.url:
        raise HTTPException(status_code=422, detail="Pending image has no source url.")

    # Many sites (Wikimedia included) reject requests with no identifying
    # User-Agent as bot abuse — a descriptive one is required, not optional.
    headers = {"User-Agent": "estudio-profundo/0.1 (local personal study tool; contact: n/a)"}
    response = requests.get(image.url, timeout=15, stream=True, headers=headers)
    response.raise_for_status()
    content = response.raw.read(MAX_DOWNLOAD_BYTES + 1)
    if len(content) > MAX_DOWNLOAD_BYTES:
        raise HTTPException(status_code=413, detail="Image exceeds the 15 MB limit.")

    ext = Path(urlparse(image.url).path).suffix or mimetypes.guess_extension(
        response.headers.get("content-type", "")
    ) or ".bin"
    filename = f"{image.id.split('::')[-1]}{ext}"
    settings = get_settings()
    images_dir = settings.images_dir_for(image.document_id)
    (images_dir / filename).write_bytes(content)

    image.local_path = f"{image.document_id}/images/{filename}"
    image.source = "external_confirmed"
    session.commit()
    return {"status": "confirmed", "local_path": image.local_path}


@router.post("/{image_id}/discard")
def discard_image(image_id: str, session: Session = Depends(get_session)) -> dict[str, str]:
    image = session.get(Image, image_id)
    if image is None:
        raise HTTPException(status_code=404, detail="Unknown image.")
    if image.source != "external_pending":
        raise HTTPException(status_code=409, detail="Only pending images can be discarded.")
    session.delete(image)
    session.commit()
    return {"status": "discarded"}


@router.get("/{image_id}/file")
def get_image_file(image_id: str, session: Session = Depends(get_session)) -> FileResponse:
    image = session.get(Image, image_id)
    if image is None or not image.local_path:
        raise HTTPException(status_code=404, detail="Image not available.")
    path = _resolve_local_path(image.local_path)
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Image file missing on disk.")
    media_type = mimetypes.guess_type(path.name)[0] or "application/octet-stream"
    return FileResponse(path, media_type=media_type)
