import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]

DOCS_DIR = PROJECT_ROOT / "docs"
FEED_ENTRIES_DIR = PROJECT_ROOT / "feed" / "entries"
AGENDA_EVENTS_DIR = PROJECT_ROOT / "agenda" / "events"
AGENDA_TODOS_DIR = PROJECT_ROOT / "agenda" / "todos"
GLOSSARY_TERMS_DIR = PROJECT_ROOT / "glossary" / "terms"
CONTACTS_PEOPLE_DIR = PROJECT_ROOT / "contacts" / "people"
CONTACTS_INTERACTIONS_DIR = PROJECT_ROOT / "contacts" / "interactions"
FRONTEND_DIR = PROJECT_ROOT / "frontend"
DATA_DIR = PROJECT_ROOT / "backend" / "data"
CHROMA_DIR = DATA_DIR / "chroma"
INGEST_MANIFEST_PATH = DATA_DIR / "ingest_manifest.json"
NEWS_SEEN_PATH = DATA_DIR / "news_seen.json"
SOURCES_PATH = Path(__file__).resolve().parent / "feed" / "sources.yaml"

OLLAMA_HOST = os.environ.get("OLLAMA_HOST", "http://localhost:11434")
EMBED_MODEL = os.environ.get("UNED_EMBED_MODEL", "nomic-embed-text")
LLM_MODEL = os.environ.get("UNED_LLM_MODEL", "qwen2.5:7b-instruct")

RAG_COLLECTION = "uned_docs"
RAG_CHUNK_SIZE = 1200
RAG_CHUNK_OVERLAP = 150

DATA_DIR.mkdir(parents=True, exist_ok=True)
