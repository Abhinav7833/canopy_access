---
module: models
owns: [models]
boundary: backend/app/models/__init__.py
last_reviewed: df33d2bd24cb
---
# models
SQLAlchemy ORM models for the Canopy schema: projects, monitoring observations/evidence, methodologies, risk scores, and generated reports/QA logs.

## Structure
- `project.py` — `Project` and `ProjectBoundary` (PostGIS `POLYGON` geometry via GeoAlchemy2).
- `observation.py` — `Observation`, `Metric`, `EvidenceItem`, linked by foreign keys (project → observation → metric/evidence item).
- `methodology.py` — `Methodology` (data sources, assumptions, limitations as JSONB).
- `risk.py` — `RiskScore` (composite score, band, JSONB drivers) per project.
- `report.py` — `Report` (generated memo content + cited evidence IDs) and `QaLog` (ask/answer history).

## Public interface
`app/models/__init__.py` re-exports `Base` (from `app.core.db`) plus every model class: `Project`, `ProjectBoundary`, `Observation`, `Metric`, `EvidenceItem`, `RiskScore`, `Methodology`, `Report`, `QaLog`. Other modules import from `app.models` rather than the individual files.

## Depends on
`app.core.db` (`Base`), SQLAlchemy ORM, GeoAlchemy2 (`Geometry`) for `ProjectBoundary`.
