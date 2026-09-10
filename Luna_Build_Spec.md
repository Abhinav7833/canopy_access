# Canopy — Luna's Build Spec (sprint → Wednesday)

**Audience:** Claude Code, building on the existing `canopy_pipeline/` repo.
**Owner:** Luna (geospatial / pipeline / verification layer).
**Not in scope:** Abhinav's imagery-based detection/classification model — that's a separate workstream. Where this spec needs his output, it defines a stub interface (see Appendix C).

---

## 0. Context & conventions (read first)

The repo is a modular Sentinel pipeline. Existing structure to respect and reuse:

```
canopy_pipeline/
  config.py
  run_pipeline.py
  input/            # AOI + request validation
  data/             # sentinel1_loader.py, sentinel2_loader.py, reference.py
  preprocessing/    # cloud_masking, clipping, resampling, normalization
  indices/          # ndvi.py, ndwi.py, nbr.py
  analytics/        # carbon_model, change_detection, fire, flood, risk_scoring, screening, timeseries
  export/           # json_export, geojson_export, raster_export
handover/canopy_aois.geojson
```

**Reuse, don't rebuild:**
- `data/reference.py` already has `annual_ghi(aoi, year)` and `pv_generation_estimate(capacity_mw, ghi_kwh, pr=0.80, tracking=1.0)`. The solar impact chain (area→capacity→generation→CO₂) already exists. Do **not** re-implement it.
- `analytics/carbon_model.py` already does the mangrove AGB→carbon chain.
- Follow the existing JSON output spec used by `export/json_export.py`.

**Hard rules (architecture guarantees):**
1. **Deterministic matching only.** GEM/OSM/Catastro are structured data — match with pandas + `rapidfuzz` + `geopandas`. **No LLM in the matching or measurement path.**
2. **LLM (if used at all) only reads unstructured disclosure text**, returns values *with the source location*, and never decides a match.
3. **Every value must trace to a source** via the evidence graph (WI-4). No orphan numbers.
4. **Precompute offline.** The demo shows precomputed results — no live processing on stage.

**Demo scope:** two Spanish assets only — **Francisco Pizarro** (primary), **Núñez de Balboa** (backup). These are a *validation set*, not production.

---

## Work items

### WI-1 — Lock the AOIs (foundational; everything depends on this)

**Goal:** produce authoritative footprint polygons + provenance for both assets, plus the "gap" polygons.

**Location:** extend `handover/canopy_aois.geojson` (or a new `data/aois/` folder of GeoJSON).

**Inputs (starting hints — do NOT hardcode as final):**
- Pizarro: centre ≈ 39.61 N, 5.69 W; generous box N 39.66 / S 39.56 / W 5.76 / E 5.60; ~1,300 ha field.
- Núñez: centre ≈ 38.30 N, 6.16 W; box N 38.34 / S 38.26 / W 6.22 / E 6.10; ~854–1,000 ha field.

**Steps:**
1. Pull each footprint polygon from **GEM** (Global Solar Power Tracker: "Francisco Pizarro solar farm", "Núñez de Balboa"). GEM maps phase polygons.
2. Cross-check against **OpenStreetMap** (Overpass query: `way["power"="plant"]["plant:source"="solar"]` within the bbox).
3. Refine boundary with **Spanish Catastro** parcels.
4. Digitise the **gap polygons**: Pizarro = the un-paneled exclusion zones inside the fence (little-bustard + archaeological); Núñez = the ~525 ha disputed parcel (from Catastro).
5. Store each feature with properties: `{name, asset_type, source, source_url, retrieved_date, notes}`.

**Definition of Done:** valid GeoJSON, one polygon per asset + one gap polygon per asset, each with provenance properties; opens correctly in geojson.io / QGIS; areas within ~10% of reported (~1,300 ha Pizarro, ~900 ha Núñez).

---

### WI-2 — Disclosure → claims schema + curated claim files

**Goal:** a structured, sourced representation of what each disclosure *promises* — the left-hand side of every cross-check.

**Location:** new `canopy_pipeline/disclosure/` — `claims_schema.py`, `claims/pizarro.json`, `claims/nunez.json`.

**Approach:** for the 2 demo assets, hand-curate the claim JSON from the source pack (LLM extraction is optional and out of critical path — if built, it must output the same schema and cite page/URL per field).

**Claim schema (per asset):**
```json
{
  "asset_id": "pizarro",
  "name": "Francisco Pizarro Solar Farm",
  "asset_type": "solar_pv",
  "region": "Cáceres, Extremadura, Spain",
  "developer": "Iberdrola",
  "claims": {
    "capacity_mwp":        {"value": 590,   "unit": "MWp", "source": "Iberdrola start-up release (Aug 2022)", "source_url": "..."},
    "area_ha":             {"value": 1300,  "unit": "ha",  "source": "NS Energy project profile", "source_url": "..."},
    "financing_date":      {"value": "2019","unit": "year","source": "green PPA (Danone/Bayer/PepsiCo)", "source_url": "..."},
    "operational_date":    {"value": "2022-08", "source": "Iberdrola", "source_url": "..."},
    "build_phased_through":{"value": "2023", "source": "Phase III EIA BOE-A-2023-5247", "source_url": "..."},
    "co2_avoided_tpy":     {"value": 150000,"unit": "tCO2/yr", "source": "Iberdrola", "source_url": "..."}
  }
}
```
Curate the equivalent for Núñez (500 MWp / 391 MWac, ~854–1,000 ha, built 2019, grid export 2020-04, EIB Green Loan 20180584 €145m + ICO €140m, ~832 GWh/yr, ~215k tCO₂/yr, court order 2022-06 to return 525 ha).

**Definition of Done:** both claim files validate against `claims_schema`; every claim has a `source`.

---

### WI-3 — Reference + entity-resolution layer (your Path A)

**Goal:** given disclosure attributes, return a **candidate location** from the structured reference databases — deterministically.

**Location:** new `canopy_pipeline/matching/` — `reference_loader.py`, `entity_resolution.py`.

**`reference_loader.py`:** load GEM tracker table(s) (CSV/XLSX from the GEM data request), plus optional OSM/Catastro geometries, into a normalised GeoDataFrame with columns: `name, asset_type, country, capacity, start_year, lat, lon, geometry, source`.

**`entity_resolution.py`:**
```python
def resolve_candidate(claims: dict, reference_gdf) -> dict:
    """Deterministically match a disclosure to a reference asset.
    Returns {candidate_geometry, candidate_centroid, match_score, matched_fields, source}.
    match_score = weighted combination of:
      - fuzzy name match (rapidfuzz token_set_ratio)
      - capacity within tolerance (e.g. ±20%)
      - country/region match
      - (optional) start_year vs financing/operational date
    Return the argmax candidate AND the margin to the runner-up (the confidence signal).
    No LLM. No ML.
    """
```

**Definition of Done:** `resolve_candidate` returns the correct GEM/OSM polygon for both Pizarro and Núñez, with a `match_score`, a `margin` to the second-best, and the matched-fields list. Deterministic and logged.

---

### WI-4 — Evidence graph (the provenance backbone)

**Goal:** a per-project knowledge graph where every value traces to the base disclosure — the anti-hallucination / audit layer.

**Location:** new `canopy_pipeline/evidence/` — `graph_schema.py`, `graph_builder.py`. Use `networkx` (in-memory) + JSON serialisation. Do **not** use a graph DB.

**Node schema:**
```json
{
  "id": "pizarro.observed.footprint_ha",
  "type": "claim | observation | derived | source",
  "value": 1287.4,
  "unit": "ha",
  "source": "Sentinel-2 composite 2023 / GEM polygon",
  "source_url": "...",
  "date": "2023-07-01",
  "method": "geopandas area of matched polygon",
  "confidence": 0.9,
  "formula_at_time": "area(polygon) in ha",
  "assurance_label": "observed | modelled | needs-ground-truth",
  "parent_ids": ["pizarro.disclosure.root"]
}
```

**Rules:**
- Root node per project = the base disclosure.
- Claims (WI-2) attach to root. Observations attach to the claim they test. Derived values (e.g. generation estimate) carry `formula_at_time` + `assurance_label` and link to their inputs.
- **Invariant:** every leaf must have a path to the disclosure root. Add a `validate_graph()` that fails if any node is orphaned.

**Definition of Done:** `graph_builder` assembles a Pizarro graph from the claim file + pipeline outputs; `validate_graph()` passes; serialises to JSON that `export/` (and later Cem's UI) can read.

---

### WI-5 — Cross-check stage (reported vs observed)

**Goal:** pit each disclosed claim against the observed value and emit a verdict + delta + assurance, written into the evidence graph.

**Location:** new `canopy_pipeline/analytics/cross_check.py`.

```python
def cross_check(claims: dict, observed: dict) -> list[dict]:
    """For each comparable claim, return a record:
    {claim, reported, observed, delta, verdict, confidence, assurance_label, note}
    verdict in {consistent, partially_consistent, inconsistent, insufficient_data}
    Phrase notes in ISAE 3000 / ISSA 5000 limited-assurance language.
    """
```

**Checks to implement (minimum):**
- **Scale:** observed footprint area vs capacity-implied area band (capacity × ~1.5–3 ha/MW).
- **Timing (the key check):** `build_onset_year >= financing_year` → "additional capacity, consistent with use-of-proceeds"; if earlier → flag. Needs `build_onset_year` from Abhinav's build-dating (Appendix C) or the S1/S2 trajectory.
- **Magnitude:** modelled generation band (reuse `pv_generation_estimate`) vs reported — present as a conservative lower bound, not a point match.

**Definition of Done:** running on Pizarro produces the reported-vs-observed record set; each record is written as evidence-graph nodes; timing check correctly returns "consistent (post-financing)" for Pizarro.

---

### WI-6 — Walk-forward backtest harness (proves the coordinate claim)

**Goal:** demonstrate the pipeline localises + verifies from a region-level hint alone, scored against the locked ground truth. Internal validation, not production.

**Location:** new `canopy_pipeline/backtest/` — `harness.py`.

**Steps:**
1. Take Pizarro. Hide the coordinates. Assemble the **hint** = `{region, developer, capacity_mwp, financing_date}` (subset of the claim file).
2. Pass the hint to the localizer interface (Appendix C) → get proposed footprint + confidence.
3. **Score localization:** IoU (intersection-over-union) of the proposed footprint vs the WI-1 locked polygon; also centroid distance. Pass threshold: IoU ≥ 0.5 (tune).
4. Run the pipeline from the pre-build baseline year (Pizarro: 2020) → 2023.
5. **Score timing:** detected build-onset lands after `financing_date` and matches the known phased 2021→2023 build.
6. **Score scale:** observed area within the capacity-implied band.
7. Emit a headline line: `"given a standard disclosure, localised (IoU=0.72) and confirmed build post-financing → on-track"`.

**Definition of Done:** `harness.py` runs end-to-end on Pizarro with a stubbed localizer (Appendix C) and prints the three scores + headline. Swappable to Abhinav's real localizer via the interface.

---

## Appendix A — schema files to create
- `disclosure/claims_schema.py` (WI-2)
- `evidence/graph_schema.py` (WI-4)
- cross-check record shape (WI-5) — document inline.

## Appendix B — data sources
- **GEM** Global Solar Power Tracker / Global Integrated Power Tracker (CC BY 4.0; request via GEM form). Names: "Francisco Pizarro solar farm", "Núñez de Balboa".
- **OpenStreetMap** via Overpass API (`power=plant`, `plant:source=solar`).
- **Spanish Catastro** (sede electrónica) — parcel geometry; source of Núñez's 525 ha disputed parcel.
- **EIB** project page 20180584 (Núñez finance chain).
- Carbon assets (future): **Verra**, **Plan Vivo**, **Gold Standard** registries.

## Appendix C — interface with Abhinav (stub now, swap later)
```python
def localize(hint: dict) -> dict:
    """Abhinav's detection model. INPUT: {region, developer, capacity_mwp, financing_date}.
    OUTPUT: {footprint_geometry, centroid, confidence}.
    STUB for now: return the WI-1 polygon + confidence 1.0 so the harness runs.
    Confirm with Abhinav: output type (bbox / polygon / centroid+radius) and hint format.
    """
```
The seam to agree with Abhinav: **he** produces candidate footprint(s) from pixels; **Luna** does attribute-based disambiguation (capacity/date/substation) and the reference match. Agreement between his detection and Luna's reference candidate = the confidence number.

---

## Suggested build order
1. WI-1 (AOIs) — unblocks all.
2. WI-2 (claims) — cheap, curated.
3. WI-4 (evidence graph schema) — the backbone; build early so WI-3/5 write into it.
4. WI-3 (reference matching).
5. WI-5 (cross-check).
6. WI-6 (backtest) — gated on Abhinav's `localize` output format; run with the stub until then.
