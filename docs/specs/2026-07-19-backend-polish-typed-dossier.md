# Backend Polish — Typed Dossier Contract, Relationship Assembly, FK Indexes

**Date:** 2026-07-19
**Status:** Queued (design + plan) — the first backend task of a fresh session.
**Context:** Phase 0 normalized the dossier into typed tables (commit `085d284`), but a review found the *API boundary* is still untyped and the assembly is hand-rolled. This closes that gap. Read alongside `docs/specs/2026-07-17-dossier-normalization-design.md`.

## Goal

Make the `/dossier` response contract as typed as the database behind it, shrink the manual assembly, and index the FK columns. Purely internal quality — the JSON the frontend receives must stay byte-compatible (verify with a before/after snapshot of `GET /projects/<id>/dossier` for both assets).

## Problems being fixed

1. **Untyped response schema.** `app/schemas/project.py::Dossier` declares `disclosure: dict`, `claims: list[dict]`, `localization: dict`, `observation_series: list[dict]`, `cross_check: list[dict]`, `confidence: dict`, `extra="allow"`. The response is unvalidated and OpenAPI shows `dict`. Its docstring is also stale ("read straight from a fixture … no DB persistence yet" — false since Phase 0).
2. **Hand-assembled `get_dossier`.** `services/projects.py::get_dossier` builds a big dict by hand (manual trace + promised/observed union reconstruction). Adding a field touches model + migration + seed + assembly (4 places).
3. **No FK indexes.** New tables have only PK indexes; every `WHERE project_id = …` seq-scans.

## Plan

### Task 1 — Typed Dossier sub-models (schema)
In `app/schemas/project.py`, replace the `dict`/`list[dict]` fields with real pydantic models mirroring the assembled shape:
- `DossierTrace` (source, date: `str|None`, method, confidence, traces_to — all `str|None`)
- `DisclosureOut` (title, issuer, instrument, financing_date: `str|None`, doc_ref, region_hint, summary, trace: `DossierTrace`)
- `ClaimOut` (id, kind, promised: `float | str | None`, unit, source_span, trace)
- `AlternativeOut` (name, reason); `LocalizationOut` (region_hint, located_centroid: `tuple[float, float]`, confidence, method, alternatives_rejected: `list[AlternativeOut]`, trace)
- `SnapshotOut` (date, image_key, footprint_ha, ndvi, note, trace)
- `CrossCheckOut` (claim_id, observed: `float | str | None`, status, variance, evidence_ids: `list[str]`, trace)
- `ConfidenceOut` (on_track_pct, rationale, drivers: `list[str]`, risk_score, risk_band, trace)
- `Dossier` composes them; drop `extra="allow"`; rewrite the docstring to "assembled from normalized tables."
Keep field names/nesting identical so the serialized JSON is unchanged. Update the frontend `types.ts` only if a name diverges (it should not).

### Task 2 — Relationship-based assembly (reduce manual mapping)
Add SQLAlchemy relationships so a project's sections load as objects (e.g. `Project.claims`/`cross_checks`/`snapshots` ordered by `ordinal`, `Localization.alternatives`, `CrossCheck.evidence_links`). Then build the `*Out` models with a thin adapter instead of one giant dict:
- one shared `_trace(o) -> DossierTrace` and `_value(num, text) -> float|str|None` (already exist as `_trace_out`/`_value_out` — promote them),
- construct each `*Out` from its ORM row (a pydantic `model_validate` with `from_attributes` where the columns line up; explicit for the reconstructed union/trace/centroid fields).
Net: adding a plain column later means editing the model + `*Out` only, not a hand-written dict. Keep the scoped `cross_check_evidence` query (per project) from the review fix.

### Task 3 — FK indexes (migration)
New Alembic revision (on top of `d192822fd5c2`) adding indexes on: `claims.project_id`, `cross_checks.project_id`, `cross_checks.claim_id`, `cross_check_evidence.evidence_id` (the PK already covers `cross_check_id` first), `observation_snapshots.project_id`, `evidence_items.project_id`, `localization_alternatives.project_id`. Add matching `index=True` on the model columns so autogenerate stays consistent; include a `downgrade`. Apply to the live DB.

### Stretch (optional) — composite claim PK
Replace the `_claim_pk` string prefix with a composite PK `(project_id, id)` on `claims` and a composite FK on `cross_checks(project_id, claim_id)`. Removes the prefix leaking into the payload and the `trace.traces_to` mismatch. Bigger change (touches model, migration, seed, assembly, and the dossier's claim-id values) — only if the payload-id cleanliness is worth it; otherwise leave the documented prefix.

## Verification
- Snapshot `GET /projects/nur_navoi_solar/dossier` and `/projects/pizarro/dossier` before and after; assert byte-identical (the whole point — typing must not change output).
- Backend gate (ruff/format/mypy/pytest) + frontend gate green. Add a test that the typed `Dossier` rejects a payload with a wrong-typed field (proving validation now bites).
- `EXPLAIN` a dossier fetch shows index scans on `project_id`.

## Out of scope
- `methodologies` id/method_id de-dup; modeling `trace.traces_to` as a real FK edge (over-engineering for the demo). Note but don't do.
