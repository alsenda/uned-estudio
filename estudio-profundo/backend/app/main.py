"""FastAPI application factory.

Runs as a standalone service on its own port (default 8011, see
``scripts/run.ps1``), independent of whatever project's documentation it is
pointed at via ``content_dir`` — CORS is opened to the consuming frontend
(UNED's, by default) rather than mounting into its process.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import get_settings
from app.db import init_db
from app.routers import (
    access,
    documents,
    engagement,
    entities,
    images,
    inconsistencies,
    quiz,
    results,
    review,
    sets,
)

FRONTEND_DIST = Path(__file__).resolve().parent.parent.parent / "frontend" / "dist"


@asynccontextmanager
async def lifespan(_app: FastAPI) -> AsyncIterator[None]:
    init_db()
    yield


def create_app() -> FastAPI:
    app = FastAPI(title="Estudio a fondo", lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=get_settings().cors_origins,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/api/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    app.include_router(documents.router)
    app.include_router(entities.router)
    app.include_router(images.router)
    app.include_router(inconsistencies.router)
    app.include_router(access.router)
    app.include_router(sets.router)
    app.include_router(quiz.router)
    app.include_router(results.router)
    app.include_router(review.router)
    app.include_router(engagement.router)

    if FRONTEND_DIST.is_dir():
        app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
    return app


app = create_app()
