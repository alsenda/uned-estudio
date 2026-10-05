"""Access log for docs/ items: an append-only JSONL file (not a database —
this project has no SQL store, and a personal library never gets big enough
to need one). Read side dedupes by path, keeping the latest view."""

import json
from datetime import UTC, datetime
from pathlib import Path

from ..config import DATA_DIR

ACCESS_LOG_PATH = DATA_DIR / "access_log.jsonl"


def log_access(path: str, title: str) -> None:
    ACCESS_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
    entry = {"path": path, "title": title, "viewed_at": datetime.now(UTC).isoformat()}
    with open(ACCESS_LOG_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def recent(page: int = 1, page_size: int = 10) -> dict:
    if not ACCESS_LOG_PATH.exists():
        return {"items": [], "page": page, "page_size": page_size, "total": 0}

    latest_by_path: dict[str, dict] = {}
    with open(ACCESS_LOG_PATH, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            entry = json.loads(line)
            latest_by_path[entry["path"]] = entry

    items = sorted(latest_by_path.values(), key=lambda e: e["viewed_at"], reverse=True)
    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]
    return {"items": page_items, "page": page, "page_size": page_size, "total": total}
