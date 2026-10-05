"""Access log: records document views so the home page can show "recently
accessed", and exposes them paginated."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import AccessLog, Document
from app.schemas import AccessLogRequest, RecentItem, RecentPage

router = APIRouter(prefix="/api/access", tags=["access"])


@router.post("")
def log_access(request: AccessLogRequest, session: Session = Depends(get_session)) -> dict[str, str]:
    session.add(AccessLog(item_type=request.item_type, item_id=request.item_id))
    session.commit()
    return {"status": "logged"}


@router.get("/recent")
def recent(
    page: int = 1, page_size: int = 10, session: Session = Depends(get_session)
) -> RecentPage:
    # Most recent view per item_id (a document opened 5 times shows up once,
    # at its latest viewed_at) — same "derive from raw log, don't dedupe on
    # write" spirit as the quiz engine's progress stats.
    latest_per_item = (
        select(AccessLog.item_type, AccessLog.item_id, func.max(AccessLog.viewed_at).label("viewed_at"))
        .group_by(AccessLog.item_type, AccessLog.item_id)
        .subquery()
    )
    total = session.execute(select(func.count()).select_from(latest_per_item)).scalar_one()
    rows = session.execute(
        select(latest_per_item)
        .order_by(latest_per_item.c.viewed_at.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    ).all()

    items: list[RecentItem] = []
    for item_type, item_id, viewed_at in rows:
        title = item_id
        if item_type == "document":
            document = session.get(Document, item_id)
            if document is not None:
                title = document.title
        items.append(RecentItem(item_type=item_type, item_id=item_id, title=title, viewed_at=viewed_at))

    return RecentPage(items=items, page=page, page_size=page_size, total=total)
