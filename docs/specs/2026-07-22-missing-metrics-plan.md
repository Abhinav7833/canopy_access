# Add the missing metrics (physical risk · energy · carbon · cross-asset/additionality)

**Status:** scoped + approved by user (all 4 groups; placement = Confidence screen + portfolio KPIs). Ready to execute in a fresh session. Presentation of typed, honestly-authored values (no real pipeline yet) — the slots Luna's real numbers drop into later. Source: gap analysis `docs/specs/2026-07-22-spec-gap-analysis.md` §1.5–§1.9, §5 item 9; spec §6–§8.

## STEP 0 — resolve the DB-migration path FIRST (blocker)
The dossier is normalized into typed Postgres tables. Determine how tables are created before adding any:
- `grep -rn "create_all\|Base.metadata\|alembic" backend/app backend/*.py backend/alembic* 2>/dev/null`; check `backend/app/core/db.py`, `app/main.py` startup, and for an `alembic/` dir.
- If **create_all** on startup → NEW tables auto-create on backend restart (adding *new* tables is safe; ALTERing existing tables is not). Prefer **new tables** (below) over adding columns to existing ones.
- If **alembic** → add one migration.
- Either way: after model + seed changes, restart backend + re-seed (`cd backend && uv run python ../scripts/seed.py`) — the seeder is idempotent and skips existing imagery.

## STEP 1 — backend models (mirror `app/models/dossier.py` typed style; one PK/FK per project)
Add new tables (new tables = create_all-safe). Suggested in `app/models/dossier.py` (or a new `metrics.py` registered in `models/__init__.py`):

- `PhysicalHazards(Base)` — `project_id` PK→projects.id CASCADE; `fire_score:int fire_band:str  flood_score:int flood_band:str  degradation_score:int degradation_band:str  composite_score:int composite_band:str`. Composite = worst-of (max score / highest band).
- `ImpactMetrics(Base)` — `project_id` PK→projects.id CASCADE; all nullable so both asset types fit one table:
  `generation_gwh:float?  avoided_emissions_tco2:float?` (solar) ·
  `carbon_stock_tco2:float?  carbon_band:str?  assurance:str?` (mangrove) ·
  `co2_intensity_value:float?  co2_intensity_unit:str?` ·
  `build_year:int?  financing_year:int?  additionality_verdict:str?`.
- Add both as `relationship` off `Project` (like the other dossier sections) OR fetch in `services/projects.get_dossier`.

## STEP 2 — Pydantic schema (`app/schemas/project.py`)
Add sub-models + attach to `Dossier`:
```
class HazardScore(BaseModel): score:int; band:str
class PhysicalRisk(BaseModel): fire:HazardScore; flood:HazardScore; degradation:HazardScore; composite:HazardScore
class Impact(BaseModel):
    generation_gwh:float|None=None; avoided_emissions_tco2:float|None=None
    carbon_stock_tco2:float|None=None; carbon_band:str|None=None; assurance:str|None=None
    co2_intensity_value:float|None=None; co2_intensity_unit:str|None=None
    build_year:int|None=None; financing_year:int|None=None; additionality_verdict:str|None=None
# Dossier: physical_risk: PhysicalRisk|None = None ; impact: Impact|None = None
```

## STEP 3 — seeder (`scripts/seed.py`)
In `seed_project`, read `fx.get("metrics")` and merge PhysicalHazards + ImpactMetrics rows (mirror the Disclosure/Confidence merge pattern). Null-safe.

## STEP 4 — seed data (`seed_data/projects/*.json`) — authored, plausible, honestly labeled
Add a `metrics` block to each asset. Suggested values:

**nur_navoi_solar** (100 MW, Uzbekistan desert):
```
"metrics": {
  "physical_risk": { "fire":{"score":15,"band":"Low"}, "flood":{"score":12,"band":"Low"},
                     "degradation":{"score":8,"band":"Low"}, "composite":{"score":15,"band":"Low"} },
  "impact": { "generation_gwh":268, "avoided_emissions_tco2":150000,
              "co2_intensity_value":1500, "co2_intensity_unit":"tCO2e/MW/yr",
              "build_year":2021, "financing_year":2020, "additionality_verdict":"consistent" }
}
```
(generation ≈ claimed 270; avoided ≈ 268 GWh × ~0.56 tCO2/MWh Uzbek grid ≈ 150k, near the disclosed 153k; build 2021 > financing 2020 → additionality consistent.)

**mikoko_pamoja** (117 ha mangrove, Kenya coast):
```
"metrics": {
  "physical_risk": { "fire":{"score":9,"band":"Low"}, "flood":{"score":36,"band":"Medium"},
                     "degradation":{"score":10,"band":"Low"}, "composite":{"score":36,"band":"Medium"} },
  "impact": { "carbon_stock_tco2":9880, "carbon_band":"±50% (Tier-1)", "assurance":"Moderate",
              "co2_intensity_value":84, "co2_intensity_unit":"tCO2e/ha",
              "build_year":2014, "financing_year":2013, "additionality_verdict":"consistent" }
}
```

## STEP 5 — frontend
- `frontend/src/lib/types.ts`: add `PhysicalRisk`, `Impact` to the `Dossier` type.
- **Confidence screen** (`app/projects/[id]/confidence/page.tsx`): add two `Card`s below the rating —
  - **Physical risk**: fire / flood / degradation rows + a composite `Badge` (reuse `riskTone`/`Badge`/`RiskBar`; band → tone). Explains the single risk score.
  - **Impact**: asset-type-aware — solar shows generation (GWh/yr) + avoided emissions (tCO2e/yr); mangrove shows carbon stock (tCO2e) + band + assurance. Plus additionality (build vs financing year → verdict). Use `Stat`/mono tabular numbers; label modeled values honestly.
- **Portfolio** (`app/portfolio/page.tsx`): promote 1–2 metrics to the KPI tile row (e.g. portfolio avoided emissions total, or worst composite hazard). Cross-asset CO₂: compute per-MW intensity spread across capacity assets on the portfolio page (with only one solar asset today, show intensity + note "single capacity asset — no spread yet").
- No em dashes; no "stub"/demo language; label modeled metrics as modeled.

## STEP 6 — verify + ship
- Re-seed; gates `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`.
- Playwright: Confidence (both assets) shows the two new cards with correct per-type metrics + composite hazard; portfolio KPIs updated; both themes; 0 console errors; no clipped text (rerun the detector); no em dashes.
- Add light RTL tests if new components are extracted. Commit (code → review marker) + seed (data, free) + push. Update ledger/memory.

## Notes / honesty guardrails
- All values AUTHORED (no real GEE run) — keep labels honest ("modeled"), keep the `co2_intensity_unit` explicit, don't imply metered precision.
- Cross-asset CO₂ + additionality are partially constrained by having only 2 historical assets (one solar, one mangrove) — per-MW cross-asset spread needs ≥2 capacity assets; note this rather than fabricating a comparison.
