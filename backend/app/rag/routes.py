from fastapi import APIRouter

from . import query as rag_query
from .ingest import ingest
from .store import get_collection

router = APIRouter(prefix="/api/rag", tags=["rag"])


@router.get("/query")
def query(q: str, k: int = 5, subject: str | None = None, topic: str | None = None):
    return rag_query.answer(q, k=k, subject=subject or None, topic=topic or None)


@router.post("/ingest")
def run_ingest():
    return ingest(verbose=False)


@router.get("/status")
def status():
    collection = get_collection()
    return {"indexed_chunks": collection.count()}
