---
module: app
owns: [modules]
boundary: backend/app/main.py
last_reviewed: 43772b824dad
---
# app
The Canopy FastAPI application package: builds the app, mounts static assets, wires error handlers, and includes the HTTP routers. Everything else in the backend lives in its subpackages.

## Structure
- `main.py` — `create_app()` builds the FastAPI app (health check, static mount, error handlers, routers) and exposes the module-level `app` instance.
- `api/` — HTTP layer: route modules under `api/routes/` (projects, evidence, agent).
- `core/` — infra: settings, DB session/engine, local file storage, error envelope/handlers.
- `models/` — SQLAlchemy ORM models (project, observation, methodology, report, risk).
- `schemas/` — Pydantic request/response DTOs (project, evidence, agent).
- `services/` — business logic between routes and models (projects, evidence, agent, queries).
- `agent/` — LLM reasoning layer (client, prompts, retrieval, orchestration).

## Public interface
`app.main:app` (the ASGI app) is the process entry point, e.g. for `uvicorn app.main:app`. Subpackages are imported directly by name (`app.api`, `app.core`, `app.models`, `app.schemas`, `app.services`, `app.agent`) — there is no re-exporting `__init__.py`.

## Depends on
FastAPI, SQLAlchemy/GeoAlchemy2 (via `core`/`models`), the `openai` SDK (via `agent`), and Pydantic Settings for configuration.
