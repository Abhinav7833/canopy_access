# Canopy MVP — Backend, Database, Frontend & LLM Agent

**Date:** 2026-07-03
**Status:** Approved design — ready for implementation planning
**Owner:** Cem (backend + database + LLM agent + frontend/mapping, per Pipeline Spec §8.2)
**Source docs:** `.claude/docs/vision/` — Technical Direction Brief, Demo Build Document, Engineering Supplement (MVP Handoff), Geospatial Pipeline Spec

---

## 1. Overview & guiding principle

Canopy is a green-finance intelligence platform that turns satellite/environmental data into finance-grade, traceable **evidence** for investors, insurers, development banks, and green-bond stakeholders. This spec covers the **evidence → decision layer** that sits on top of the existing Google Earth Engine pipeline (`canopy_pipeline/`, already built): a FastAPI backend, a PostgreSQL/PostGIS/pgvector database, an LLM reasoning agent, and a Next.js frontend with mapping.

**Guiding principle — evidence is the central primitive.** Every dashboard number, risk flag, answer, and memo statement must trace to a stored evidence item. The LLM *explains and reports*; it never computes environmental findings or infers from pixels. This is what makes Canopy feel like a finance-grade diligence tool rather than a generic AI dashboard.

**Execution model — precomputed store.** The real pipeline is run **offline** on a small set of curated projects; its output is seeded into Postgres + local asset files. At demo time the backend serves stored evidence and the LLM explains it. A live "run analysis" endpoint is a stretch goal. This matches the Engineering Supplement's Option 1, and the precomputed assets *are* the real pipeline's output — no faked data.

## 2. Scope

| In scope (MVP) | Out of scope |
| --- | --- |
| Curated demo projects with fixed boundaries | Open-ended user-uploaded AOI processing |
| Precomputed before/after imagery + overlays | Live cloud masking / imagery processing at demo time |
| Precomputed vegetation, land-cover, flood, construction, and risk metrics | Production-grade hazard/underwriting/carbon-certification models |
| Evidence cards with provenance, method, confidence | Untraceable AI-generated conclusions |
| Bounded Q&A over structured evidence | Free-form LLM speculation or investment advice |
| Generated due-diligence / monitoring memo | Audited compliance certification or legal sign-off |
| Architecture shaped for the later modular engine | Full production workflow orchestration + global monitoring |
| Single-user demo (no auth) | Multi-tenancy, RBAC |

**Definition of done:** a non-technical finance user can select a project, view its boundary, inspect before/after imagery and structured observations, ask bounded questions, and generate a finance-ready memo — with no developer intervention and no live-GEE dependency on the demo path.

## 3. Architecture & data flow

```
OFFLINE (once, by the team):
  canopy_pipeline.run_pipeline(project)  ──►  raw §3.1 JSON
        └─ or a checked-in JSON fixture (unblocks BE/FE dev without GEE auth)
  scripts/seed.py:  JSON ──► relational rows (Postgres) + local asset files

DEMO (live):
  Next.js frontend ──► FastAPI ──► Postgres (stored evidence, PostGIS geometry)
                             └──► LLM agent (OpenAI-compatible, over stored evidence only)
                             └──► /static local files (RGB/overlay PNGs, GeoJSON)
  [stretch] POST /analyses ──► threadpool run_pipeline ──► seed ──► serve
```

Stack: **FastAPI** + SQLAlchemy 2.0 / GeoAlchemy2 + Alembic; **PostgreSQL + PostGIS + pgvector** via Docker Compose; **Next.js** (App Router) + Tailwind; **React Query** (server state) + **Zustand** (UI state); **MapLibre GL** for mapping.

## 4. Repository layout (monorepo)

```
backend/
  app/
    main.py               # FastAPI app factory, router mounting
    core/                 # config (.env), db session, storage abstraction, logging
    models/               # SQLAlchemy + GeoAlchemy2 ORM models
    schemas/              # Pydantic v2 response/request contracts
    api/routes/           # thin controllers: projects, evidence, ask, reports, analyses
    services/             # business logic: evidence retrieval, risk assembly, memo builder
    agent/                # LLM client, system prompt, guardrails, retrieval
  alembic/                # migrations
  tests/                  # pytest (unit + API integration)
  pyproject.toml          # ruff + mypy + pytest config
frontend/
  src/
    app/                  # Next.js App Router routes (the 7 screens)
    components/{ui,features,layout}
    hooks/
    services/             # typed API client
    stores/               # Zustand (UI) ; React Query wired in providers
    types/
  package.json            # eslint + prettier + tsc
canopy_pipeline/          # (unchanged) real GEE engine
seed_data/                # curated project JSON fixtures + downloaded assets
scripts/seed.py           # JSON → DB rows + local assets
docker-compose.yml        # postgres(+postgis+pgvector), backend, (frontend dev)
```

## 5. Data model (PostgreSQL)

Follows Engineering Supplement §5, reconciled with the pipeline's actual JSON output.

- **projects** — `id, name, asset_type, country, financing_type, monitoring_objective, status, screening_status, risk_score, risk_band, confidence, main_finding`
- **project&#95;boundaries** — `id, project_id, geom (PostGIS Polygon 4326), crs, source, area_hectares, validation_status`
- **observations** — `id, project_id, observation_type, period_start, period_end, summary, severity, confidence, created_at`
- **metrics** — `id, observation_id, metric_name, value, unit, baseline_value, comparison_value, method_id`
- **evidence&#95;items** — `id, observation_id, source_name, source_date, method_id, confidence, limitations (jsonb), financial_relevance, supporting_assets (jsonb)`
- **risk&#95;scores** — `id, project_id, score_type, score_value, score_band, drivers_json, updated_at`
- **methodologies** — `id, method_id, name, description, data_sources, assumptions, limitations, version`
- **reports** — `id, project_id, report_type, generated_at, evidence_ids_json, content, report_uri`
- **qa&#95;logs** — `id, project_id, question, answer, evidence_ids_json, model, created_at`
- **doc&#95;chunks** *(stretch)* — `id, project_id, kind, text, embedding vector` for pgvector semantic retrieval

**Methodology seed (static):** `ndvi_change_v1`, `build_v1`, carbon `AR-ACM0003`, and the composite risk score — each with plain-English description, data sources, assumptions, and limitations.

## 6. Seed pipeline (offline data preparation)

This is the highest-leverage hidden task — the demo only feels credible if prepared assets are consistent and labelled. `scripts/seed.py`:

1. Loads a curated project's request + result JSON (from a live `run_pipeline` run **or** a checked-in fixture in `seed_data/`).
2. Downloads the pipeline's RGB/overlay/GeoJSON assets to `seed_data/assets/<project_id>/` (local storage).
3. Maps the pipeline JSON onto the relational tables: `summary`→project fields + risk_scores; `metrics{}`→metrics rows; `evidence[]`→observations + evidence_items; boundary from AOI coords → PostGIS geometry.
4. Inserts the static methodology rows.
5. Asserts every metric and evidence card resolves to an evidence_item id (traceability check).

Fixtures decouple backend/frontend development from Google Earth Engine auth: devs run against committed JSON; the team regenerates fixtures when the pipeline changes.

**Minimum dataset:** 1 flagship + 2 lighter projects; 2–3 before/after image pairs and 3–5 overlays for the flagship; 8–15 evidence cards; 1 methodology entry per metric type; 2 report templates.

## 7. Backend API (FastAPI)

Matches Engineering Supplement §8 — serves **product objects**, never raw implementation detail.

```
GET  /projects                       list + high-level status
GET  /projects/{id}                  metadata, financing, boundary ref
GET  /projects/{id}/boundary         GeoJSON boundary
GET  /projects/{id}/imagery          before/after image + overlay URLs + date metadata
GET  /projects/{id}/observations     dated observations
GET  /projects/{id}/metrics          dashboard metrics + historical values
GET  /projects/{id}/risk             risk score, band, drivers
GET  /projects/{id}/evidence         evidence cards + supporting asset URIs
POST /projects/{id}/ask              bounded Q&A over allowed evidence
POST /projects/{id}/reports          generate due-diligence / monitoring memo
GET  /reports/{id}                   retrieve generated memo content / URI
[stretch] POST /analyses             async live pipeline run + status polling
```

Conventions: consistent JSON error envelope `{ "error": { "code", "message", "detail" } }`; validation errors → 422; not-found → 404; every response is a Pydantic-typed contract.

## 8. LLM reasoning agent

- **Provider-agnostic:** an OpenAI-compatible client (`base_url + api_key + model` from `.env`), swappable across OpenAI / Anthropic / Google, MCP-ready. Server key for the demo; a UI "bring-your-own-key" field is a stretch.
- **Deterministic retrieval (MVP):** select evidence by `project_id` (+ optional `observation_type`); `/ask` honours `allowed_evidence_ids` scoping. pgvector semantic retrieval is a stretch; retrieved chunks must still map back to typed evidence IDs.
- **Guardrails (Engineering Supplement §9 system prompt):** answer only from supplied evidence/metrics/methodology; separate observed vs modelled/proxy vs unsupported; always cite evidence IDs; state uncertainty and limitations; if evidence is insufficient, say what is missing and recommend human review; refuse legal/audit/regulatory/carbon-verification/investment-advice claims. Responses return `evidence_used[]`, `confidence`, `limitations[]`, and `unsupported_claims_refused[]`.
- **Memo generation:** fills the Appendix B skeleton (executive summary, key observations with evidence IDs, risk & compliance relevance, evidence table, limitations, recommended next review) with cited evidence only. Every generated report logs the evidence IDs it used.

**Allowed:** answer from retrieved evidence, generate memos/summaries, explain uncertainty, classify/route questions to evidence. **Disallowed:** invent findings not in the store, pixel-level inference, legal/audit/carbon-verification conclusions, return predictions, or hide limitations.

## 9. Frontend (Next.js + MapLibre + Tailwind) — 7 screens

1. **Portfolio / Project Selector** — choose a curated project (name, type, country, financing, status badge, latest observation date, risk).
2. **Project Overview** — boundary map, metadata, financing/monitoring context, data-source summary.
3. **Evidence Timeline** — before/after imagery swipe, overlay toggles, observation markers, source labels.
4. **Metrics Dashboard** — vegetation change, land-cover change, flood/fire, construction proxy, risk score + confidence.
5. **Evidence Drawer** — auditable cards: source, method, date, confidence, limitations, linked overlay/image.
6. **Ask Canopy** — bounded chat with cited answers, source references, and visible refusals for unsupported claims.
7. **Generate Memo** — rendered finance-ready report (HTML/Markdown) with evidence table + limitations. PDF export is a stretch.

**Mapping (hard constraint — the browser blocks remote CDNs/tiles):** MapLibre GL JS, self-hosted via npm, **no base tiles**. The pipeline's RGB composite PNG is rendered as a georeferenced image layer pinned to the AOI bounds, with the GeoJSON boundary and overlay PNGs as additional layers and a before/after swipe. No remote tile requests. **UI principle:** the map is the entry point, not the product — the product is turning observations into finance-grade evidence.

**State:** React Query for all server data (projects, evidence, metrics, ask, reports); Zustand for light UI state (selected overlay, swipe position, drawer open). Optimistic updates are unnecessary — all reads are cheap and the one write (memo/ask) is pessimistic.

## 10. Storage abstraction

A small interface (`get_url(key)`, `put(key, bytes)`, `open(key)`) with a **local filesystem** implementation for the demo (assets under `seed_data/assets/`, served at `/static`). An S3/MinIO implementation can drop in later without touching callers. No cloud storage for the MVP.

## 11. Error handling & conventions

| Case | Backend | Frontend |
| --- | --- | --- |
| Validation | 422 + field errors | inline field / toast |
| Not found | 404 + error envelope | empty state |
| LLM insufficient evidence | 200 + qualified refusal in body | render refusal + human-review flag |
| Server error | 500 + logged | generic message + retry |

Backend uses structured logging; every `/ask` and `/reports` call records the evidence IDs used (audit trail).

## 12. Testing strategy & acceptance criteria

**Testing layers:** pytest unit tests (services, agent guardrails, seed mapping); pytest API integration tests (each endpoint against a seeded test DB); frontend component tests (Testing Library); one end-to-end happy-path (Playwright) covering select → view → ask → memo.

**Acceptance criteria (Engineering Supplement §12):**
- **Core flow:** a user completes select → boundary → before/after → metrics → ask → memo with no developer intervention.
- **Traceability:** every displayed metric, risk flag, Q&A answer, and report conclusion references ≥1 evidence item.
- **LLM safety:** the assistant refuses or qualifies unsupported claims and never invents findings outside the store (tested with adversarial prompts).
- **Uncertainty:** UI and memo distinguish observed evidence, proxy/modelled indicators, and limitations.
- **Determinism:** the demo path has no dependency on live geospatial processing.
- **Production alignment:** schema and UI can later support automated evidence generation without a conceptual rewrite.

## 13. Build phases

- **P0 — Data package:** finalize curated projects; produce/capture seed JSON fixtures + assets; write the evidence-language standard.
- **P1 — Backend foundation:** Docker Compose (Postgres/PostGIS/pgvector); DB schema + Alembic; storage abstraction; `scripts/seed.py`; read endpoints (`/projects`, `/boundary`, `/imagery`, `/observations`, `/metrics`, `/risk`, `/evidence`).
- **P2 — Frontend foundation:** project selector, overview map (MapLibre), imagery viewer, metrics dashboard, evidence drawer; typed API client; React Query + Zustand wiring.
- **P3 — LLM integration:** `/ask` with deterministic retrieval, guardrail system prompt, evidence citations, refusal behavior; audit logging.
- **P4 — Report output:** `/reports` memo generation + in-app rendered view (evidence table + limitations).
- **P5 — QA & polish:** end-to-end path, hallucination/refusal tests, copy polish, visual polish, demo script, one-page "demo vs production" explainer.

## 14. Stretch goals

Live `POST /analyses` (async `run_pipeline` in a threadpool with status polling); PDF export of the memo; pgvector semantic retrieval; UI bring-your-own-key field; S3/MinIO storage backend.

## 15. Assumed defaults (state now to avoid re-litigation)

- Local static-file storage; no S3/MinIO for the demo.
- No auth (single-user demo).
- pgvector present in the DB image but retrieval is deterministic-by-`project_id` for the MVP.
- Monorepo; `canopy_pipeline/` stays where it is (not moved to `geospatial/`).
- Flagship demo asset: a solar/renewable project (Nur Navoi) with Mikoko mangrove as a vegetation-rich secondary — final flagship pick confirmed in P0.
- Memo output is in-app HTML/Markdown; PDF is a stretch.

---

*Engineering discipline: a pre-commit hook (`.claude/hooks/pre-commit-review.sh`) blocks code commits until `/simplify` + `/code-review` have run on the staged diff, and runs ruff/mypy/pytest + eslint/tsc gates once those toolchains exist.*
