# Canopy — Source-Pack Demo Assets & Asset-Type-Driven Rendering

**Date:** 2026-07-17
**Status:** Approved design, pre-implementation
**Source:** `Canopy_AOI_ Demo_Projects_Source_Pack 02_06.docx.pdf` (engineering brief, the two final demo assets)

## Goal

Replace the demo's two mock assets with the source pack's final pair, and make the
per-project experience render according to the asset's **type** so a solar plant and a
mangrove forest each read in their own language.

- **Remove** the Pizarro (Spain solar) fixtures entirely — it is not in the source pack.
- **Rework** Nur Navoi Solar around the pack's "self-reporting gap" narrative.
- **Add** Mikoko Pamoja (Gazi Bay mangrove blue-carbon) as a new asset.
- **Drive the UI off `asset_type`** so metric labels and the Observe-tab framing differ per
  type, without standing up a backend metric-definition service (Approach A — see below).

Both assets keep the same five-step narrative (Disclosure → Locate → Observe → Cross-check
→ Confidence). They differ in metric vocabulary and wording, not in structure.

## Non-goals / out of scope

- **Real satellite imagery.** Pulling and precomputing real Sentinel-2/1 rasters is the
  separate data-population task (see `canopy-frontend-vs-data-scope`). This work uses the
  existing placeholder image assets (`before_rgb.png` / `after_rgb.png` / `change_overlay.png`)
  keyed as today. The dossier/observation dates and metrics are real (from the pack); the
  pixels are still stand-ins.
- **A backend metric catalog / per-type validation engine** (Approach B). Rejected as
  over-built for a two-asset demo.

## Data model

The `projects.asset_type` column already exists and is already served in `ProjectSummary`
/ `ProjectDetail`. It becomes the type discriminator — **no schema change**.

| id | asset_type | financing_type | role |
|----|-----------|----------------|------|
| `nur_navoi_solar` | `solar` | `development_finance` | Primary (`PRIMARY_PROJECT_ID`) |
| `mikoko_pamoja` | `mangrove` | `carbon_finance` | Secondary |

Cross-check status vocabulary (`met` / `on_track` / `behind` / `variance`) and its tone
mapping are reused unchanged for both types — no new statuses.

## Fixtures (the two dossiers)

Dossier shape is unchanged (`disclosure`, `claims`, `localization`, `observation_series`,
`cross_check`, `confidence`, `memo_ready`); only content differs. Claim `kind`s are free-form
strings (types already permit this). Imagery keys stay `before_rgb.png` / `after_rgb.png` /
`change_overlay.png`.

### Nur Navoi Solar — "the self-reporting gap"

- **Identity:** Nur Navoi Solar, 100 MW, Masdar (Nur Navoi Solar FE LLC); Navoi region,
  Uzbekistan; centroid ≈ (lon 65.3, lat 40.1). Financiers ADB / EBRD (US$25m) / World Bank–IFC.
  PPA Nov 2019 → financing Dec 2020 → construction 2020–2021 → operational **Aug 2021**.
- **Disclosure:** self-reported SDG/green-bond allocation & impact — figures issuer-provided,
  only "limited assurance" paper-checked, never physically verified.
- **Claims:**
  - `capacity_mw` — "Nameplate capacity" — 100 MW
  - `generation_gwh` — "Annual generation" — ~270 GWh/yr
  - `co2_avoided_tpy` — "CO₂ avoided" — ~153,000 tCO₂/yr
  - `area_ha` — "Panel-field footprint" — ~240 ha
  - `cod_date` — "Commercial operation date" — 2021-08-01
- **Localization:** region hint "Navoi region, Uzbekistan"; method = region hint + ADB/World
  Bank site map matched against the Sentinel-2 panel field; alternatives rejected (e.g. the
  Sherabad sister plant — different location/scale).
- **Observation series:** baseline 2019 → construction 2020–21 → operational 2021+ (3 points),
  `footprint_ha` growing to the built scale, `ndvi` dropping as panels cover ground.
- **Cross-check** (independent satellite vs the self-reported figures):
  - footprint / `area_ha` → full build confirmed → `met`
  - `cod_date` → on-time commissioning (Aug 2021) confirmed → `met`
  - `generation_gwh` → proxy consistent with ~270 GWh/yr → `on_track`, with a stated
    limitation (not independently metered)
- **Confidence:** `on_track_pct` ≈ 85, `risk_band` "Low". Rationale: independent satellite
  confirms the plant was built at the claimed scale and is operating on schedule — turning a
  self-reported figure into observed evidence; generation is a consistent proxy, not metered.
  Drivers: full footprint matches disclosed build; on-time commissioning confirmed; generation
  proxy consistent with self-report; **finer/metered claims need ground truth**.

### Mikoko Pamoja — "capital unlocked by data"

- **Identity:** Mikoko Pamoja ("Mangroves Together"), Gazi Bay, Kwale County, Kenya; operated
  by MPCO, coordinated by ACES; centroid ≈ (lon 39.50, lat -4.42). World's first
  community-led blue-carbon project; Plan Vivo-certified.
- **Disclosure:** Plan Vivo certification / project design document — promised protection,
  restoration, and permanence (the "hard part" a small entity must prove to get funded).
- **Claims:**
  - `protected_ha` — "Protected area" — 117 ha
  - `restored_ha` — "Restored area" — ~10 ha
  - `credits_tco2` — "Carbon credits issued" — ~9,880 tCO₂ (2014–2018)
  - `community_usd` — "Community benefit" — ~US$58,591
- **Localization:** region hint "Gazi Bay, Kwale County, Kenya"; method = Plan Vivo boundary
  matched against Sentinel-2 mangrove extent at the tidal edge; alternatives rejected
  (neighbouring Gazi / Makongeni mangroves).
- **Observation series:** annual composites 2016 → 2024 (use ≥3 representative points),
  `footprint_ha` = protected/canopy hectares (stable-to-expanding), `ndvi` = canopy index
  (stable-to-rising); notes describe no-deforestation and canopy expansion.
- **Cross-check** (independent satellite vs the certified outcome):
  - `protected_ha` → ≈0% loss vs the ~2.7%/yr regional deforestation baseline → `met`
  - `restored_ha` → ~10 ha canopy gain confirmed → `met`
  - `credits_tco2` → carbon proxy consistent with the 9,880 credits issued → `on_track`
- **Confidence:** `on_track_pct` ≈ 90, `risk_band` "Low". Rationale: protection and
  restoration independently corroborated; carbon proxy consistent with issued credits;
  permanence risk low. Drivers: no deforestation vs the 2.7%/yr baseline; canopy
  stable-to-expanding on NDVI (biomass growth); carbon proxy matches credits; **finer
  species/impact claims need ground truth**.

### Boundaries

`mikoko_pamoja.json` needs an AOI polygon around its centroid (the seed loads
`project_boundaries` geometry from the project JSON). Nur Navoi keeps its existing polygon.

## Frontend: asset-type-driven presentation (Approach A)

The rules for "what each type looks like" live in the frontend, keyed by `asset_type`. The
backend only stores the type (already) and the metric data (dossier).

- **New `frontend/src/lib/assetType.ts`** — a config map:
  ```ts
  type AssetTypeConfig = {
    observeTitle: string;        // Observe CardHeader title
    footprintLabel: string;      // observation-point area metric label
    claimLabels: Record<string, string>;
  };
  export const ASSET_TYPES: Record<string, AssetTypeConfig> = {
    solar:    { observeTitle: "Build progress",        footprintLabel: "Footprint",      claimLabels: {...} },
    mangrove: { observeTitle: "Forest change & canopy", footprintLabel: "Canopy area",   claimLabels: {...} },
  };
  ```
  With a safe default (fall back to `titleCase` / "Build progress" / "Footprint") for any
  unknown type.
- **`lib/dossier.ts`** — `claimLabel(kind, assetType?)` becomes type-aware: look up
  `ASSET_TYPES[assetType].claimLabels[kind]`, else fall back to the current generic map, else
  `titleCase(kind)`. `formatClaimValue` is unchanged (already generic).
- **Pages read `asset_type` from `useProject(id)`** (DB is the source of truth; React Query
  dedupes the fetch that `ProjectHeader` already makes). Touch points:
  - **Disclosure** (`page.tsx`) and **Cross-check** (`crosscheck/page.tsx`) — claim labels via
    `claimLabel(kind, assetType)`.
  - **Observe** (`timeline/page.tsx`) — `observeTitle` and the per-snapshot `footprintLabel`
    from the config instead of the hardcoded "Build progress" / "Footprint".
- **`lib/config.ts`** — `PRIMARY_PROJECT_ID` → `"nur_navoi_solar"`.

Everything else (Locate, Confidence, portfolio table, `DossierUnavailable`, trace chips)
is already type-agnostic and needs no change.

## Tests & cleanup

- Backend: update the dossier tests that reference Pizarro (`test_dossier_returns_pizarro`,
  `seed("pizarro")`, the malformed-fixture test) to the new assets; keep coverage for the
  happy path, the 404, and the malformed-fixture path.
- Frontend: update `lib/api.test.ts` (`pizarro/dossier` → a surviving id).
- Add a small frontend test that `claimLabel` returns the mangrove label for a mangrove kind
  and the solar label for a solar kind.
- Reseed the DB (drop `pizarro`, add `mikoko_pamoja`).
- Delete `seed_data/projects/pizarro.json` and `pizarro.dossier.json`.

## Success criteria

- Portfolio lists exactly Nur Navoi Solar and Mikoko Pamoja; Nur Navoi carries the Primary badge.
- Nur Navoi reads as the self-reporting-gap story (self-reported figures → independently
  confirmed build + generation proxy, with honest limitation).
- Mikoko Pamoja reads as a mangrove: Observe tab titled "Forest change & canopy", claim labels
  are protection/restoration/credits/community, cross-check verifies protection/growth/carbon.
- Backend and frontend gates stay green; the app drives cleanly through both assets' tabs.
