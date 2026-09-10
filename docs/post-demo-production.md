# Canopy — Post-Demo → Production Roadmap

**Status:** Living backlog. Everything the MVP demo defers, simplifies, or stubs — to be addressed when moving from the precomputed demo (Option 1) to the modular monitoring engine (Option 2).
**Companion to:** `docs/specs/2026-07-03-canopy-mvp-design.md` (the demo spec) and the vision docs in `.claude/docs/vision/`.
**How to use:** As we finish the demo, revisit each section. Items are grouped by area with an owner where the vision docs assign one (Luna = geospatial/GEE, Abhinav = ingestion/ML/storage, Cem = backend/API/LLM/frontend/deploy). Keep the conservative-evidence language throughout.

---

## 0. The core architectural shift

The demo is **precomputed evidence served from a store**. Production is a **scheduled monitoring engine** that generates that evidence automatically. Reuse the frontend, the evidence data model, the report generator, and the LLM guardrails; replace the manual/precomputed inputs with scheduled processing jobs and automated alerts.

| MVP Demo | Production Engine |
|---|---|
| Manual/precomputed raster previews + overlays | Automated imagery ingestion, preprocessing, cloud masking, module execution |
| Static curated evidence rows in the DB | Scheduled evidence generation from geospatial workers |
| Rule-based risk score from prepared metrics | Configurable risk models with thresholds, alerts, optional ML components |
| Manual demo project loading (seed script) | Self-serve asset upload, boundary validation, monitoring cadence selection |
| Generated memo from selected evidence | Scheduled reports, alerts, audit trails, stakeholder exports |

**What already carries over (don't rebuild):** the production-shaped data model (projects / boundaries / observations / metrics / evidence_items / risk_scores / reports / qa_logs), the evidence-as-central-primitive discipline, the LLM guardrail system prompt, the `Storage` interface seam, and the OpenAI-compatible provider-agnostic LLM client.

## 1. Governance, ethics & data residency (non-negotiable — do first)

- [ ] **EU / UK data residency** — EU cloud + data centres. A major theme for a UK/EU launch; pick the cloud region before any hosted data lands. *(Cem)*
- [ ] **Closed / secured models** — "do like Anthropic": deliberate governance principles, no leaky data paths. Document the model/data governance posture.
- [ ] **Verification, not surveillance** — stay inside the green/ESG intent (not Palantir). Bake the framing into product copy and positioning.
- [ ] **Conservative evidence language everywhere** — keep monitoring / screening / evidence / proxy / confidence / limitations / human-review. Never imply audit-grade verification, compliance, or carbon credibility until formal validation standards exist.
- [ ] **Human-review flags** — surface and route low-confidence / material-change findings for human sign-off.

## 2. Data & geospatial pipeline productionisation

- [ ] **Scheduled ingestion** — productionise satellite data ingestion (move off manual/on-demand). *(Abhinav)*
- [ ] **Preprocessing at scale** — automated cloud masking, atmospheric correction, clipping, resampling, normalisation as a scheduled module. *(Abhinav owns the ingestion→ML hand-off; Luna owns masking/clipping inside GEE for her layers — confirm the boundary.)*
- [ ] **Finalise change-detection method** for build & reforestation (before/after). *(Luna)*
- [ ] **ML classification models** — land-cover / segmentation, canopy-height, asset detection, anomaly detection. Validate against ground truth. *(Abhinav model; Luna validates)*
- [ ] **SAR flood layer** — pre-calibrated Sentinel-1 in GEE (Luna's layer); raw SAR ingestion (Abhinav).
- [ ] **GEDI / biomass** — sparse LiDAR calibration; keep carbon as *screening*, not MRV, until methodology validated.
- [ ] **Per-use-case models** — biomass ≠ pollution ≠ canopy; each needs its own model. Expand scope beyond the one demo vertical deliberately.
- [ ] **Planet imagery** — evaluate for daily cadence upgrade (algal-bloom precedent); paid, optional.
- [ ] **Live `run_pipeline` as a service** — the demo's stretch `POST /analyses` becomes the core async processing path (2–5 min jobs, never blocks the API).

## 3. Storage (local → object storage)

- [ ] **Swap `LocalStorage` → `S3Storage`** via the existing `Storage` interface (one class + config; no caller changes).
- [ ] **Object storage** — S3 / GCS / Azure Blob / MinIO in the chosen EU region.
- [ ] **COG rasters** — store large rasters as Cloud-Optimised GeoTIFFs referenced by URL, streamable by tile; never inline.
- [ ] **Asset lifecycle** — retention, versioning, and cleanup policies for imagery/overlays.

## 4. Database

- [ ] **Managed PostgreSQL** in the EU region (residency), with connection pooling, automated backups, PITR.
- [ ] **Enable pgvector** and build the semantic-retrieval path (methodology snippets, report templates, evidence narrative chunks). Retrieved chunks must still map back to typed evidence IDs.
- [ ] **Migrations discipline** — Alembic in CI; no `create_all` in prod.
- [ ] **Indexing & spatial performance** — GiST indexes on geometry; query tuning as project count grows.

## 5. LLM reasoning agent

- [ ] **Bring-Your-Own-Key onboarding** — let institutions plug in their own provider keys (avoid the bill; clients already have AI budgets + usage governance). UI + secure per-tenant key storage.
- [ ] **MCP-ready tool surface** — expose the API to third-party tool-calling (the OpenAI-API standard already positions this).
- [ ] **Usage metering & cost controls** per tenant.
- [ ] **Provider-upgrade path** — model-agnostic client means new frontier models improve the product with zero changes; add an eval harness to validate before switching.
- [ ] **Semantic retrieval** (pgvector) replacing MVP deterministic-by-`project_id` retrieval, where it earns its cost.
- [ ] **Guardrail hardening** — expand the adversarial/hallucination test suite; keep evidence-ID citation + refusal behaviour.

## 6. Risk engine

- [ ] **Rules → configurable models** — thresholds per asset type / region; keep the methodology documented and visible.
- [ ] **Alerts** on threshold breaches and material change.
- [ ] **Optional ML components** — only where they earn their place over deterministic rules.
- [ ] **Still not an underwriting model** — position as monitoring support with human validation until formally validated.

## 7. Reports, alerts & exports

- [ ] **PDF export** of memos (deferred stretch in the demo).
- [ ] **Scheduled reports** and monitoring updates on the SLA cadence.
- [ ] **Audit trails** — full provenance for every generated report and Q&A (extend the demo's evidence-ID logging).
- [ ] **Stakeholder exports** and per-persona report templates (investor / insurer / development bank / green-bond).

## 8. Self-serve product flow

- [ ] **Asset upload** — user-provided AOIs (GeoJSON), replacing curated demo projects.
- [ ] **Boundary validation** — geometry/area/CRS checks (the pipeline's `AOI_TOO_LARGE`, `VALIDATION_ERROR`, etc. surfaced to users).
- [ ] **Monitoring cadence selection** — weekly/daily per data source; SLA framing (Sentinel ~10 days; Planet daily).
- [ ] **Portfolio management** — many projects per tenant, status tracking, monitoring history.

## 9. Auth, multi-tenancy & security

- [ ] **Authentication** (demo has none).
- [ ] **Multi-tenancy** — orgs/tenants with strict per-tenant data isolation.
- [ ] **RBAC** — roles/permissions.
- [ ] **Secrets management** — provider keys, DB creds, storage creds out of `.env` into a secrets manager.
- [ ] **Security review** — auth surfaces, injection, SSRF on any URL fetch, dependency audit.

## 10. Mapping (resolve the open decision)

- [ ] **Pick the mapping library** — Mapbox / Leaflet / deck.gl (open decision in Pipeline Spec §8.4). Determines whether outputs are GeoJSON, tile URLs, or raster references. *(Luna · Abhinav · Cem)*
- [ ] **Tile serving for COGs** — serve rasters by tile rather than whole-file.
- [ ] **Re-test the browser constraint** — confirm whether remote tiles/CDNs are actually blocked in the target environment (the demo assumed yes; verify before committing to a basemap strategy). If unblocked, a normal basemap is on the table.

## 11. Infra & operations

- [ ] **Background job queue** — Celery / Redis / Dramatiq / Prefect for async geospatial processing.
- [ ] **Observability** — structured logging, metrics, error tracking, tracing.
- [ ] **CI/CD** — tests + migrations + build/deploy pipeline (in the EU region).
- [ ] **Rate limiting & caching** — API protection and cheap-read caching.
- [ ] **Containerisation for prod** — the demo's Compose becomes a real orchestration target.

## 12. Quality at scale

- [ ] **Load / performance testing** on the processing path and API.
- [ ] **Expanded E2E** across the self-serve flow (not just the curated demo path).
- [ ] **Data-quality monitoring** — scene availability, cloud cover, missing-data handling surfaced as evidence limitations.

## 13. SLA & positioning

- [ ] **State a real SLA cadence** — weekly now, daily later (Sentinel ~10-day revisit; Planet daily).
- [ ] **Buyer-persona adaptation** — start with green-bond / project-finance monitoring; adapt outputs per persona later. Avoid one-size-fits-all.
- [ ] **Free social tier** (the funnel) — free land-cover + vegetation monitoring + risk scoring/alerts for small, climate-exposed developers → feeds the institutional premium.

## 14. Team ownership (re-integration for prod)

- **Luna** — geospatial GEE pipeline, indices, change detection, SAR flood layer, simple carbon, map output files, ML-output validation.
- **Abhinav** — productionised ingestion + scheduling, preprocessing module, storage/pgvector indexing, ML classification model.
- **Cem** — FastAPI backend & API, LLM reasoning agent, frontend + mapping, cloud-storage upload + deployment.

## 15. Open decisions to revisit

- [ ] Mapping library (Pipeline Spec §8.4).
- [ ] Which flagship + additional verticals to productionise first (MDB anti-corruption / green-bond reforestation / infrastructure impact).
- [ ] Whether to keep Postgres+PostGIS or add specialised geospatial infra at scale.
- [ ] Report formats (Markdown/HTML/PDF) and which are contractual per persona.
- [ ] How much source methodology to expose to the user.

## 16. Red-team questions the product must keep surviving

Where did this metric come from? · What's the source date and resolution? · Is this observed or inferred? · How confident is the system? · What are the limitations? · Can this be used as compliance proof? · What changes in production vs the demo? · What happens when evidence is insufficient?

## 17. Deferred code-review findings (Plan 1 backend review, 2026-07-09)

Minor items surfaced by the Plan 1 review and deliberately deferred as demo-acceptable — revisit when hardening for production:

- [ ] **`/boundary` has no `response_model`** — returns a raw GeoJSON dict; fine because GeoJSON is dynamic, but a typed `Feature` schema would make the contract explicit in OpenAPI.
- [ ] **Fragile string parsing** — `_method_id` (parsing `method_id:` out of free text) and the imagery `label` / `"rgb" in name` classifier are heuristics that assume controlled demo asset names; move `method_id` to a structured fixture field and derive `kind` explicitly.
- [ ] **`test_db.py::test_postgis_available` uses the app (dev) engine** instead of the isolated test engine — harmless now, but couples one test to the dev DB.
- [ ] **`alembic/env.py` has no offline (`--sql`) branch** — `alembic upgrade head --sql` won't work; add the `context.is_offline_mode()` path when a gated-deploy SQL review is needed.
- [ ] **`main()` in `scripts/seed.py` hard-indexes fixture keys** — a malformed fixture crashes with a raw `KeyError`; add validation/clear errors if fixtures become user-supplied.
- [ ] **`/imagery` returns an empty `layers` list** for a project whose evidence carries no `supporting_assets` — acceptable, but worth a defined empty-state contract for the frontend.
- [ ] **Flat per-project asset filename namespace** — `ensure_assets` and `get_imagery` key assets by bare filename, so two captures of the same project arriving under the same filename collide on disk and in the layer list. Fine while a project holds one AOI reference frame; namespace assets by observation/period when dated captures land and a snapshot's `image_key` starts resolving to per-date imagery.
- [x] ~~**Duplicated evidence-by-project query**~~ — resolved: extracted `app/services/queries.py`; `get_imagery`, `services/evidence`, and `agent/retrieval` all reuse it.
