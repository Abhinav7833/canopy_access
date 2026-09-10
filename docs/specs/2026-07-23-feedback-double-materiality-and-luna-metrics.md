# Canopy — double materiality, legal cross-reference, and Luna's unsurfaced metrics

**Branch:** `canopy-feedback` (off `main`, with `canopy-mvp` merged in for the verdict
vocabulary and the imagery honesty fix).

**Inputs:** two voice notes from Luna (2026-07-23) and `Canopy_Hackathon_Pitch.pptx.pdf`.

---

## 0. What the feedback actually says

> **(1)** "when we locate, we also cross-reference with legal stuff … permits, construction
> permits, anything that has to do with lawsuits. All of that is also done. So we need this
> as well, to show as well. That's more of the financial part. So when you say cross-check,
> that's one of the things that we also want to cross-check on the plant."

> **(2)** "when you put confidence, the risk score, you put physical risk, so degradation and
> everything … we work on double materiality matrix. The question we ask first is: what is
> the impact of the plant to its environment? And then you have to separate it with what's
> the impact of the environment [on the plant]. So flood risk, fire risk, those things to our
> physical plant. These are two things that we need to separate."

The pitch deck says the same thing in product language (slide 4): *"What harm is the project
doing?"* vs *"What danger is nature posing to it?"* — plus *"Who is behind it, legally?"*.

---

## 1. The defect behind feedback (2)

`canopy_pipeline/analytics/risk_scoring.py:45`

```python
composite = max(fire, flood, degradation)   # worst hazard drives screening
```

The three sub-scores are not the same kind of measurement:

| Sub-score | Derivation | Direction | Materiality |
|---|---|---|---|
| `fire` | FFWI hazard x asset exposure x fuel vulnerability | environment -> asset | financial |
| `flood` | Aqueduct 100yr depth x exposure x Huizinga damage | environment -> asset | financial |
| `degradation` | observed vegetation loss (`pct_loss`) | asset -> environment | impact |

A single `max()` across both directions yields a number whose meaning is undefined: it rises
both when the site is *endangered* and when the site *causes harm*. The reader cannot tell
which, and the two imply opposite actions (insure/harden vs remediate/mitigate).

The product inherited the conflation verbatim: `PhysicalRiskOut {fire, flood, degradation,
composite}` renders as a single "Physical risk" card on the Confidence screen, and
`confidences.risk_score` / `risk_band` (which drive the portfolio rating) are fed from that
mixed composite.

**Fix:** never merge the two directions into one score. Two groups, two composites, two
bands, two cards, each labelled with the question it answers.

---

## 2. Target model

### 2.1 Financial materiality — environment -> asset ("what danger is nature posing to it?")

Table `asset_hazards` (renamed from `physical_hazards`, degradation removed):

| Field | Source |
|---|---|
| `fire_score`, `fire_band` | `risk_scoring.score()["fire"]` |
| `fire_ffwi`, `fire_dnbr`, `fire_severity_class` | `risk_detail.fire_*` |
| `flood_score`, `flood_band` | `risk_scoring.score()["flood"]` |
| `flood_depth_100yr_m`, `flood_damage_frac`, `flood_observed_frac` | `risk_detail.flood_*` |
| `heat_score`, `heat_band`, `water_stress_score`, `water_stress_band` | deck slide 4 (not yet computed -> nullable) |
| `asset_exposure` | `risk_detail.asset_exposure` |
| `composite_score`, `composite_band` | max(fire, flood, heat, water) — **hazards only** |

### 2.2 Impact materiality — asset -> environment ("what harm is the project doing?")

Table `environmental_effects` (new; receives `degradation`):

| Field | Source |
|---|---|
| `vegetation_change_pct` | `metrics.vegetation_change_percent` |
| `vegetation_loss_score`, `vegetation_loss_band` | `risk_scoring.score()["degradation"]` |
| `deforestation_detected` | `metrics.deforestation_detected` |
| `water_change_pct` | NDWI delta (deck: "water changes") — nullable until computed |
| `land_disturbance_ha` | deck: "land clearing" — nullable until computed |
| `community_exposure_built_up` | `risk_detail.community_exposure_built_up` |
| `composite_score`, `composite_band` | **effects only** |

The existing `impact_metrics` (generation, avoided emissions, carbon stock, additionality)
is the *positive* half of the same inside-out question and is presented in the same section,
not as an unrelated card.

### 2.3 Consequences elsewhere

- `risk_scoring.score()` returns `hazard_composite` and `effect_composite`; no `max()` across
  the two. `json_export.assemble()` summary carries both.
- `confidences.risk_score` / `risk_band` are defined as the **hazard** composite (what an
  asset manager underwrites); the effect composite is surfaced beside it, never folded in.
- Portfolio rating column keeps meaning what it means today (asset risk) — one added column
  for the impact side rather than a silently changed number.

---

## 3. Legal & regulatory cross-reference (feedback 1)

**Nothing exists.** `grep -rn "legal|sanction|permit|lawsuit|opencorporates|cross_reference"`
over `canopy_pipeline/` returns zero hits; the product has no field and no UI. The deck
advertises it on three slides ("Scans 240M companies for sanctions, permits and lawsuits").

Table `legal_checks` (one row per check, ordinal-ordered):

| Field | Meaning |
|---|---|
| `check_type` | `permit` \| `sanction` \| `litigation` \| `ownership` |
| `subject` | what was checked (entity name, permit reference) |
| `verdict` | the shared 4-value vocabulary (`app/core/vocabulary.py`) |
| `detail` | one line, e.g. "renewal due Q3 2026" |
| `authority` | issuing or screening body |
| `as_of` | date the check reflects |
| `reference` | document / register id |
| + `trace_*` | via `TraceMixin`, like every other dossier element |

Verdict mapping: clean screening -> `consistent`; expiring permit or partial register
coverage -> `partially_consistent`; sanctions hit or revoked permit -> `inconsistent`;
register not reachable -> `insufficient_data`.

**Data source:** no connector exists, so values are authored per asset for now — labelled
with their real authority and `as_of` date, and never described as an automated 240M-company
scan we did not run. A connector (OpenCorporates / EU + OFAC sanctions lists / national
permit registers) is the follow-up, gated behind `CANOPY_LIVE_CONNECTORS`.

UI: a "Legal & regulatory" section on the Cross-check screen, same table idiom and same
verdict pills as the claim rows — this is a cross-check, per the feedback.

---

## 4. Luna's metrics the product does not surface

Enumerated from `verify_disclosure.py`, `analytics/{confidence,risk_scoring,screening,
timeseries,fire,flood}.py` and `export/json_export.py`.

| # | Metric group | Engine field(s) | Where it belongs | Priority |
|---|---|---|---|---|
| C1 | Confidence decomposition | `localisation_confidence`, `build_progress_confidence`, `on_track_confidence`, `status` | Confidence screen — explains the headline % | **P1** |
| C2 | Resolution detail | `match_score`, `margin`, `matched_fields`, `confidence_label`, `gem_location_id`, `source` | Locate screen — the deck's "0.94, two paths agree" | **P1** |
| C3 | AOI assurance | `aoi.assurance`, `observed_area_ha`, `has_footprint` | Locate — is the boundary a real footprint or a point box? | **P1** |
| C4 | Risk provenance | `fire_ffwi`, `fire_dnbr`, `fire_severity_class`, `flood_depth_100yr_m`, `flood_damage_frac`, `flood_observed_frac`, `asset_exposure`, `community_exposure_built_up` | folds into §2 tables | **P1** |
| C5 | Cross-check enrichment | `delta`, `assurance_label`, `note`, per-check `confidence` | Cross-check table; also the P1.5 bundle reconciliation | **P2** |
| C6 | Vegetation detail | `ndvi_start/end/trend`, `trend_per_year`, `interannual_std`, `trend_significant`, `vegetation_change_percent`, `deforestation_detected` | Observe + §2.2 | **P2** |
| C7 | Screening summary | `screening_status`, `change_detected`, `human_review_recommended`, `main_finding`, `assurance_statement` | project header / Confidence | **P2** |
| C8 | Evidence card detail | `observation_type`, typed `metric{name,value,baseline,comparison}`, `source{resolution,processing}`, `agb_t_ha`, `carbon_source`, `ndvi_timeline` | Evidence drawer | **P3** |
| C9 | Map outputs | `ndvi_raster_url`, `change_map_url`, `aoi_geojson_url` | Observe — makes the swipe real | **P3** (needs GEE) |

---

## 5. Phases

- **Phase 1 — double materiality.** §2: split the tables, split `risk_scoring`, migration,
  two Confidence cards, portfolio column. Absorbs C4 and the `degradation` half of C6.
- **Phase 2 — legal cross-reference.** §3: table, schema, seeded values, Cross-check section.
- **Phase 3 — confidence & localisation provenance.** C1, C2, C3, C7.
- **Phase 4 — cross-check + evidence enrichment.** C5, C6 remainder, C8.
- **Phase 5 — ingestion.** Replace authored fixtures with `verify_disclosure()` output
  (the P1.5/P1.7 seam). Needs Luna's bundle frozen; C9 needs GEE credentials.

Each phase: typed tables -> Pydantic contract -> seeder validation -> UI -> tests -> gates
(ruff/mypy/pytest, tsc/eslint/vitest/next build) -> in-browser verification.

---

## 6. Deck/product inconsistencies to resolve (not feedback, but demo-blocking)

1. Case-study numbers disagree: deck says Nur Navoi **858 ha observed / 900 ha claimed** and
   225–265 GWh; the fixture says **238 / 240 ha** and ~270 GWh. The hectare figures look like
   Núñez de Balboa's (500 MW, ~1000 ha) under Nur Navoi's name and 100 MW label.
2. The slide-3 dashboard mockup is captioned "Solar Park – Rajasthan, India" — a third asset.
3. Deck roadmap says the engine runs on **Nur Navoi and Núñez de Balboa**; the product ships
   Nur Navoi and Mikoko Pamoja. Mikoko does not appear in the pitch. Luna's engine has
   `disclosure/claims/{nunez,pizarro}.json`. This is the demo-asset decision, still open.
