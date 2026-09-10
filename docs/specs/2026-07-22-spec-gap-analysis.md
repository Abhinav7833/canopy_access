# Canopy — Spec Gap Analysis

**Date:** 2026-07-22
**Analyst:** read-only gap analysis (no code changed)
**Spec compared:** `/Users/cemkilinc/Desktop/Canopy_Pipeline_Spec_hackathon.docx` — *"CANOPY Green Finance Intelligence Platform · Geospatial Pipeline · Technical Specification v0.3, July 2026"* by **Luna** (Geospatial Lead).
**Implementation surveyed:** `/Users/cemkilinc/Desktop/Canopy` on branch `canopy-mvp` — `backend/app/`, `canopy_pipeline/`, `seed_data/`, `frontend/src/`, `scripts/seed.py`, `docs/`.

---

## 0. The one-paragraph framing (read this first)

Luna's spec describes a **fully deterministic Google Earth Engine pipeline** (Path A EO engine + Path B disclosure-verification, matching, evidence graph, cross-checks, confidence blend, legal/financial connectors) that she claims is *"built and running NOW"* for the demo assets **Núñez de Balboa** and **Francisco Pizarro** (spec §1.4, §10). **None of that pipeline lives in this repo.** What this repo actually ships is a **product shell**: a FastAPI service that serves **hand-authored, precomputed "dossier" JSON fixtures** (every `method` field literally ends in `(stub)`), single-timestamp Esri imagery reused as fake before/after, and a **genuinely real, evidence-grounded LLM Ask/Memo layer**. The product's own direction docs (`docs/specs/2026-07-13-canopy-disclosure-direction.md`) are explicit that this is *"a validation set, not production … ~5–6 precomputed screens bound to the LLM, no live processing."* The gap is therefore **not** "a few features are stubbed" — it is that **Luna's entire scientific engine is unintegrated**, and the product deliberately runs on stubs pending her drop-in. This analysis inventories that gap precisely so the integration work can be planned.

Two structural facts frame everything below:
- **The backend never calls the pipeline.** `grep` for `canopy_pipeline` / `run_pipeline` / `verify_and_report` in `backend/app/` returns **nothing**. The FastAPI product and the `canopy_pipeline/` package are fully decoupled.
- **The repo's `canopy_pipeline/` is not Luna's v0.3 pipeline.** It is an older, ~378-line real-GEE **Path-A-only** skeleton (Nur Navoi + Mikoko examples). It is missing almost every module the spec §4.1 folder layout names.

---

## 1. Missing — expected by the spec but NOT delivered

For each: **spec expectation → what exists today → the gap.**

### 1.1 Path B — the entire disclosure-verification engine
- **Spec (§1.2, §4.1, §4.2):** `verify_disclosure()` and `verify_and_report()` drivers; `matching/entity_resolution.py` (rapidfuzz match of a disclosure to a GEM/registry asset), `matching/reference_loader.py`, `matching/registries/`; footprint refinement from OSM / Giri mangrove extent.
- **Today:** `canopy_pipeline/` has **no** `verify_disclosure.py`, `verify_and_report.py`, `matching/`, `taxonomy.py`, `cross_reference/`, `evidence/`, or `disclosure/` directories. Entity resolution / match_score / margin / matched_fields (spec §6.1) do not exist as code. The **localization** shown in the product (`seed_data/projects/*.json` → `localization.method`) is a hand-written sentence ending `"(precomputed, stub — no ML this sprint)"` with a hardcoded `confidence` float.
- **Gap:** 100% of Path B is absent from the pipeline. The product *simulates* its output shape with fixtures.

### 1.2 Real multi-date Sentinel imagery + change detection
- **Spec (§1.3 stages 3–5, §6.2):** two cloud-masked Sentinel-2 median composites (before/after) + Sentinel-1 backscatter; bi-temporal `|ΔNDVI|>0.1` change map; per-year NDVI slope with interannual-noise gating.
- **Today:** `scripts/seed.py::ensure_assets` fetches **one** Esri World Imagery PNG per AOI (`fetch_aoi_imagery`, guarded by a `fetch_attempted` flag) and assigns that **same single image** to *both* `before_rgb.png` and `after_rgb.png`. Verified: `before_rgb.png` and `after_rgb.png` are **byte-identical** (matching md5) for all three asset folders. There is no Sentinel-2, no composite, no ΔNDVI computation feeding the product. The standalone `canopy_pipeline` *does* compute a real GEE composite + change (`data/sentinel2_loader.py`, `analytics/change_detection.py`), but it is unwired and requires GEE credentials (`session.py` → `ee.Initialize`).
- **Gap:** No real temporal imagery in the product; "before/after" is a single present-day Esri snapshot; change detection is not run on product data.

### 1.3 NDVI / NDWI / NBR indices on product data
- **Spec (§6.2):** NDVI (Rouse 1974), NDWI (McFeeters 1996), NBR (Key & Benson 2006) per composite.
- **Today:** `canopy_pipeline/indices/{ndvi,ndwi,nbr}.py` implement the real formulas (5–8 lines each) but are only reachable through the unwired `run_pipeline`. In the dossiers, `ndvi` is a **single hand-authored float per snapshot** (e.g. Nur Navoi `0.22 → 0.14 → 0.11`); `ndwi`/`nbr`/`ndvi_slope` never appear (grep: 0 dossiers).
- **Gap:** Indices exist as code but are not computed for the shipped assets; product NDVI numbers are authored, not measured.

### 1.4 Carbon — ESA CCI Biomass method
- **Spec (§6.2, §7):** `carbon_estimate = AGB × 0.47 × 3.67 × area`, AGB from **ESA CCI Biomass** (`ESA_CCI_AGB`), banded (SD or ±50% Tier-1), assurance = MOD.
- **Today:** `canopy_pipeline/analytics/carbon_model.py` uses a different, weaker method — `max(ndvi_end,0) × BIOMASS_FACTOR × 0.47 × 3.67` (an **NDVI→biomass linear proxy**, not ESA CCI; the module's own docstring calls NDVI→biomass "the weak, saturating link"). In the dossiers, carbon is a stub (`carbon_ar_acm0003 (stub)`, Mikoko only); no banded estimate, no ESA CCI source.
- **Gap:** Carbon is either a proxy (pipeline) or a stub (product); the spec's ESA CCI + IPCC-banded method is not implemented anywhere here.

### 1.5 Physical-risk hazards (fire / flood / degradation)
- **Spec (§6.3, §7):** Fire = Fosberg FFWI (ERA5) × NDVI fuel; Flood = Huizinga depth-damage on WRI Aqueduct + Otsu-on-S1 minus JRC GSW permanent water; degradation = pct veg loss; composite = worst-hazard; plus `fire_severity_dnbr`, `community_exposure` (GHSL).
- **Today:** `canopy_pipeline/analytics/risk_scoring.py` computes a simplified risk from `ndvi_trend`, `nbr_mean`, and SAR `water_fraction` — **not** Fosberg/ERA5, **not** Aqueduct/Huizinga, **not** Otsu, **not** GHSL. In the product, hazards are absent entirely: grep of dossiers for `fire`/`flood`/`aqueduct` → **0**; only a single opaque `risk_score`/`risk_band` appears in `confidence` (e.g. Nur Navoi `risk_score: 22, risk_band: Low`), hand-authored.
- **Gap:** No per-hazard scoring, no published-method risk, no fire/flood sub-scores. The product's risk is a single authored number.

### 1.6 Energy — generation & avoided emissions (PVWatts)
- **Spec (§6.4):** `generation = capacity × GHI × 0.80 × tracking ÷ 1000` (NREL PVWatts, ERA5 GHI); `avoided_emissions = generation × 1000 × grid_factor` (per-country factor, e.g. Spain 0.123).
- **Today:** No PVWatts, no ERA5 GHI, no grid-factor table in code (grep `pvwatts`/`avoided`/`gwh` in pipeline → 0 real impl). Nur Navoi's dossier carries a `generation_gwh` claim cross-checked by `generation_proxy_v1 (stub)`; the number is authored.
- **Gap:** Generation/avoided-emissions modelling absent; product shows a stubbed cross-check verdict only.

### 1.7 Cross-checks, verdicts & confidence blend
- **Spec (§6.5, §8):** deterministic verdicts `_check_scale` (LBNL land-use bands), `_check_timing` (**additionality**: build-year vs financing-year), `_check_band` (generation/CO₂), `cross_asset_co2_check` (per-MW intensity spread >0.25 → inconsistent), and a confidence blend over **testable checks only**. Verdict vocabulary: `consistent / partially_consistent / inconsistent / insufficient_data`.
- **Today:** `canopy_pipeline/analytics/screening.py` has a small if-ladder producing `Consistent / Partially consistent / Inconsistent / Insufficient data` from NDVI trend + change % + scene count — **no additionality, no scale band, no cross-asset check, no CO₂ gates**. Product dossiers hardcode cross-check `status` values of `met` / `on_track` (different vocabulary again) and a hand-authored `confidence.on_track_pct`. Additionality (a spec centerpiece, §8.1) is **absent** (grep → 0).
- **Gap:** The spec's cross-check logic and the headline confidence-blend are not implemented; product cross-checks are authored labels.

### 1.8 Evidence graph + orphan validation
- **Spec (§1.1, §3.4, §4.3):** a per-asset provenance **graph** (`evidence_graph: {nodes, edges}`) with `validate_graph`/`graph_builder.py` that **fails on any orphan number**; every value traces to the disclosure root; `orphans: []` in the bundle.
- **Today:** No `evidence/graph_schema.py` or `graph_builder.py`. The product implements a **lighter** traceability model: each fixture item carries a `trace` object (`source/date/method/confidence/traces_to`), surfaced in the UI as `TraceChip`. There is no nodes/edges graph and no orphan validator.
- **Gap:** The anti-orphan invariant and graph structure are missing; the product's per-item `traces_to` is a reasonable but non-equivalent substitute.

### 1.9 Legal / financial cross-reference connectors
- **Spec (§5.3, §6.7):** BOE (permits), EIB (financing), CENDOJ (court), OpenCorporates (ownership), IFC disclosures; link on entity+region (rapidfuzz ≥0.6); `legal_financial_risk` with confidence penalties (×0.5 high / ×0.8 medium). Núñez's **HIGH legal risk (court order)** is a spec highlight (§10.1).
- **Today:** No `cross_reference/` package; grep of dossiers for `boe`/`eib`/`cendoj`/`opencorporates`/`legal` → **0**. The Núñez court-order narrative does not exist (Núñez itself is absent — see §4).
- **Gap:** Entire legal/financial dimension absent from both pipeline and product.

### 1.10 Map outputs (rasters)
- **Spec (§3.1):** `map_outputs: {rgb_composite_url, ndvi_raster_url, change_map_url, aoi_geojson_url}`.
- **Today:** Product serves `before_rgb.png`, `after_rgb.png`, `change_overlay.png` via `/projects/{id}/imagery`. The `change_overlay.png` is a **761-byte solid-color placeholder, byte-identical across all three assets** (same md5). No NDVI raster; no real change map. (`canopy_pipeline/export/raster_export.py` can emit GEE tiles but is unwired.)
- **Gap:** No real NDVI/change rasters; the change overlay is a shared placeholder.

---

## 2. Delivered but not expected / divergent

Things this repo does that the spec didn't ask for, or does differently.

- **Different demo assets (major divergence).** Spec §10 designates **Núñez de Balboa** + **Francisco Pizarro** (Spanish solar) as the two assets "fully run through the current pipeline," and §10.3 explicitly labels **Nur Navoi + Mikoko Pamoja** as *"historical … not re-run this cycle."* The product ships **exactly those two historical assets** (`seed_data/projects/{nur_navoi_solar,mikoko_pamoja}.json`; `frontend/src/lib/config.ts` → `PRIMARY_PROJECT_ID = "nur_navoi_solar"`) and has **no Núñez dossier at all**. This was a deliberate product decision: `docs/specs/2026-07-17-canopy-source-pack-assets-design.md` *removed* Pizarro and adopted a "source pack" of Nur Navoi + Mikoko. Net effect: **product and spec demo on different assets**, so the spec's worked examples (§10) cannot be reproduced in the UI.
- **Orphan Pizarro imagery.** `seed_data/assets/pizarro/` still holds three PNGs (before/after byte-identical, placeholder overlay) but there is **no `pizarro.json` project** and it is not git-tracked (only the two JSON fixtures are). The 2026-07-17 design intended to delete these; they are leftover cruft.
- **A real, evidence-grounded LLM layer (net-positive, spec-consistent).** `backend/app/agent/` implements a genuine OpenAI-compatible client (`client.py`), a strict grounding system prompt (`prompts.py` — "Answer only from the supplied project evidence … cite the evidence IDs"), DB-backed retrieval (`retrieval.py` builds context from confidence/observations/cross-checks/evidence), structured Ask output + Memo generation, and QA/Report logging. This is **more than the spec asked of the engine** (spec §1.1 only says a presentation LLM "may present pre-computed, sourced values") and is architecturally **consistent** with the spec's "LLM never scores/reads a pixel" principle. It degrades gracefully when `LLM_API_KEY` is unset (`LLMNotConfigured` → `LlmUnavailable` UI).
- **Normalized Postgres dossier schema.** The product persists the dossier into typed tables (`backend/app/models/{project,dossier,observation,methodology,report}.py`, seeded by `scripts/seed.py`) and serves it via `GET /projects/{id}/dossier` (`backend/app/schemas/project.py::Dossier`). The spec treats the engine as synchronous/dict-based (§2.1) and leaves the async/DB wrapper to Cem — so this is the expected Cem-owned layer, but its **schema differs from the spec's `verify_and_report` bundle** (§3.4) — see §5.
- **Richer frontend narrative than the spec sketches.** `frontend/src/app/projects/[id]/` ships dedicated screens: `locate`, `timeline`, `crosscheck`, `confidence`, `ask`, `memo`, plus a `portfolio` list — a linear disclosure→confidence narrative (per the 2026-07-13 direction doc) that the spec does not prescribe.
- **Vocabulary drift.** Product cross-check statuses are `met` / `on_track`; spec verdicts are `consistent` / `partially_consistent` / `inconsistent` / `insufficient_data`. Product imagery is labeled Esri; spec assumes Sentinel-2.

---

## 3. Stubbed vs real — pipeline-stage inventory

| Stage (spec §1.3) | Real computation? | Where / evidence |
|---|---|---|
| Validate + route (taxonomy veg/built) | **Partial-real** (pipeline only) | `canopy_pipeline/input/request_validator.py`, `analytics/screening.is_vegetation` (3-asset list, not full taxonomy). No `taxonomy.py`. Unwired to product. |
| Locate (Path B: resolve + footprint) | **Stub** | Product: `localization.method = "…(precomputed, stub — no ML this sprint)"`. No matching code exists. |
| Compose imagery (S2 composites, S1) | **Real but unwired** (pipeline); **stub** (product) | Pipeline `data/sentinel2_loader.py` / `sentinel1_loader.py` are real GEE. Product uses single Esri PNG reused as before==after. |
| Indices (NDVI/NDWI/NBR) | **Real but unwired** (pipeline); **authored** (product) | `canopy_pipeline/indices/*`. Dossier NDVI = hand floats; NDWI/NBR absent. |
| Change & trajectory (ΔNDVI, slope) | **Partial** (pipeline ΔNDVI real; no slope); **stub** (product) | Pipeline `analytics/change_detection.py`. No `timeseries.py`/slope. Dossier `ndvi_change_v1 (stub)`. |
| Carbon / permanence | **Proxy** (pipeline, NDVI→biomass, not ESA CCI); **stub** (product) | `analytics/carbon_model.py`. No `permanence.py`. Dossier `carbon_ar_acm0003 (stub)`. |
| Build detect / date (SAR, NDVI collapse) | **Missing** | No build-year detection anywhere; grep `build_year`/`backscatter` → 0. |
| Hazards (fire/flood/degradation) | **Simplified** (pipeline); **absent** (product) | `analytics/risk_scoring.py` (NBR+SAR proxy, not Fosberg/Aqueduct). No `fire.py`/`flood.py`. Dossier: single authored `risk_score`. |
| Generation (PVWatts + avoided) | **Missing** | No PVWatts/ERA5/grid-factor code. Dossier `generation_proxy_v1 (stub)`. |
| Cross-check (verdicts, cross-asset CO₂) | **Missing** (spec logic); **authored** (product) | No `cross_check.py`/additionality/cross-asset. Dossier statuses hand-set (`met`/`on_track`). |
| Assemble (JSON + evidence graph + tables) | **Partial** | Pipeline `export/json_export.py` (real, Path-A shape). No `evidence/graph_builder.py`, no `export/tables.py`, no orphan validation. Product assembles from fixtures. |
| **LLM Ask / Memo (presentation)** | **REAL** | `backend/app/agent/*` — genuine grounded LLM, requires `LLM_API_KEY`. |
| **Backend API + persistence** | **REAL** | `backend/app/api/routes/*`, `models/*`, `scripts/seed.py`. |
| **Frontend product** | **REAL** | `frontend/src/app/*`, `components/*`. |

**Summary:** the *product plumbing* (API, DB, LLM, UI) is real; the *science* is either an unwired simplified pipeline or a hand-authored fixture. Every dossier `method` field advertises `(stub)`.

---

## 4. Data gaps (concrete)

1. **Before == After imagery.** `before_rgb.png` and `after_rgb.png` are byte-identical (md5-verified) for **all three** asset folders. Root cause: `scripts/seed.py::ensure_assets` fetches one Esri image and assigns it to every `*_rgb.png`. The UI's timeline/before-after therefore shows the same pixels twice.
2. **Single timestamp masquerading as a time series.** `observation_series` claims 3 dated snapshots each (e.g. Nur Navoi `2019-04 / 2021-03 / 2021-09` with NDVI `0.22→0.14→0.11`, footprint `0→180→238 ha`) but maps them to only **2 image_keys** (`before_rgb`, `after_rgb`) — which are identical anyway. The dates, NDVI values, and footprint areas are hand-authored, not measured.
3. **Placeholder change overlay.** `change_overlay.png` is a **761-byte solid-color PNG, identical across all assets** (shared md5). No real change map exists (`_solid_png` fallback in `seed.py`).
4. **Every `method` exposes `(stub)`.** In `seed_data/projects/*.json`: `document_extraction (stub)`, `manual_precomputed_v1`, `aoi_snapshot_v1 (stub)`, `ndvi_composite_v1 (stub)`, `ndvi_change_v1 (stub)`, `footprint_density_v1 (stub)`, `generation_proxy_v1 (stub)`, `carbon_ar_acm0003 (stub)`, `confidence_composite_v1 (stub)`. These strings flow into the DB (`methodology`/`trace`) and are visible to the LLM context and potentially the UI.
5. **Imagery mislabeled as Sentinel.** Dossier `trace.source` says `"Sentinel-2 + Sentinel-1"` for snapshots that are actually a single Esri World Imagery frame. The 2026-07-13 direction doc's P3 task ("relabel imagery source accurately (Esri, not Sentinel-2)") appears not fully done in the fixtures.
6. **Núñez de Balboa entirely absent.** The spec's primary worked example (§10.1, the CO₂ over-reporting + court-order case) has no dossier, no imagery, no claims. Pizarro has orphan imagery but no dossier.
7. **Confidence / risk numbers are opaque authored constants.** `confidence.on_track_pct` (85 / …), `risk_score` (22), `risk_band` (Low) are hardcoded in the fixtures with no computation behind them, despite the spec defining exact formulas (§6.5).
8. **No physical-hazard, generation, carbon-band, legal, or cross-asset data** in any dossier (grep-confirmed zeros in §1).

---

## 5. Priority-ranked fix list for the next session

Effort key: **S** ≈ <½ day · **M** ≈ 1–2 days · **L** ≈ 3+ days / needs external delivery. Dependencies called out inline.

> Strategic note: the deepest gap (Luna's whole engine unintegrated) is only closable when Luna delivers `verify_and_report()`. Until then, the highest-value work is (a) making the *stub honest and demo-safe*, and (b) *building the seam* so Luna's bundle drops in cleanly. Rank accordingly.

**P0 — Truth & demo-safety (do first; cheap, high-trust-impact)**
1. **Fix before==after imagery.** *(M, no deps)* Either fetch two genuinely different frames (real dated Sentinel-2 via the unwired `canopy_pipeline` once GEE creds exist — see P3), or, until then, visibly flag in the UI that before/after is the same Esri stand-in. At minimum stop presenting identical pixels as change. Touch: `scripts/seed.py::ensure_assets`, `frontend` timeline/before-after.
2. **Replace the placeholder `change_overlay.png`.** *(S–M)* Generate a real (even coarse) per-asset ΔNDVI overlay, or remove the change-map visual and label it "not yet computed." Touch: `scripts/seed.py`, `EvidenceMap`/timeline.
3. **Purge `(stub)` from user/LLM-facing strings; relabel imagery as Esri.** *(S)* Move the "(stub)" honesty into a single machine-readable `assurance`/`is_stub` flag rather than baking it into `method`/`source` text that the LLM ingests and the UI may render. Complete the 2026-07-13 P3 relabel. Touch: `seed_data/projects/*.json`, `scripts/seed.py`, dossier schema.
4. **Delete orphan Pizarro assets** (or add a real Pizarro dossier — see P2). *(S)* Touch: `seed_data/assets/pizarro/`.

**P1 — Align the seam to Luna's bundle (unblocks integration)**
5. **Reconcile the product Dossier schema with the spec `verify_and_report` bundle (§3.4).** *(M)* The product serves `disclosure/claims/localization/observation_series/cross_check/confidence` with per-item `trace`; the spec bundle is `assets[].{resolution{match_score,margin,gem_location_id,centroid}, aoi{assurance,observed_area_ha}, cross_check[{claim,reported,observed,delta,verdict,assurance_label}], physical_risk, cross_reference[], legal_financial_risk, evidence_graph{nodes,edges}, orphans[]}` + `cross_asset_co2`. Decide adapter-vs-adopt and write a mapping. Dep: coordinate with Luna. Touch: `backend/app/schemas/project.py`, `services/projects.py`, `scripts/seed.py`.
6. **Standardize verdict vocabulary** to the spec's `consistent/partially_consistent/inconsistent/insufficient_data` (replace `met`/`on_track`). *(S)* Touch: fixtures + `schemas` + frontend `crosscheck` page + LLM retrieval text.
7. **Add an ingestion path that consumes Luna's `verify_and_report()` output** into the DB in place of the hand-authored fixtures. *(M)* This is the "Luna's schema replaces the fixture reads later" hook the 2026-07-13 doc anticipated. Dep: Luna's bundle format frozen.

**P2 — Content parity with the spec's story**
8. **Decide the demo-asset question: Núñez/Pizarro (spec) vs Nur Navoi/Mikoko (current).** *(M, product-owner call)* If the demo must match Luna's §10 worked examples (CO₂ over-reporting, court order, cross-asset divergence), author Núñez + Pizarro dossiers; otherwise document the deliberate divergence so the two teams stop drifting. Dep: Luna coordination (memory notes a held PR pending this).
9. **Represent the missing dimensions in the dossier** even if still stubbed: physical-risk hazards (fire/flood), generation/avoided-emissions, carbon band, and — for the Núñez story — legal/financial risk + cross-asset CO₂. *(M)* Gives the UI real fields to bind and a place for Luna's numbers to land.

**P3 — Wire / upgrade the real engine (largest, external deps)**
10. **Bring up the real `canopy_pipeline` Path A** (it exists and is real GEE) behind a backend job, so at least one asset shows genuinely computed NDVI/change/risk. *(L; needs **GEE credentials** — `ee.Authenticate/Initialize` in `canopy_pipeline/session.py`)*. Note this repo's pipeline is simpler than spec (NDVI-proxy carbon, NBR fire, SAR flood) — treat as bridge, not final.
11. **Integrate Luna's full v0.3 pipeline** (Path B matching, ESA CCI carbon, Fosberg/Aqueduct hazards, PVWatts, cross-check + confidence blend, evidence graph + orphan validation, legal/financial connectors). *(L; **blocked on Luna's delivery** + optional flags: `CANOPY_LIVE_CONNECTORS`, `OPENCORPORATES_API_TOKEN`, `CANOPY_NATURE_LIVE`)*. This closes §1.1–§1.9 in one integration once her code lands.
12. **Enable the LLM at runtime for the demo.** *(S; needs an **LLM key** — `LLM_API_KEY`/`LLM_BASE_URL`/`LLM_MODEL` in `backend/.env`)*. The Ask/Memo layer is real and ready; it just needs credentials to be live in the demo.

**Not gaps (spec-acknowledged FUTURE — do not chase):** Catastro/PNOA footprints, Landsat pre-2017 additionality, the second localization path (image classification, Abhinav) + IoU backtest, scheduled alerts/monitor, DEM flood modelling, gap-polygon cut-outs, CENDOJ live API (spec §1.4).

---

### Appendix — key file references
- Spec: `/Users/cemkilinc/Desktop/Canopy_Pipeline_Spec_hackathon.docx`
- Unwired pipeline: `canopy_pipeline/run_pipeline.py` (96 LoC), `analytics/{carbon_model,change_detection,risk_scoring,screening}.py`, `data/{sentinel2_loader,sentinel1_loader}.py`, `indices/{ndvi,ndwi,nbr}.py`, `session.py` (GEE init).
- Product fixtures: `seed_data/projects/{nur_navoi_solar,mikoko_pamoja}.json`; assets `seed_data/assets/*/` (before==after; placeholder overlay).
- Seeder: `scripts/seed.py` (`ensure_assets`, `fetch_aoi_imagery`, `_solid_png`, `_placeholder_color`).
- Backend: `backend/app/api/routes/{projects,agent,evidence}.py`, `schemas/project.py` (`Dossier`), `models/*`, `agent/{client,agent,prompts,retrieval}.py`, `core/config.py` (LLM settings).
- Frontend: `frontend/src/app/projects/[id]/{locate,timeline,crosscheck,confidence,ask,memo}/page.tsx`, `lib/config.ts` (`PRIMARY_PROJECT_ID`).
- Team framing: `docs/specs/2026-07-13-canopy-disclosure-direction.md`, `docs/specs/2026-07-17-canopy-source-pack-assets-design.md`.
