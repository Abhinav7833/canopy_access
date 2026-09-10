# Canopy — Dossier Normalization (Single Source of Truth)

**Date:** 2026-07-17
**Status:** Approved design, pre-implementation
**Phase:** 0 (schema) — precedes the source-pack asset swap (Phase 1, see `2026-07-17-canopy-source-pack-assets-design.md`, whose data-model section this supersedes).

## Goal

Make the database the single source of truth for a project. Today the dossier is served from a JSON file the DB knows nothing about, and risk/confidence scalars are duplicated between `projects` and the dossier. Normalize the dossier into first-class relational tables, derive every duplicated field from one home, and delete the dead old-model surface. `/dossier` becomes a pure derived view; **no field is stored twice anywhere.**

## Principles ("deliver the best")

- **Typed columns over JSONB.** JSONB only for genuinely schemaless data (none remains after this).
- **Child tables** for structured or referential lists (`{name, reason}` alternatives; cross-check→evidence references).
- **Postgres arrays** (`ARRAY(String)`) for simple ordered scalar lists (drivers, limitations, supporting assets) — typed and ordered, not JSONB, not over-fragmented.
- **Real foreign keys** for every reference (integrity enforced by the DB).
- **One source per field** — derive, never duplicate.
- **API + dossier response shapes stay byte-compatible** — this phase is backend-internal; the frontend dossier pages are untouched.
- **Dead code is removed**, not left behind.

## Schema conventions

- **Primary keys:** string business ids for entities referenced elsewhere (`claims`, `observation_snapshots`, `cross_checks` — referenced by `cross_check.claim_id` and `trace.traces_to`); integer-identity surrogate PKs only for pure child rows never referenced by id (`localization_alternatives`). 1:1 section tables use `project_id` as PK.
- **Foreign keys:** every FK to `projects` (and every child→parent FK) is `ON DELETE CASCADE`, with matching SQLAlchemy relationship `cascade="all, delete-orphan"`. Deleting a project removes its entire dossier in one statement.
- **Audit columns:** every new table has `created_at TIMESTAMPTZ NOT NULL DEFAULT now()` (consistency with the existing `observations`/`risk_scores` convention).
- **Value typing:** `Date` for real dates (`financing_date`, snapshot `date`, `source_date`); `Numeric` for exact business quantities (`promised_num`/`observed_num` — credits, USD, MW, GWh); `Float` for measurements (`ndvi`, `footprint_ha`, `confidence`, `centroid_lon/lat`). No JSONB remains anywhere in the model.
- **Constraints:** `promised`/`observed` each carry a CHECK that exactly one of `*_num` / `*_text` is non-null. NOT NULL on every non-optional column.

## Target schema

A reusable `TraceMixin` provides the provenance value-object as typed columns on every dossier element (no JSONB trace blobs). `trace_traces_to` stays a plain string (its target is heterogeneous — a section name or a claim id — so it is not a FK):

```
TraceMixin: trace_source (str), trace_date (Date|null), trace_method (str|null),
            trace_confidence (str|null), trace_traces_to (str|null)
```

### New tables

**`disclosures`** — 1:1 with project
`project_id` (PK, FK→projects) · `title` · `issuer` · `instrument` · `financing_date` (Date|null) · `doc_ref` (str|null) · `region_hint` (str|null) · `summary` · +Trace

**`claims`** — 1:N
`id` (PK) · `project_id` (FK) · `ordinal` (int) · `kind` (str) · `promised_num` (float|null) · `promised_text` (str|null) · `unit` (str|null) · `source_span` (str|null) · +Trace
CHECK: exactly one of `promised_num` / `promised_text` is non-null. API reconstructs `promised` as number-or-string.

**`localizations`** — 1:1
`project_id` (PK, FK) · `region_hint` (str|null) · `centroid_lon` (float) · `centroid_lat` (float) · `confidence` (float|null) · `method` (str|null) · +Trace

**`localization_alternatives`** — 1:N child of localization
`id` (int identity PK) · `project_id` (FK→localizations.project_id) · `ordinal` (int) · `name` (str) · `reason` (str)

**`observation_snapshots`** — 1:N
`id` (PK) · `project_id` (FK) · `ordinal` (int) · `date` (Date) · `image_key` (str) · `footprint_ha` (float|null) · `ndvi` (float|null) · `note` (str|null) · +Trace

**`cross_checks`** — 1:N
`id` (PK) · `project_id` (FK) · `ordinal` (int) · `claim_id` (FK→claims.id) · `observed_num` (float|null) · `observed_text` (str|null) · `status` (str) · `variance` (str|null) · +Trace
CHECK: exactly one of `observed_num` / `observed_text`.

**`cross_check_evidence`** — join, M:N cross_checks ↔ evidence_items
`cross_check_id` (FK→cross_checks.id) · `evidence_id` (FK→evidence_items.id) · PK(both)

**`confidences`** — 1:1 (the single home for risk/confidence)
`project_id` (PK, FK) · `on_track_pct` (int) · `rationale` (str|null) · `drivers` (ARRAY(String)) · `risk_score` (int|null) · `risk_band` (str|null) · +Trace

### Modified tables

**`projects`** — DROP `risk_score`, `risk_band`, `confidence`, `main_finding` (now derived from `confidences`). Keeps `id, name, asset_type, country, financing_type, monitoring_objective, status, screening_status`. Add ORM relationships to `disclosure`, `localization`, `confidence`, `boundary` (all uselist=False).

**`evidence_items`** — re-parent from `observation_id` → `project_id` (FK→projects, CASCADE). `method_id` becomes FK→`methodologies.id` (nullable, RESTRICT — a methodology in use can't be deleted). `source_date` becomes `Date`. `limitations` and `supporting_assets` become `ARRAY(String)` (were JSONB). Keeps `id, source_name, confidence, financial_relevance`.

**`methodologies`** — convert `data_sources` / `assumptions` / `limitations` from JSONB to `ARRAY(String)` (consistency; reference data otherwise unchanged).

### Dropped tables

`observations`, `metrics`, `risk_scores` — old evidence/risk model, superseded by claims + observation_snapshots + cross_checks + confidences.

## Removed dead surface

- **Endpoints:** `GET /projects/{id}/observations`, `/metrics`, `/risk` (no frontend caller).
- **Backend:** `services/evidence.py::observations/metrics/risk`, `queries.py::metrics_for_project` (and any other now-unused query helper), schemas `ObservationOut` / `MetricOut` / `RiskOut`, models `Observation` / `Metric` / `RiskScore`.
- **Frontend:** `api.getObservations/getMetrics/getRisk`, `useObservations/useMetrics/useRisk`, and the `Observation` / `Metric` / `Risk` types — all currently unreferenced by any component. Also drop `confidence` and `main_finding` from the `ProjectDetail` type (removed from the API above).

## API compatibility (every rendered field unchanged)

Every field the frontend actually renders keeps its exact shape; only duplicated-and-unused fields are dropped.

- **`GET /projects/{id}/dossier`** — `services/projects.get_dossier` now **assembles** the `Dossier` from the six tables (disclosure, claims ordered by `ordinal`, localization + alternatives, snapshots ordered, cross_checks ordered + their `evidence_ids` from the join, confidence + drivers). Trace dicts reconstructed from `trace_*` columns; `promised`/`observed` reconstructed from `*_num`/`*_text`; dates serialized to ISO strings. Response is byte-compatible with today's fixture output. No file read.
- **`GET /projects` / `/projects/{id}`** — `risk_score` / `risk_band` (the only project-level risk fields the frontend consumes) are derived on read by LEFT-JOINing `confidences`. The two duplicated-and-unused fields — `ProjectDetail.confidence` (float) and `main_finding` — are **removed** from the schema and the frontend `ProjectDetail` type rather than derived (verified: no component reads them). `monitoring_objective` and `screening_status` stay (genuine project attributes, not duplication). All fields the frontend actually renders keep their exact shape.
- **`/boundary`, `/imagery`, `/evidence`** — unchanged; `evidence_for_project` now filters `evidence_items` by `project_id` directly.

## Fixtures & seed

**One merged fixture per project** (`seed_data/projects/<id>.json`) replaces the `<id>.json` + `<id>.dossier.json` pair — the last duplication removed. Shape:

```json
{
  "id": "...", "name": "...", "asset_type": "...", "country": "...",
  "financing_type": "...", "monitoring_objective": "...", "status": "monitored",
  "screening_status": "...", "aoi_coords": [[lon,lat], ...], "area_hectares": 0.0,
  "disclosure": { ...trace inline... },
  "claims": [ { "id","kind","promised","unit","source_span","trace" } ],
  "localization": { "region_hint","located_centroid":[lon,lat],"confidence","method","alternatives_rejected":[{"name","reason"}],"trace" },
  "observation_series": [ { "date","image_key","footprint_ha","ndvi","note","trace" } ],
  "cross_check": [ { "claim_id","observed","status","variance","evidence_ids":[...],"trace" } ],
  "confidence": { "on_track_pct","rationale","drivers":[...],"risk_score","risk_band","trace" },
  "evidence": [ { "id","source_name","source_date","method_id","confidence","limitations":[...],"financial_relevance","supporting_assets":[...] } ],
  "memo_ready": true
}
```

`scripts/seed.py` is rewritten to load the merged fixture and write the normalized rows: project (meta only), boundary, disclosure, claims, localization + alternatives, observation_snapshots, cross_checks + `cross_check_evidence` links, confidence + drivers, evidence_items. `promised`/`observed` are split into `*_num`/`*_text`; `located_centroid` into `centroid_lon/lat`. The traceability self-check is updated to assert, within the seed transaction (all-or-nothing), that every `cross_check.claim_id` resolves to a claim, every `evidence_id` resolves to an evidence item, and every `observation_snapshots.image_key` appears in some evidence's `supporting_assets` (the soft FK the DB can't enforce against image files). `ensure_assets`/Esri fetch is unchanged.

## Migration & tests

- An **Alembic migration** implements the schema change (drop columns/tables, alter `evidence_items`, add the eight tables, FK cascades, array conversions) with a working **`downgrade`** for reversibility. Tests build the schema from the models via the existing `conftest` `create_all`; the live dev DB on `:5433` is migrated (or dropped/recreated) and reseeded with both current assets.
- **Backend tests:** delete the removed-endpoint tests; add tests that `/dossier` assembled from tables matches the expected shape, that `/projects` risk fields come from `confidences` (change one and see it reflected), that evidence resolves by `project_id`, and that a cross_check's `evidence_ids` come from the join. Keep the 404 / malformed-input coverage adapted to the new seed path.
- **Frontend:** remove the dead hooks/types/api methods and any test referencing them; the dossier pages and their tests are unchanged (shape identical).

## Out of scope

- Real satellite imagery (data-population task).
- The `reports` / `qa_logs` tables and the agent/LLM endpoints (untouched).

## Sequencing

- **Phase 0 (this spec):** normalize + de-duplicate + remove dead code, keeping the two current assets (Nur Navoi as-is, Pizarro) working through the new model.
- **Phase 1:** the source-pack asset swap — now just "author two merged fixtures on the normalized model" (Pizarro removed, Nur Navoi reworked, Mikoko Pamoja added) plus the asset-type frontend rendering.

## Success criteria

- No scalar (risk_score/band/confidence/rationale/drivers) or dossier section is stored in more than one place; grep/schema review confirms one home per field.
- `GET /dossier` is byte-compatible with before; `/projects` and `/projects/{id}` keep every field the frontend renders (only the unused `confidence`/`main_finding` are dropped). Existing frontend renders unchanged.
- The dead endpoints/hooks/models are gone; `grep` finds no references.
- Backend + frontend gates green; the app drives cleanly through both assets.
