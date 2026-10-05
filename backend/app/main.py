from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .config import FRONTEND_DIR
from .agenda.routes import router as agenda_router
from .contacts.routes import router as contacts_router
from .feed.routes import router as feed_router
from .glossary.routes import router as glossary_router
from .library.routes import router as library_router
from .rag.routes import router as rag_router

app = FastAPI(title="UNED")

app.include_router(feed_router)
app.include_router(rag_router)
app.include_router(library_router)
app.include_router(agenda_router)
app.include_router(glossary_router)
app.include_router(contacts_router)

app.mount("/", StaticFiles(directory=str(FRONTEND_DIR), html=True), name="frontend")
