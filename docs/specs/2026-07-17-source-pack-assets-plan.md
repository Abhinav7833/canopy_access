# Source-Pack Demo Assets Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace the demo's two mock assets with the source-pack pair — Nur Navoi Solar (self-reporting-gap narrative) and Mikoko Pamoja (mangrove blue-carbon) — and render each per its `asset_type`.

**Architecture:** `asset_type` (already a column, already served) is the discriminator. Dossier fixtures carry the metric data; a new frontend `assetType` config owns per-type labels and the Observe-tab framing (Approach A). Backend code is unchanged except tests; all narrative content is in JSON fixtures.

**Tech Stack:** FastAPI + SQLAlchemy + PostGIS (backend), Next.js 16 + React + TanStack Query (frontend), pytest / vitest.

## Global Constraints

- Spec: `docs/specs/2026-07-17-canopy-source-pack-assets-design.md`.
- Dossier fixtures live at `seed_data/projects/<id>.dossier.json`; project seed fixtures at `seed_data/projects/<file>.json` (seed reads `analysis_id` as the project id).
- Claim `kind` and cross-check `status` are free-form strings — no type/schema changes needed.
- Imagery stays placeholder/Esri-fetched via `seed.py`; keys are `before_rgb.png` / `after_rgb.png` / `change_overlay.png`. Real dated rasters are out of scope (data-population task).
- Coordinates are `[lon, lat]` pairs everywhere (`aoi_coords`, `located_centroid`).
- **Commit gate:** commits touching `.py/.ts/.tsx` go through the standing `/simplify` + `/code-review` gate (see `canopy-precommit-review-gate`): stage, run the passes, `git write-tree > .git/canopy-review-marker`, then commit (add + commit as separate steps). **JSON/MD-only commits pass the gate freely.** When executing inline, batching all code changes into one gated commit at the end is acceptable.
- Backend gate (hook runs): `uv run ruff check .`, `uv run ruff format --check .`, `uv run mypy app`, `uv run pytest -q`. Frontend gate: `./node_modules/.bin/eslint .`, `./node_modules/.bin/tsc --noEmit`, `npx vitest run`.
- DB is live PostGIS on `localhost:5433` (no Docker). Backend runs on `:8001`, frontend on `:3000`.

---

### Task 1: Rework the Nur Navoi fixtures (self-reporting-gap narrative)

**Files:**
- Modify: `seed_data/projects/nur_navoi.json` (project seed row + summary)
- Modify: `seed_data/projects/nur_navoi_solar.dossier.json` (the narrative)

**Interfaces:**
- Produces: project id `nur_navoi_solar`, `asset_type: "solar"`, evidence id `nur_navoi_solar_ev_0`, claim kinds `capacity_mw` / `generation_gwh` / `co2_avoided_tpy` / `area_ha` / `cod_date`.

- [ ] **Step 1: Rewrite `seed_data/projects/nur_navoi.json`** (keep the existing AOI polygon — its centroid ≈ 64.986°E/40.11°N matches the pack's map link):

```json
{
  "analysis_id": "nur_navoi_solar",
  "project_name": "Nur Navoi Solar (100 MW), Uzbekistan",
  "asset_type": "solar",
  "country": "Uzbekistan",
  "financing_type": "development_finance",
  "monitoring_objective": "Independently verify build-out and operation vs the self-reported green/SDG-bond impact figures.",
  "aoi_coords": [[64.978, 40.104], [64.994, 40.104], [64.994, 40.120], [64.978, 40.120], [64.978, 40.104]],
  "summary": {
    "screening_status": "Consistent",
    "risk_score": 22, "risk_band": "Low", "confidence": 0.85,
    "change_detected": true, "human_review_recommended": false,
    "main_finding": "Independent satellite confirms the 100 MW plant was built at the self-reported scale and is operating since Aug 2021 — turning a self-reported figure into observed evidence; generation remains a proxy, not metered."
  },
  "metrics": {
    "vegetation_change_percent": 41.0, "flood_risk_score": 22, "fire_risk_score": 12,
    "deforestation_detected": false
  },
  "evidence": [
    {
      "observation_type": "land_cover_change",
      "summary": "Full panel-field build-out and operation confirmed against the self-reported 100 MW / 240 ha figures.",
      "metric": {"name": "vegetation_change_percent", "value": 41.0,
                 "baseline_period": "2019-06", "comparison_period": "2021-09"},
      "source": {"name": "Sentinel-2 + Sentinel-1", "resolution": "10 m",
                 "processing": "median composite; SAR water layer"},
      "method": "bi-temporal change + SAR flood proxy (method_id: build_v1)",
      "confidence": "high",
      "financial_relevance": "Independent build/operation evidence turning self-reported bond impact figures into observed proof.",
      "limitations": ["confirms build/land-cover change, not metered generation",
                      "generation/carbon is a proxy, needs ground truth to certify",
                      "no independent metering in the demo"],
      "supporting_assets": ["before_rgb.png", "after_rgb.png", "change_overlay.png"]
    }
  ],
  "map_outputs": {"rgb_composite_url": "before_rgb.png"},
  "metadata": {"date_range": {"start": "2019-06-01", "end": "2021-09-30"},
               "aoi_area_hectares": 231.4}
}
```

- [ ] **Step 2: Rewrite `seed_data/projects/nur_navoi_solar.dossier.json`:**

```json
{
  "project_id": "nur_navoi_solar",
  "disclosure": {
    "title": "Nur Navoi Solar (100 MW) — SDG/Green Bond Allocation & Impact (self-reported)",
    "issuer": "Republic of Uzbekistan (Ministry of Finance) / Masdar",
    "instrument": "Sovereign SDG bond (2021, $235m, LSE) — self-reported use-of-proceeds allocation & impact",
    "financing_date": "2020-12-01",
    "doc_ref": "uzbekistan_sdg_bond_allocation_impact_2023.pdf",
    "region_hint": "Navoi region, Uzbekistan",
    "summary": "Allocation and impact figures for a 100 MW solar IPP are self-reported by the issuer and sponsor, checked only by a document-based 'limited assurance' review. There is no independent, physical verification that what was financed was actually built, on schedule, at the claimed scale, and is operating.",
    "trace": {"source": "uzbekistan_sdg_bond_allocation_impact_2023.pdf", "date": "2023-12-01", "method": "document_extraction (stub)", "confidence": "medium", "traces_to": "disclosure"}
  },
  "claims": [
    {"id": "claim_capacity_mw", "kind": "capacity_mw", "promised": 100, "unit": "MW",
     "source_span": "\"...a 100 MW nameplate solar photovoltaic plant...\"",
     "trace": {"source": "uzbekistan_sdg_bond_allocation_impact_2023.pdf", "date": "2023-12-01", "method": "document_extraction (stub)", "confidence": "high", "traces_to": "disclosure"}},
    {"id": "claim_generation_gwh", "kind": "generation_gwh", "promised": 270, "unit": "GWh/yr",
     "source_span": "\"...expected to generate approximately 270 GWh per year...\"",
     "trace": {"source": "uzbekistan_sdg_bond_allocation_impact_2023.pdf", "date": "2023-12-01", "method": "document_extraction (stub)", "confidence": "medium", "traces_to": "disclosure"}},
    {"id": "claim_co2_avoided", "kind": "co2_avoided_tpy", "promised": 153000, "unit": "tCO₂/yr",
     "source_span": "\"...avoiding around 153,000 tonnes of CO2 annually...\"",
     "trace": {"source": "uzbekistan_sdg_bond_allocation_impact_2023.pdf", "date": "2023-12-01", "method": "document_extraction (stub)", "confidence": "low", "traces_to": "disclosure"}},
    {"id": "claim_area_ha", "kind": "area_ha", "promised": 240, "unit": "ha",
     "source_span": "\"...a panel field of roughly 240 hectares in the Navoi region...\"",
     "trace": {"source": "uzbekistan_sdg_bond_allocation_impact_2023.pdf", "date": "2023-12-01", "method": "document_extraction (stub)", "confidence": "medium", "traces_to": "disclosure"}},
    {"id": "claim_cod_date", "kind": "cod_date", "promised": "2021-08-01", "unit": "date",
     "source_span": "\"...commercial operation achieved in August 2021...\"",
     "trace": {"source": "uzbekistan_sdg_bond_allocation_impact_2023.pdf", "date": "2023-12-01", "method": "document_extraction (stub)", "confidence": "medium", "traces_to": "disclosure"}}
  ],
  "localization": {
    "region_hint": "Navoi region, Uzbekistan",
    "located_centroid": [64.986, 40.112],
    "aoi_ref": "nur_navoi_solar",
    "confidence": 0.9,
    "method": "region_hint + ADB/World Bank site map matched against the Sentinel-2 panel field (precomputed, stub — no ML this sprint)",
    "alternatives_rejected": [
      {"name": "Sherabad Solar (456.7 MW)", "reason": "different, larger site in Surxondaryo with separate financing"},
      {"name": "Samarkand Solar", "reason": "different region than the disclosed Navoi site"}
    ],
    "trace": {"source": "region_hint + ADB/WB site map (stub)", "date": "2026-07-17", "method": "manual_precomputed_v1", "confidence": "medium", "traces_to": "disclosure"}
  },
  "observation_series": [
    {"date": "2019-06-15", "image_key": "before_rgb.png", "footprint_ha": 0, "ndvi": 0.18,
     "note": "Pre-construction baseline — desert scrub, no panel structures visible.",
     "trace": {"source": "Esri World Imagery (Sentinel-2 stand-in)", "date": "2019-06-15", "method": "aoi_snapshot_v1 (stub)", "confidence": "medium", "traces_to": "claim_area_ha"}},
    {"date": "2020-09-20", "image_key": "after_rgb.png", "footprint_ha": 150, "ndvi": 0.12,
     "note": "Construction underway; panel rows across roughly two-thirds of the field. Image reused from the single fetched snapshot (stub — not a true dated capture).",
     "trace": {"source": "Esri World Imagery (Sentinel-2 stand-in)", "date": "2020-09-20", "method": "aoi_snapshot_v1 (stub)", "confidence": "low", "traces_to": "claim_area_ha"}},
    {"date": "2021-09-30", "image_key": "after_rgb.png", "footprint_ha": 240, "ndvi": 0.10,
     "note": "Full panel field in place and operating, consistent with Aug 2021 commissioning. Image reused from the single fetched snapshot (stub — not a true dated capture).",
     "trace": {"source": "Esri World Imagery (Sentinel-2 stand-in)", "date": "2021-09-30", "method": "aoi_snapshot_v1 (stub)", "confidence": "medium", "traces_to": "claim_area_ha"}}
  ],
  "cross_check": [
    {"claim_id": "claim_area_ha", "observed": 240, "status": "met", "variance": "0% vs self-reported 240 ha",
     "evidence_ids": ["nur_navoi_solar_ev_0"],
     "trace": {"source": "observation_series[2] + evidence nur_navoi_solar_ev_0", "date": "2021-09-30", "method": "footprint_density_v1 (stub)", "confidence": "medium", "traces_to": "claim_area_ha"}},
    {"claim_id": "claim_cod_date", "observed": "2021-08 (operational per imagery)", "status": "met", "variance": "on schedule",
     "evidence_ids": ["nur_navoi_solar_ev_0"],
     "trace": {"source": "observation_series[2] + evidence nur_navoi_solar_ev_0", "date": "2021-09-30", "method": "footprint_density_v1 (stub)", "confidence": "medium", "traces_to": "claim_cod_date"}},
    {"claim_id": "claim_generation_gwh", "observed": "Footprint + operating status consistent with the ~270 GWh/yr self-report", "status": "on_track", "variance": "consistent (proxy, not metered)",
     "evidence_ids": ["nur_navoi_solar_ev_0"],
     "trace": {"source": "observation_series[2] + evidence nur_navoi_solar_ev_0", "date": "2021-09-30", "method": "generation_proxy_v1 (stub)", "confidence": "low", "traces_to": "claim_generation_gwh"}}
  ],
  "confidence": {
    "on_track_pct": 85,
    "rationale": "Independent satellite confirms the plant was built at the self-reported scale and is operating on schedule — turning a self-reported figure into observed evidence. Generation is a consistent proxy, not independent metering.",
    "drivers": [
      "Full 240 ha panel field matches the self-reported build",
      "On-time commissioning (Aug 2021) independently confirmed",
      "Footprint and operation consistent with the ~270 GWh/yr self-report",
      "Generation and finer impact claims not independently metered — need ground truth"
    ],
    "risk_score": 22,
    "risk_band": "Low",
    "trace": {"source": "cross_check[] aggregate", "date": "2021-09-30", "method": "confidence_composite_v1 (stub)", "confidence": "medium", "traces_to": "disclosure"}
  },
  "memo_ready": true
}
```

- [ ] **Step 3: Validate both JSON files parse:**

Run: `node -e "require('./seed_data/projects/nur_navoi.json'); require('./seed_data/projects/nur_navoi_solar.dossier.json'); console.log('ok')"`
Expected: `ok`

- [ ] **Step 4: Commit (JSON-only — gate passes freely):**

```bash
git add seed_data/projects/nur_navoi.json seed_data/projects/nur_navoi_solar.dossier.json
git commit -m "data: rework Nur Navoi fixtures to the self-reporting-gap narrative"
```

---

### Task 2: Create the Mikoko Pamoja fixtures (mangrove blue-carbon)

**Files:**
- Create: `seed_data/projects/mikoko_pamoja.json`
- Create: `seed_data/projects/mikoko_pamoja.dossier.json`

**Interfaces:**
- Produces: project id `mikoko_pamoja`, `asset_type: "mangrove"`, evidence id `mikoko_pamoja_ev_0`, claim kinds `protected_ha` / `restored_ha` / `credits_tco2` / `community_usd`.

- [ ] **Step 1: Create `seed_data/projects/mikoko_pamoja.json`:**

```json
{
  "analysis_id": "mikoko_pamoja",
  "project_name": "Mikoko Pamoja Mangrove (Gazi Bay), Kenya",
  "asset_type": "mangrove",
  "country": "Kenya",
  "financing_type": "carbon_finance",
  "monitoring_objective": "Verify protection, restoration, and permanence vs the Plan Vivo-certified carbon-credit claims.",
  "aoi_coords": [[39.492, -4.425], [39.508, -4.425], [39.508, -4.415], [39.492, -4.415], [39.492, -4.425]],
  "summary": {
    "screening_status": "Consistent",
    "risk_score": 15, "risk_band": "Low", "confidence": 0.90,
    "change_detected": true, "human_review_recommended": false,
    "main_finding": "Mangrove protected with no deforestation and canopy stable-to-expanding — consistent with the certified 117 ha protected + ~10 ha restored and the credits issued."
  },
  "metrics": {
    "vegetation_change_percent": 6.2, "flood_risk_score": 20, "fire_risk_score": 8,
    "deforestation_detected": false
  },
  "evidence": [
    {
      "observation_type": "mangrove_protection_growth",
      "summary": "No deforestation across the protected block; NDVI stable-to-rising indicates canopy growth consistent with the certified restoration.",
      "metric": {"name": "ndvi_change_percent", "value": 6.2,
                 "baseline_period": "2016", "comparison_period": "2024"},
      "source": {"name": "Sentinel-2 + Sentinel-1", "resolution": "10 m",
                 "processing": "annual NDVI/NDWI composites; SAR coastal context"},
      "method": "NDVI/NDWI change + change detection (method_id: ndvi_change_v1)",
      "confidence": "high",
      "financial_relevance": "Protection + growth evidence relevant to blue-carbon credit permanence and issuance.",
      "limitations": ["confirms canopy/land-cover change, not per-tree biomass",
                      "carbon is a proxy, not MRV-grade metering",
                      "finer species/impact claims need ground truth"],
      "supporting_assets": ["before_rgb.png", "after_rgb.png", "change_overlay.png"]
    }
  ],
  "map_outputs": {"rgb_composite_url": "before_rgb.png"},
  "metadata": {"date_range": {"start": "2016-01-01", "end": "2024-12-31"},
               "aoi_area_hectares": 198.7}
}
```

- [ ] **Step 2: Create `seed_data/projects/mikoko_pamoja.dossier.json`:**

```json
{
  "project_id": "mikoko_pamoja",
  "disclosure": {
    "title": "Mikoko Pamoja — Plan Vivo Blue-Carbon Project Design & Certification",
    "issuer": "Mikoko Pamoja Community Organisation (MPCO), coordinated by ACES",
    "instrument": "Plan Vivo-certified carbon credits (community-led blue carbon)",
    "financing_date": "2013-09-01",
    "doc_ref": "mikoko_pamoja_planvivo_pdd.pdf",
    "region_hint": "Gazi Bay, Kwale County, Kenya",
    "summary": "To be certified and funded, the community had to prove the hard part: that the mangrove is genuinely protected (no deforestation), that restoration is real, and that biomass is growing (permanence). Promised: 117 ha protected plus ~10 ha restored, with credits sold against verified growth.",
    "trace": {"source": "mikoko_pamoja_planvivo_pdd.pdf", "date": "2013-09-01", "method": "document_extraction (stub)", "confidence": "medium", "traces_to": "disclosure"}
  },
  "claims": [
    {"id": "claim_protected_ha", "kind": "protected_ha", "promised": 117, "unit": "ha",
     "source_span": "\"...117 hectares of mangrove forest under protection...\"",
     "trace": {"source": "mikoko_pamoja_planvivo_pdd.pdf", "date": "2013-09-01", "method": "document_extraction (stub)", "confidence": "high", "traces_to": "disclosure"}},
    {"id": "claim_restored_ha", "kind": "restored_ha", "promised": 10, "unit": "ha",
     "source_span": "\"...approximately 10 hectares under active restoration...\"",
     "trace": {"source": "mikoko_pamoja_planvivo_pdd.pdf", "date": "2013-09-01", "method": "document_extraction (stub)", "confidence": "medium", "traces_to": "disclosure"}},
    {"id": "claim_credits_tco2", "kind": "credits_tco2", "promised": 9880, "unit": "tCO₂",
     "source_span": "\"...around 9,880 tonnes CO2e of credits issued (2014-2018)...\"",
     "trace": {"source": "mikoko_pamoja_planvivo_pdd.pdf", "date": "2013-09-01", "method": "document_extraction (stub)", "confidence": "medium", "traces_to": "disclosure"}},
    {"id": "claim_community_usd", "kind": "community_usd", "promised": 58591, "unit": "USD",
     "source_span": "\"...about US$58,591 paid to the community...\"",
     "trace": {"source": "mikoko_pamoja_planvivo_pdd.pdf", "date": "2013-09-01", "method": "document_extraction (stub)", "confidence": "medium", "traces_to": "disclosure"}}
  ],
  "localization": {
    "region_hint": "Gazi Bay, Kwale County, Kenya",
    "located_centroid": [39.500, -4.420],
    "aoi_ref": "mikoko_pamoja",
    "confidence": 0.9,
    "method": "Plan Vivo project boundary matched against the Sentinel-2 mangrove extent at the tidal edge (NDWI-separated), precomputed stub",
    "alternatives_rejected": [
      {"name": "Gazi Bay seagrass beds", "reason": "seagrass/tidal flat signature, not the protected mangrove block"},
      {"name": "Makongeni mangroves (Gazi Bay east)", "reason": "adjacent stand outside the Mikoko Pamoja project boundary"}
    ],
    "trace": {"source": "Plan Vivo boundary + Sentinel-2 NDWI (stub)", "date": "2026-07-17", "method": "manual_precomputed_v1", "confidence": "medium", "traces_to": "disclosure"}
  },
  "observation_series": [
    {"date": "2016-07-01", "image_key": "before_rgb.png", "footprint_ha": 117, "ndvi": 0.61,
     "note": "Baseline mangrove extent — dense canopy across the protected block; no clearing.",
     "trace": {"source": "Esri World Imagery (Sentinel-2 stand-in)", "date": "2016-07-01", "method": "aoi_snapshot_v1 (stub)", "confidence": "medium", "traces_to": "claim_protected_ha"}},
    {"date": "2020-07-01", "image_key": "after_rgb.png", "footprint_ha": 122, "ndvi": 0.66,
     "note": "Canopy stable-to-expanding; the restored fringe is filling in. Image reused from the single fetched snapshot (stub — not a true dated capture).",
     "trace": {"source": "Esri World Imagery (Sentinel-2 stand-in)", "date": "2020-07-01", "method": "aoi_snapshot_v1 (stub)", "confidence": "low", "traces_to": "claim_restored_ha"}},
    {"date": "2024-07-01", "image_key": "after_rgb.png", "footprint_ha": 127, "ndvi": 0.69,
     "note": "No deforestation over the window; canopy denser and the restored area established. Image reused from the single fetched snapshot (stub — not a true dated capture).",
     "trace": {"source": "Esri World Imagery (Sentinel-2 stand-in)", "date": "2024-07-01", "method": "aoi_snapshot_v1 (stub)", "confidence": "medium", "traces_to": "claim_protected_ha"}}
  ],
  "cross_check": [
    {"claim_id": "claim_protected_ha", "observed": "≈0% canopy loss vs the ~2.7%/yr regional deforestation baseline", "status": "met", "variance": "no loss detected",
     "evidence_ids": ["mikoko_pamoja_ev_0"],
     "trace": {"source": "observation_series + evidence mikoko_pamoja_ev_0", "date": "2024-07-01", "method": "change_detection_v1 (stub)", "confidence": "high", "traces_to": "claim_protected_ha"}},
    {"claim_id": "claim_restored_ha", "observed": "~10 ha canopy gain on the restored fringe confirmed", "status": "met", "variance": "consistent with ~10 ha restored",
     "evidence_ids": ["mikoko_pamoja_ev_0"],
     "trace": {"source": "observation_series + evidence mikoko_pamoja_ev_0", "date": "2024-07-01", "method": "ndvi_change_v1 (stub)", "confidence": "medium", "traces_to": "claim_restored_ha"}},
    {"claim_id": "claim_credits_tco2", "observed": "NDVI-derived biomass growth consistent with the 9,880 tCO₂ issued", "status": "on_track", "variance": "consistent (proxy, not MRV-grade)",
     "evidence_ids": ["mikoko_pamoja_ev_0"],
     "trace": {"source": "observation_series + evidence mikoko_pamoja_ev_0", "date": "2024-07-01", "method": "carbon_ar_acm0003 (stub)", "confidence": "low", "traces_to": "claim_credits_tco2"}}
  ],
  "confidence": {
    "on_track_pct": 90,
    "rationale": "Protection and restoration are independently corroborated: no deforestation against a ~2.7%/yr regional baseline, canopy stable-to-expanding on NDVI, and a carbon proxy consistent with the credits issued. Permanence risk is low.",
    "drivers": [
      "No deforestation vs the ~2.7%/yr regional baseline (permanence)",
      "Canopy stable-to-expanding on NDVI (biomass growth)",
      "Carbon proxy consistent with the 9,880 tCO₂ credits issued",
      "Finer species/impact claims need ground truth"
    ],
    "risk_score": 15,
    "risk_band": "Low",
    "trace": {"source": "cross_check[] aggregate", "date": "2024-07-01", "method": "confidence_composite_v1 (stub)", "confidence": "medium", "traces_to": "disclosure"}
  },
  "memo_ready": true
}
```

- [ ] **Step 2b: Validate both JSON files parse:**

Run: `node -e "require('./seed_data/projects/mikoko_pamoja.json'); require('./seed_data/projects/mikoko_pamoja.dossier.json'); console.log('ok')"`
Expected: `ok`

- [ ] **Step 3: Commit (JSON-only — gate passes freely):**

```bash
git add seed_data/projects/mikoko_pamoja.json seed_data/projects/mikoko_pamoja.dossier.json
git commit -m "data: add Mikoko Pamoja mangrove blue-carbon fixtures"
```

---

### Task 3: Remove Pizarro, reseed the DB, update backend tests

**Files:**
- Delete: `seed_data/projects/pizarro.json`, `seed_data/projects/pizarro.dossier.json`
- Modify: `backend/tests/test_projects_api.py`

**Interfaces:**
- Consumes: the `seed` fixture callable `seed(name="nur_navoi")` (reads `<name>.json`, returns the project id). The `client` fixture. `get_settings()` from `app.core.config`.

- [ ] **Step 1: Delete the Pizarro fixtures:**

```bash
git rm seed_data/projects/pizarro.json seed_data/projects/pizarro.dossier.json
```

- [ ] **Step 2: Remove Pizarro from the live DB (dependency order):**

```bash
PGPASSWORD=canopy psql -h localhost -p 5433 -U canopy -d canopy <<'SQL'
DELETE FROM metrics WHERE observation_id IN (SELECT id FROM observations WHERE project_id='pizarro');
DELETE FROM evidence_items WHERE observation_id IN (SELECT id FROM observations WHERE project_id='pizarro');
DELETE FROM observations WHERE project_id='pizarro';
DELETE FROM risk_scores WHERE project_id='pizarro';
DELETE FROM project_boundaries WHERE project_id='pizarro';
DELETE FROM qa_logs WHERE project_id='pizarro';
DELETE FROM reports WHERE project_id='pizarro';
DELETE FROM projects WHERE id='pizarro';
SQL
```

- [ ] **Step 3: Reseed the two assets (from `backend/`, using the seed script):**

```bash
cd backend && .venv/bin/python ../scripts/seed.py ../seed_data/projects/nur_navoi.json \
  && .venv/bin/python ../scripts/seed.py ../seed_data/projects/mikoko_pamoja.json
```
Expected: two `seeded ...` lines (real AOI imagery or placeholder).

- [ ] **Step 4: Verify the DB now holds exactly the two assets:**

Run: `PGPASSWORD=canopy psql -h localhost -p 5433 -U canopy -d canopy -c "select id, asset_type, risk_band from projects order by name;"`
Expected: `mikoko_pamoja | mangrove | Low` and `nur_navoi_solar | solar | Low` — no `pizarro`.

- [ ] **Step 5: Update `backend/tests/test_projects_api.py`** — replace the Pizarro-specific tests and fix the risk-band assertion. Change `test_list_and_detail` to assert Nur Navoi's new band, and swap the two dossier tests to the surviving assets:

```python
def test_list_and_detail(client, seed):
    seed()  # default nur_navoi
    assert client.get("/projects").json()[0]["id"] == "nur_navoi_solar"
    detail = client.get("/projects/nur_navoi_solar").json()
    assert detail["risk_band"] == "Low"
```

```python
def test_dossier_returns_mikoko(client, seed):
    seed("mikoko_pamoja")
    dossier = client.get("/projects/mikoko_pamoja/dossier").json()
    assert dossier["project_id"] == "mikoko_pamoja"
    assert dossier["disclosure"]["title"]
    assert {c["kind"] for c in dossier["claims"]} >= {"protected_ha", "credits_tco2"}
    assert dossier["confidence"]["on_track_pct"] > 0
    assert dossier["memo_ready"] is True
```

```python
def test_dossier_malformed_fixture_returns_clean_error(client, seed, tmp_path, monkeypatch):
    """A fixture that exists but drops a required field must surface as a clean envelope,
    not a raw ResponseValidationError."""
    from app.core.config import get_settings

    seed("mikoko_pamoja")
    (tmp_path / "mikoko_pamoja.dossier.json").write_text('{"project_id": "mikoko_pamoja"}')
    monkeypatch.setattr(get_settings(), "dossier_dir", tmp_path)
    res = client.get("/projects/mikoko_pamoja/dossier")
    assert res.status_code == 500
    assert res.json()["error"]["code"] == "invalid_fixture"
```

(Leave `test_detail_404`, `test_boundary_*`, `test_imagery_layers`, `test_dossier_404_for_unknown_project` as-is — none reference Pizarro. Grep to confirm: `grep -rn pizarro backend/` must return nothing.)

- [ ] **Step 6: Run the backend suite:**

Run: `cd backend && uv run pytest -q`
Expected: all pass.

- [ ] **Step 7: Confirm no lingering Pizarro references in backend/tests:**

Run: `grep -rn pizarro backend/tests backend/app`
Expected: no output.

- [ ] **Step 8: Commit (touches `.py` → gate applies; JSON deletions ride along):**

Run the backend gate + `/simplify` + `/code-review` per Global Constraints, then:
```bash
git add -A
git write-tree > .git/canopy-review-marker
git commit -m "data: remove Pizarro; reseed Nur Navoi + Mikoko Pamoja; update dossier tests"
```

---

### Task 4: Frontend asset-type config + type-aware claim labels

**Files:**
- Create: `frontend/src/lib/assetType.ts`
- Modify: `frontend/src/lib/dossier.ts`
- Create: `frontend/src/lib/dossier.test.ts`

**Interfaces:**
- Produces: `assetTypeConfig(assetType?: string): { observeTitle: string; footprintLabel: string; claimLabels: Record<string,string> }` and `claimLabel(kind: string, assetType?: string): string`.

- [ ] **Step 1: Write the failing test `frontend/src/lib/dossier.test.ts`:**

```ts
import { describe, expect, it } from "vitest";
import { claimLabel } from "@/lib/dossier";
import { assetTypeConfig } from "@/lib/assetType";

describe("claimLabel", () => {
  it("uses the solar label for a solar claim kind", () => {
    expect(claimLabel("capacity_mw", "solar")).toBe("Nameplate capacity");
  });
  it("uses the mangrove label for a mangrove claim kind", () => {
    expect(claimLabel("protected_ha", "mangrove")).toBe("Protected area");
  });
  it("falls back to Title Case for an unknown kind", () => {
    expect(claimLabel("weird_kind", "mangrove")).toBe("Weird Kind");
  });
});

describe("assetTypeConfig", () => {
  it("gives the mangrove Observe framing", () => {
    expect(assetTypeConfig("mangrove").observeTitle).toBe("Forest change & canopy");
    expect(assetTypeConfig("mangrove").footprintLabel).toBe("Canopy area");
  });
  it("defaults safely for an unknown type", () => {
    expect(assetTypeConfig(undefined).observeTitle).toBe("Build progress");
  });
});
```

- [ ] **Step 2: Run it to verify it fails:**

Run: `cd frontend && npx vitest run src/lib/dossier.test.ts`
Expected: FAIL (`assetType` module / `claimLabel` signature not present).

- [ ] **Step 3: Create `frontend/src/lib/assetType.ts`:**

```ts
/** Per-asset-type presentation rules (Approach A — the "what each type looks like" config
 * lives in the frontend, keyed by the backend's `asset_type`). Owns the Observe-tab framing
 * and the claim-label vocabulary; the metric *data* still comes from the dossier. */
export type AssetTypeConfig = {
  observeTitle: string; // Observe-tab card title
  footprintLabel: string; // observation-point area metric label
  claimLabels: Record<string, string>; // claim kind -> display label
};

const SOLAR: AssetTypeConfig = {
  observeTitle: "Build progress",
  footprintLabel: "Footprint",
  claimLabels: {
    capacity_mw: "Nameplate capacity",
    generation_gwh: "Annual generation",
    co2_avoided_tpy: "CO₂ avoided",
    area_ha: "Panel-field footprint",
    cod_date: "Commercial operation date",
    timeline_months: "Construction timeline",
  },
};

const MANGROVE: AssetTypeConfig = {
  observeTitle: "Forest change & canopy",
  footprintLabel: "Canopy area",
  claimLabels: {
    protected_ha: "Protected area",
    restored_ha: "Restored area",
    credits_tco2: "Carbon credits issued",
    community_usd: "Community benefit",
  },
};

const DEFAULT: AssetTypeConfig = {
  observeTitle: "Build progress",
  footprintLabel: "Footprint",
  claimLabels: {},
};

const CONFIGS: Record<string, AssetTypeConfig> = { solar: SOLAR, mangrove: MANGROVE };

/** Config for an asset type, with a safe fallback for unknown/absent types. */
export function assetTypeConfig(assetType: string | undefined): AssetTypeConfig {
  return (assetType && CONFIGS[assetType]) || DEFAULT;
}
```

- [ ] **Step 4: Rewrite `frontend/src/lib/dossier.ts`** — make `claimLabel` type-aware, drop the now-duplicated `CLAIM_LABELS` (moved into the solar config):

```ts
/** Dossier-narrative presentation helpers — claim-kind labels and value formatting shared
 * between the Disclosure and Cross-check screens. Labels are asset-type-specific (see
 * lib/assetType.ts); generic string/number/date formatting still goes through lib/format.ts. */
import { assetTypeConfig } from "@/lib/assetType";
import { formatDate, formatNumber, titleCase } from "@/lib/format";
import type { ClaimKind } from "@/lib/types";

/** Display label for a claim kind, resolved against the asset type's vocabulary and
 * falling back to Title Case for any kind the config doesn't name. */
export function claimLabel(kind: ClaimKind, assetType?: string): string {
  return assetTypeConfig(assetType).claimLabels[kind] ?? titleCase(kind);
}

/** Format a claim's promised/observed value using its kind + unit. Dates render as dates;
 * numbers render with their unit; anything else (e.g. a free-text observed description)
 * passes through unchanged. */
export function formatClaimValue(kind: ClaimKind, value: number | string, unit?: string): string {
  if (kind === "cod_date" && typeof value === "string") {
    const isoDate = value.slice(0, 10);
    return /^\d{4}-\d{2}-\d{2}$/.test(isoDate) ? formatDate(isoDate) : value;
  }
  if (typeof value === "number") return formatNumber(value, { unit });
  return value;
}
```

- [ ] **Step 5: Run the test to verify it passes:**

Run: `cd frontend && npx vitest run src/lib/dossier.test.ts`
Expected: PASS.

- [ ] **Step 6: Commit (touches `.ts` → gate applies):**

Run the frontend gate + `/simplify` + `/code-review` per Global Constraints, then:
```bash
git add frontend/src/lib/assetType.ts frontend/src/lib/dossier.ts frontend/src/lib/dossier.test.ts
git write-tree > .git/canopy-review-marker
git commit -m "feat: asset-type presentation config + type-aware claim labels"
```

---

### Task 5: Wire `asset_type` into the pages + update primary + api test

**Files:**
- Modify: `frontend/src/app/projects/[id]/page.tsx` (Disclosure — claim labels)
- Modify: `frontend/src/app/projects/[id]/crosscheck/page.tsx` (claim labels)
- Modify: `frontend/src/app/projects/[id]/timeline/page.tsx` (Observe title + footprint label)
- Modify: `frontend/src/lib/config.ts` (`PRIMARY_PROJECT_ID`)
- Modify: `frontend/src/lib/api.test.ts` (drop the `pizarro/dossier` reference)

**Interfaces:**
- Consumes: `claimLabel(kind, assetType)` and `assetTypeConfig(assetType)` from Task 4; `useProject(id)` (returns `{ data: { asset_type } }`).

- [ ] **Step 1: Disclosure page (`page.tsx`)** — read the asset type and pass it to `claimLabel`. Add the import and hook, and update the claim label call:

Add near the other imports:
```tsx
import { useDossier, useProject } from "@/lib/queries";
```
In the component body (after `const { id } = use(params);`):
```tsx
  const { data: project } = useProject(id);
  const assetType = project?.asset_type;
```
Change the claim label cell from `{claimLabel(c.kind)}` to:
```tsx
                <Td className="font-medium">{claimLabel(c.kind, assetType)}</Td>
```

- [ ] **Step 2: Cross-check page (`crosscheck/page.tsx`)** — same pattern:

Update the import:
```tsx
import { useDossier, useProject } from "@/lib/queries";
```
After `const { id } = use(params);`:
```tsx
  const { data: project } = useProject(id);
  const assetType = project?.asset_type;
```
Change `{claim ? claimLabel(claim.kind) : r.claim_id}` to:
```tsx
                      <p>{claim ? claimLabel(claim.kind, assetType) : r.claim_id}</p>
```

- [ ] **Step 3: Observe page (`timeline/page.tsx`)** — drive the card title and the snapshot footprint label from the config:

Add imports:
```tsx
import { assetTypeConfig } from "@/lib/assetType";
import { useBoundary, useDossier, useImagery, useProject } from "@/lib/queries";
```
After `const { id } = use(params);`:
```tsx
  const { data: project } = useProject(id);
  const cfg = assetTypeConfig(project?.asset_type);
```
Change the "Build progress" `CardHeader title` to `title={cfg.observeTitle}`.
Change the per-snapshot footprint label — replace the literal `Footprint:` text with `{cfg.footprintLabel}:`:
```tsx
                  <span>
                    {cfg.footprintLabel}:{" "}
                    <span className="font-mono tabular-nums text-ink">
                      {formatNumber(s.footprint_ha, { unit: "ha" })}
                    </span>
                  </span>
```

- [ ] **Step 4: Update `frontend/src/lib/config.ts`:**

```ts
export const PRIMARY_PROJECT_ID = "nur_navoi_solar";
```

- [ ] **Step 5: Update `frontend/src/lib/api.test.ts`** — change the `pizarro/dossier` expectation to a surviving id:

Change the asserted URL from `/api/projects/pizarro/dossier` to `/api/projects/nur_navoi_solar/dossier` (and any `pizarro` id in that test to `nur_navoi_solar`). Confirm with `grep -n pizarro frontend/src/lib/api.test.ts` (expect no output after).

- [ ] **Step 6: Run the frontend gate:**

Run: `cd frontend && ./node_modules/.bin/tsc --noEmit && ./node_modules/.bin/eslint . && npx vitest run`
Expected: tsc clean, eslint clean, all vitest pass.

- [ ] **Step 7: Confirm no lingering Pizarro references in the frontend:**

Run: `grep -rn pizarro frontend/src`
Expected: no output.

- [ ] **Step 8: Commit (touches `.tsx`/`.ts` → gate applies):**

Run the frontend gate + `/simplify` + `/code-review` per Global Constraints, then:
```bash
git add frontend/src/app/projects/'[id]'/page.tsx frontend/src/app/projects/'[id]'/crosscheck/page.tsx frontend/src/app/projects/'[id]'/timeline/page.tsx frontend/src/lib/config.ts frontend/src/lib/api.test.ts
git write-tree > .git/canopy-review-marker
git commit -m "feat: render Disclosure/Cross-check/Observe per asset_type; primary = Nur Navoi"
```

---

### Task 6: End-to-end verification

**Files:** none (verification only).

- [ ] **Step 1: Ensure both servers are running** (backend `:8001`, frontend `:3000`). Restart the backend if fixtures/code changed:

```bash
cd backend && lsof -ti :8001 | xargs kill 2>/dev/null; sleep 1
.venv/bin/uvicorn app.main:app --port 8001 --host 127.0.0.1 &
```

- [ ] **Step 2: API smoke test (both assets, both dossiers):**

```bash
cd backend && .venv/bin/python - <<'PY'
import urllib.request, json
def get(u):
    with urllib.request.urlopen(u, timeout=10) as r: return r.status, json.loads(r.read())
s, projs = get("http://localhost:3000/api/projects")
print("projects:", [(p["id"], p["asset_type"]) for p in projs])
for pid in ("nur_navoi_solar", "mikoko_pamoja"):
    s, d = get(f"http://localhost:3000/api/projects/{pid}/dossier")
    print(pid, "claims:", [c["kind"] for c in d["claims"]], "on_track:", d["confidence"]["on_track_pct"])
PY
```
Expected: two projects (`solar`, `mangrove`); Nur Navoi claims include `generation_gwh`; Mikoko claims include `protected_ha`.

- [ ] **Step 3: Drive both assets in the browser** (Playwright or manual). For **Mikoko Pamoja**, confirm:
  - Portfolio lists Nur Navoi (Primary badge) + Mikoko Pamoja; types read "Solar" / "Mangrove".
  - Disclosure claim labels read "Protected area", "Carbon credits issued", etc. (not "Protected Ha").
  - Observe tab title reads **"Forest change & canopy"** and snapshot rows read **"Canopy area:"**.
  - Cross-check rows read the mangrove claim labels with met/on_track statuses.
  - Confidence shows 90% + the mangrove drivers.
  For **Nur Navoi**, confirm the self-reporting-gap framing (disclosure = self-reported; cross-check = confirmed build/COD + generation proxy; confidence 85%).

- [ ] **Step 4: Full gate (backend + frontend):**

```bash
cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest -q
cd ../frontend && ./node_modules/.bin/tsc --noEmit && ./node_modules/.bin/eslint . && npx vitest run
```
Expected: all green.

---

## Self-Review

**Spec coverage:**
- Remove Pizarro → Task 3. Rework Nur Navoi → Task 1. Add Mikoko Pamoja → Task 2. `asset_type` discriminator (reused, no schema change) → Tasks 1/2 set it, Tasks 4/5 consume it. Per-type frontend config (Approach A) → Task 4. Observe framing + claim labels + `PRIMARY_PROJECT_ID` → Tasks 4/5. Tests updated → Tasks 3/4/5. Reseed → Task 3. Non-goal (real imagery) respected — placeholders only. ✅ All spec sections mapped.

**Placeholder scan:** No TBD/TODO; every fixture and code block is complete literal content. ✅

**Type consistency:** `assetTypeConfig` / `claimLabel(kind, assetType)` signatures defined in Task 4 and consumed verbatim in Task 5. Evidence ids (`nur_navoi_solar_ev_0`, `mikoko_pamoja_ev_0`) match the `{pid}_ev_0` pattern the seed script produces and the `evidence_ids` used in the dossiers. Claim kinds in the dossiers match the `claimLabels` keys in `assetType.ts`. ✅
