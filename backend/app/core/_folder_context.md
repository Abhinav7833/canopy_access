---
module: core
owns: [config, utils]
last_reviewed: dcb5d47357b3
---
# core
Cross-cutting infrastructure for the app: settings, database session/engine, local asset storage, and the API error envelope.

## Structure
- `config.py` — `Settings` (pydantic-settings, reads `.env`): DB URLs, assets dir, static mount, LLM base URL/key/model; cached via `get_settings()`.
- `db.py` — SQLAlchemy `Base`, `engine`, `SessionLocal`, and the `get_db()` FastAPI dependency (commits on success, rolls back on error).
- `storage.py` — `Storage` protocol and `LocalStorage` implementation for saving/serving evidence assets under the static mount; `get_storage()` factory.
- `errors.py` — `NotFound` exception, JSON error envelope, and `install_error_handlers()` (404 / 422 / 500 handlers) used by `main.py`.

## Public interface
`get_settings()`, `Settings`, `Base`, `engine`, `SessionLocal`, `get_db()`, `Storage`, `get_storage()`, `NotFound`, `install_error_handlers()` — imported throughout `models/`, `services/`, `agent/`, and `api/`.

## Depends on
`pydantic-settings`, SQLAlchemy, FastAPI. No dependency on other `app` subpackages (this is the base layer everything else builds on).
