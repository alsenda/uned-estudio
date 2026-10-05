import hashlib
import json
import sys
import time

from pypdf import PdfReader

from ..config import DOCS_DIR, INGEST_MANIFEST_PATH, RAG_CHUNK_OVERLAP, RAG_CHUNK_SIZE
from .store import get_collection

SUPPORTED_EXTENSIONS = {".md", ".txt", ".pdf"}
EMBED_BATCH_SIZE = 32
MAX_RETRIES = 3


def read_text(path) -> str:
    if path.suffix.lower() == ".pdf":
        reader = PdfReader(str(path))
        return "\n\n".join(page.extract_text() or "" for page in reader.pages)
    return path.read_text(encoding="utf-8", errors="ignore")


def chunk_text(text: str, size: int = RAG_CHUNK_SIZE, overlap: int = RAG_CHUNK_OVERLAP) -> list[str]:
    text = text.strip()
    if not text:
        return []
    chunks = []
    start = 0
    while start < len(text):
        end = start + size
        chunks.append(text[start:end])
        if end >= len(text):
            break
        start = end - overlap
    return chunks


def file_hash(path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load_manifest() -> dict:
    if INGEST_MANIFEST_PATH.exists():
        return json.loads(INGEST_MANIFEST_PATH.read_text(encoding="utf-8"))
    return {}


def save_manifest(manifest: dict) -> None:
    INGEST_MANIFEST_PATH.parent.mkdir(parents=True, exist_ok=True)
    INGEST_MANIFEST_PATH.write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding="utf-8")


def _upsert_with_retry(collection, ids, documents, metadatas, verbose: bool) -> None:
    for attempt in range(1, MAX_RETRIES + 1):
        try:
            collection.upsert(ids=ids, documents=documents, metadatas=metadatas)
            return
        except Exception as exc:
            if attempt == MAX_RETRIES:
                raise
            if verbose:
                print(f"[ingest]   reintento {attempt}/{MAX_RETRIES} tras error: {exc}")
            time.sleep(2 * attempt)


def _embed_and_store(collection, rel_path: str, chunks: list[str], subject: str, verbose: bool) -> list[str]:
    chunk_ids = [f"{rel_path}::{i}" for i in range(len(chunks))]
    for start in range(0, len(chunks), EMBED_BATCH_SIZE):
        end = start + EMBED_BATCH_SIZE
        batch_ids = chunk_ids[start:end]
        batch_docs = chunks[start:end]
        batch_meta = [{"source": rel_path, "chunk": start + i, "subject": subject} for i in range(len(batch_docs))]
        _upsert_with_retry(collection, batch_ids, batch_docs, batch_meta, verbose)
    return chunk_ids


def ingest(verbose: bool = True) -> dict:
    collection = get_collection()
    manifest = load_manifest()

    seen_files = set()
    added_files = 0
    skipped_files = 0
    removed_files = 0
    failed_files = []

    for path in DOCS_DIR.rglob("*"):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_EXTENSIONS:
            continue

        rel_path = path.relative_to(DOCS_DIR).as_posix()
        seen_files.add(rel_path)
        current_hash = file_hash(path)
        record = manifest.get(rel_path)

        if record and record["hash"] == current_hash:
            skipped_files += 1
            continue

        text = read_text(path)
        chunks = chunk_text(text)
        if not chunks:
            if record:
                collection.delete(ids=record["chunk_ids"])
                del manifest[rel_path]
                save_manifest(manifest)
            continue

        subject = path.relative_to(DOCS_DIR).parts[1] if len(path.relative_to(DOCS_DIR).parts) > 2 else ""

        try:
            chunk_ids = _embed_and_store(collection, rel_path, chunks, subject, verbose)
        except Exception as exc:
            failed_files.append(rel_path)
            if verbose:
                print(f"[ingest] FALLO en {rel_path}, se omite (reintentar en la proxima ejecucion): {exc}")
            continue

        if record:
            collection.delete(ids=record["chunk_ids"])

        manifest[rel_path] = {"hash": current_hash, "chunk_ids": chunk_ids}
        save_manifest(manifest)
        added_files += 1
        if verbose:
            print(f"[ingest] {rel_path} -> {len(chunks)} chunks")

    for rel_path in list(manifest.keys()):
        if rel_path not in seen_files:
            collection.delete(ids=manifest[rel_path]["chunk_ids"])
            del manifest[rel_path]
            removed_files += 1
            if verbose:
                print(f"[ingest] eliminado: {rel_path}")

    save_manifest(manifest)
    result = {
        "added_or_updated": added_files,
        "skipped": skipped_files,
        "removed": removed_files,
        "failed": failed_files,
    }
    if verbose:
        print(f"[ingest] listo: {result}")
    return result


if __name__ == "__main__":
    ingest(verbose=True)
    sys.exit(0)
