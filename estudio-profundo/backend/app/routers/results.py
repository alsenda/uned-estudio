"""Progress and export endpoints (vendored from quiz-app's app/routers/results.py, unchanged)."""

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db import get_session
from app.schemas import ExportSummary, TrackProgress
from app.services import stats

router = APIRouter(prefix="/api/results", tags=["results"])


@router.get("/tracks")
def list_tracks(session: Session = Depends(get_session)) -> list[str]:
    return stats.all_tracks(session)


@router.get("/progress")
def progress(track: str, session: Session = Depends(get_session)) -> TrackProgress:
    return stats.track_progress(session, track)


@router.get("/export")
def export(session: Session = Depends(get_session)) -> ExportSummary:
    return stats.export_summary(session)
