"""Listing and resolving intra-document inconsistencies.

Resolution is one of four things the user (or, for ``ai``, a future authoring
pass by Claude) can do with a flagged contradiction: pick side A, pick side
B, have the AI resolve it (requires a note explaining the reasoning — this is
what a future ``python scripts/seed.py`` re-authoring pass fills in after
fixing the source content), or dismiss it as not a real contradiction.
"""

from datetime import UTC, datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Entity, Inconsistency
from app.schemas import InconsistencyOut, ResolveInconsistencyRequest

router = APIRouter(tags=["inconsistencies"])

_RESOLUTION_TO_STATUS = {
    "a": "resolved_a",
    "b": "resolved_b",
    "ai": "resolved_ai",
    "dismiss": "dismissed",
}


def _out(session: Session, row: Inconsistency) -> InconsistencyOut:
    entity = session.get(Entity, row.entity_id)
    return InconsistencyOut(
        id=row.id,
        entity_id=row.entity_id,
        entity_name=entity.name if entity else row.entity_id,
        summary=row.summary,
        mention_a_location=row.mention_a_location,
        mention_a_quote=row.mention_a_quote,
        mention_b_location=row.mention_b_location,
        mention_b_quote=row.mention_b_quote,
        status=row.status,
        resolution_note=row.resolution_note,
    )


@router.get("/api/documents/{document_id}/inconsistencies")
def list_inconsistencies(
    document_id: str, status: str | None = None, session: Session = Depends(get_session)
) -> list[InconsistencyOut]:
    query = select(Inconsistency).where(Inconsistency.document_id == document_id)
    if status:
        query = query.where(Inconsistency.status == status)
    rows = session.execute(query.order_by(Inconsistency.created_at)).scalars().all()
    return [_out(session, row) for row in rows]


@router.post("/api/inconsistencies/{inconsistency_id}/resolve")
def resolve_inconsistency(
    inconsistency_id: int, request: ResolveInconsistencyRequest, session: Session = Depends(get_session)
) -> InconsistencyOut:
    row = session.get(Inconsistency, inconsistency_id)
    if row is None:
        raise HTTPException(status_code=404, detail="Unknown inconsistency.")
    row.status = _RESOLUTION_TO_STATUS[request.resolution]
    row.resolution_note = request.note
    row.resolved_at = datetime.now(UTC)
    session.commit()
    return _out(session, row)
