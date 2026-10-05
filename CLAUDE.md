# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

UNED study project, shared with other students: subject documentation (`docs/`), a combined
learning-log + news feed (`feed/`), a local RAG system over the documentation, and the study
engine (`estudio-profundo/`, annotated documents + quizzes + spaced repetition), served by two
small FastAPI backends + static frontend. Everything runs locally against Ollama — no cloud
services, no deployment. The README is written for non-programmers (double-click `Iniciar.bat`);
keep it that way. See `README.md` for the user-facing overview, `docs/README.md`
for the documentation convention, and `feed/README.md` for the feed entry format.

## Commands

Run from the repo root.

```powershell
Iniciar.bat  (or: python iniciar.py)                            # one-click: venv, deps, Ollama + models, ingest, seed, both servers, open browser
./scripts/run.ps1                                              # create venv, install deps, start server on :8000
./.venv/Scripts/python.exe -m backend.app.rag.ingest            # (re)index docs/ into ChromaDB, incremental
./.venv/Scripts/python.exe -m backend.app.rag.query "pregunta"  # query the RAG index from the CLI, no server needed
./scripts/iniciar-estudio.ps1                                   # start app (:8000) + study engine (:8011), hidden, and open the web
```

Optional Windows scheduled task (`scripts/registrar-avisos-agenda.ps1`): `UNED-AvisosAgenda` (toast notifications from `agenda/`, every 5 min).

There is no build step, linter, or test suite configured — the frontend is plain HTML/CSS/JS
served as static files (`frontend/`, mounted at `/` by `backend/app/main.py`). It's split
into native ES modules under `frontend/src/` (no bundler — browsers load them directly via
`<script type="module">`), one file per concern: `dom.js` (element helper), `api.js` (fetch
wrappers for both this backend and estudio-profundo's), `markdown.js`, `feed.js`, `rag.js`,
`library.js`, `annotated.js` + `cards.js` + `study.js` (the "Estudiar" section), `home.js`
(stats/diary/recents, shown under the dashboard), `dashboard.js` + `plan-semestre.js` (the
Inicio semester dashboard — styles in `frontend/dashboard.css`; `plan-semestre.js` holds the
hand-edited semester data: subjects, colors, weekly topics marked official vs. orientativo;
`syllabus.js` holds each subject's temario with dates and the id of its annotated study
document, if any), `subjects.js` (the "Estudiar" landing: subjects on the left, current
semester first; per subject the temario, its questions and a box that asks the RAG — styles
in `frontend/study.css`), and `main.js` (rail nav + wiring). Cross-module navigation (e.g. a RAG source or a Markdown
link opening a doc in Documentos) goes through a `doc-link` class + a `activate-section`
CustomEvent rather than direct imports, to avoid a tangle of circular imports.

The study engine lives in `estudio-profundo/` (vendored from the former standalone repo; its
Vite frontend was dropped — this app's frontend is the only UI). It's a separate FastAPI process
on `:8011` (`cd estudio-profundo/backend && python -m uvicorn app.main:app --port 8011`), started
by `iniciar.py` together with the main app, sharing the root `.venv` (deps merged into
`backend/requirements.txt`). `iniciar.py` also runs `estudio-profundo/backend/scripts/seed.py`
every launch to load `estudio-profundo/content/<slug>/{document,quiz}.json` into its SQLite DB
(`estudio.db`, gitignored: per-person progress). This app's frontend calls it cross-origin;
no shared database.

Requires Ollama running locally with `nomic-embed-text` (embeddings) and
`qwen2.5:7b-instruct` (generation, default) pulled. Override models via `UNED_EMBED_MODEL` /
`UNED_LLM_MODEL` env vars, and the Ollama host via `OLLAMA_HOST`.

## Architecture

**Two independent capabilities sharing one FastAPI app** (`backend/app/main.py` just mounts
both routers plus the static frontend):

- `backend/app/feed/` — `store.py` reads/writes feed entries as individual Markdown files
  with YAML front matter in `feed/entries/` (via `python-frontmatter`); there is no
  database. `news.py` fetches RSS sources listed in `backend/app/feed/sources.yaml` and
  writes them into the same `feed/entries/` directory as `type: noticia` entries
  (deduplicated by link in `backend/data/news_seen.json`). Diary entries (`type: diario`)
  are added the same way, either by hand or via `POST /api/feed/entries`.

- `backend/app/rag/` — `ingest.py` walks `docs/` recursively (`.md`, `.txt`, `.pdf`),
  chunks each file (`chunk_text`, ~1200 chars / 150 overlap), embeds chunks via Ollama, and
  upserts them into a persistent ChromaDB collection at `backend/data/chroma/`. It is
  **incremental**: `backend/data/ingest_manifest.json` maps each source file to its content
  hash and the chunk IDs it produced, so unchanged files are skipped and stale chunks are
  removed when a file changes or disappears. `query.py` embeds the question, retrieves the
  top-k chunks from Chroma, and asks the local LLM to answer using only that context,
  citing sources — used by both `GET /api/rag/query` and the CLI entrypoint.
  `store.py` centralizes the Chroma client: it must use ChromaDB's own
  `chromadb.utils.embedding_functions.ollama_embedding_function.OllamaEmbeddingFunction`
  (not a hand-rolled one) — ChromaDB >=1.5 requires embedding functions to implement
  `.name()`/`build_from_config()`/`get_config()`, which the built-in class already does.

**Document organization convention** (`docs/asignaturas/<codigo>-<slug>/{apuntes,resumenes,ejercicios,examenes}/`,
templated in `docs/asignaturas/_plantilla/`) is load-bearing for RAG metadata: `ingest.py`
derives each chunk's `subject` from the second path component under `docs/`
(`path.relative_to(DOCS_DIR).parts[1]`), so new subjects must follow this folder depth or
retrieval filtering by subject silently degrades.

**Data vs. code, for git purposes**: `docs/` and `feed/entries/` are shared content and are
always committed (including PDFs). Personal per-student data is gitignored on purpose so the repo
can be shared: `agenda/todos/*`, `contacts/interactions/*` (folders kept via `.gitkeep`),
`estudio-profundo/backend/estudio.db*`, `gastos*.xlsx`. `backend/data/` (Chroma index,
manifests, and now `access_log.jsonl` for "recently accessed") is gitignored on purpose —
the Chroma index and manifests are fully regenerable from `docs/` via `rag.ingest`, and the
access log is pure browsing history, neither worth versioning as binary/derived data.

- `backend/app/library/` — `routes.py` serves the `docs/` tree (`GET /api/library/tree`),
  individual files (`/file` raw, `/text` for `.md`/`.txt`), and a lightweight "recently
  viewed" log: `access.py` appends one JSON line per view to
  `backend/data/access_log.jsonl` (not a database — a personal library never gets big enough
  to need one) and `GET /api/library/recent` dedupes by path, keeping the latest view, sorted
  newest-first. The frontend's Inicio section merges this with estudio-profundo's own
  `GET :8011/api/access/recent` client-side into one paginated list. `subjects.py` parses
  `docs/asignaturas/README.md` (course/semester index) into `GET /api/library/subjects`, with
  a `current` flag for the semester being studied (`CURRENT` constant).

**RAG query**: `GET /api/rag/query?q=&subject=&topic=` — `subject` (a folder under
`docs/asignaturas/`) restricts retrieval to that subject's chunks; retrieval is hybrid (dense +
exact-phrase hints from the question, `query.py::_lexical_hits`) because dense search alone missed
chunks that define one specific term. The system prompt forces Spanish (qwen drifts to Chinese; there
is a retry) and forbids LaTeX. Study content authored for the engine lives in `estudio-profundo/content/<slug>/`. Kindle books can't be embedded (Amazon sends
`X-Frame-Options: SAMEORIGIN`) nor copied (DRM): a `.md` card with `lector: <https url>` in its front
matter gets an "open in reader window" button in Documentos.

- `backend/app/agenda/` — same file-per-record pattern as `feed/`, not a database:
  `store.py` reads/writes calendar events (`agenda/events/*.md`) and tasks
  (`agenda/todos/*.md`) as individual Markdown files with YAML front matter. Events and
  todos-with-a-`due_date` both show up on the "Calendario" section's month grid
  (`frontend/src/calendar.js`); todos without a date only appear in its flat task list.
  Real user data like `docs/`/`feed/entries/`, so `agenda/` is committed to git, not put
  under the gitignored `backend/data/` — see `agenda/README.md` for the file format.

- `backend/app/glossary/` — same pattern again: `store.py` reads/writes glossary entries
  (`glossary/terms/*.md`) as individual Markdown files with YAML front matter (`term`,
  optional `subject`/`tags`), filterable by subject/tag/free text. Served by the
  "Glosario" section (`frontend/src/glossary.js`). See `glossary/README.md`.

- `backend/app/contacts/` — same pattern again: `store.py` reads/writes people
  (`contacts/people/*.md`) and their interaction history (`contacts/interactions/*.md`,
  linked by `person_id`) as individual Markdown files. Deleting a person cascades to their
  interactions. Served by the "Contactos" section (`frontend/src/contacts.js`), which
  shares the generic backdrop/panel modal (`frontend/src/modal.js`) with
  `frontend/src/calendar.js`'s day-detail and add-item forms. See `contacts/README.md`.
