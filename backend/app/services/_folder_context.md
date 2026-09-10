---
module: services
owns: [services]
last_reviewed: 19fd84285bd4
---
# services
Business logic sitting between the HTTP routes and the ORM models/agent layer: project lookups, dossier assembly, evidence + imagery, and agent-backed Q&A/report generation.

## Structure
- `projects.py` — `list_projects()`/`get_project_detail()` (risk derived from the `confidences` row), `get_project()` (raises `NotFound`), `get_boundary_geojson()` (PostGIS `ST_AsGeoJSON`), `get_imagery()` (builds `Imagery`/`ImageLayer` from evidence `supporting_assets`), and `get_dossier()` which **assembles** the dossier from its normalized tables.
- `evidence.py` — `evidence()` per-project read, 404-ing via `get_project()` first.
- `queries.py` — shared low-level SQLAlchemy select helper (`evidence_for_project`) reused by `evidence.py` and `app.agent.retrieval`.
- `agent.py` — `ask()` (calls `app.agent.answer_question`, persists a `QaLog`) and `create_report()`/`get_report()` (calls `app.agent.generate_memo`, persists a `Report`).

## Public interface
Each module's functions are imported by name from `app.services.<module>` (e.g. `from app.services import projects as svc`) by the matching `api/routes/*` module, and `queries`/`projects` are also imported by `app.agent.retrieval`.

## Depends on
`app.models`, `app.schemas`, `app.core` (`errors.NotFound`, `storage`, `config`), and `app.agent` (`agent.py` calls into `answer_question`/`generate_memo`).
