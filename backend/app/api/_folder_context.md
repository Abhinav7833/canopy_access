---
module: api
owns: [routes]
last_reviewed: d8ef77c90437
---
# api
The HTTP layer: FastAPI routers that translate requests into `app.services` calls and shape responses with `app.schemas`.

## Structure
- `routes/` — one router module per resource, each included in `app.main.create_app()`:
  - `projects.py` — `GET /projects`, `GET /projects/{id}`, `GET /projects/{id}/boundary`, `GET /projects/{id}/imagery`.
  - `evidence.py` — `GET /projects/{id}/observations`, `/metrics`, `/risk`, `/evidence`.
  - `agent.py` — `POST /projects/{id}/ask`, `POST /projects/{id}/reports`, `GET /reports/{id}`.

## Public interface
Each `routes/*.py` exposes a module-level `router` (`APIRouter`), imported by `app.main` as `agent_routes.router`, `evidence_routes.router`, `projects_routes.router` and mounted with `app.include_router(...)`.

## Depends on
`app.core.db` (`get_db`), `app.agent.client` (`get_llm_client`, in the agent routes), `app.schemas.*` (response models), and `app.services.*` (request handling).
