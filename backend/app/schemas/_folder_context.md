---
module: schemas
owns: [schemas, dtos]
last_reviewed: 1c1ed69203e1
---
# schemas
Pydantic request/response DTOs for the API layer, kept separate from the SQLAlchemy models in `app/models`.

## Structure
- `project.py` — `ProjectSummary`, `ProjectDetail` (list/detail views), `ImageLayer`/`Imagery` (evidence imagery layers), and `Dossier` — the assembled disclosure → confidence narrative, now a fully typed tree of sub-models (`DisclosureOut`, `ClaimOut`, `LocalizationOut`, `SnapshotOut`, `CrossCheckOut`, `ConfidenceOut`, each carrying a `DossierTrace`) rather than free-form dicts.
- `evidence.py` — `EvidenceItemOut` — response shape for the `/evidence` endpoint.
- `agent.py` — `AskRequest`/`AskResponse` (Q&A), `ReportRequest`/`ReportOut` (memo generation).

## Public interface
All classes are imported directly by name from their file, e.g. `from app.schemas.project import ProjectSummary`, by `api/routes/*` (as `response_model`) and `services/*` (to construct responses). No package-level re-export (`__init__.py` is empty).

## Depends on
Pydantic (`BaseModel`, `ConfigDict`, `Field`). Several `*Out` schemas use `model_config = ConfigDict(from_attributes=True)` to validate directly off `app.models` ORM instances.
