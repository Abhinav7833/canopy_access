"""Physical risk — IPCC AR6 Hazard × Exposure × Vulnerability (Score A).

**Double materiality: the two directions are scored separately and never merged.**
A single number over both is undefined — it rises when the asset is endangered AND
when the asset causes harm, and those imply opposite actions (harden/insure vs
remediate). So this module returns two composites:

  Environment → asset (financial materiality — "what danger is nature posing to it?")
  - fire  : Fosberg FFWI (hazard) × fuel presence (vulnerability)
  - flood : Aqueduct 100-yr depth (hazard) × Huizinga depth-damage (vulnerability)
  → `hazard_composite`

  Asset → environment (impact materiality — "what harm is the project doing?")
  - degradation : observed vegetation loss inside/around the footprint
  → `effect_composite`

Each hazard is scored as Hazard × Exposure × Vulnerability, with **Exposure = the
asset footprint (the AOI is the financed asset, so it is present = 1)**, per the
methodology's §1. Community exposure (GHSL built-up) and socioeconomic
vulnerability (INFORM / ND-GAIN) are the Score B overlay, reported separately.

Observed flooding (Otsu, from flood.py) is reported alongside as a separate
"did it flood?" metric — not merged into the forward-looking risk.
"""

# JRC / Huizinga (2017) global depth-damage curve: flood depth (m) -> % loss.
_HUIZINGA = [(0, 0.0), (0.5, 0.25), (1, 0.40), (1.5, 0.50),
             (2, 0.60), (3, 0.75), (4, 0.85), (6, 1.0)]

ASSET_EXPOSURE = 1.0   # the AOI IS the financed asset -> exposure present


def band_for(score_0_100: int) -> str:
    """Shared banding, so both materiality directions read on the same scale."""
    return ("Low" if score_0_100 < 25 else "Medium" if score_0_100 < 50
            else "High" if score_0_100 < 75 else "Critical")


def huizinga_damage(depth_m):
    """Documented depth-damage: flood depth (m) -> damage fraction (0-1)."""
    if depth_m <= 0:
        return 0.0
    for (x0, y0), (x1, y1) in zip(_HUIZINGA, _HUIZINGA[1:]):
        if depth_m <= x1:
            return y0 + (y1 - y0) * (depth_m - x0) / (x1 - x0)
    return 1.0


def score(dnbr, observed_flood_frac, pct_loss,
          flood_depth_m, ffwi, fuel_ndvi, community_exposure):
    # --- Fire: FFWI hazard × exposure × fuel-presence vulnerability ---
    fire_hazard = min(1.0, ffwi / 100.0)
    fuel = max(0.0, min(1.0, (fuel_ndvi or 0) / 0.3))     # vulnerability = fuel
    fire = int(round(fire_hazard * ASSET_EXPOSURE * fuel * 100))
    # --- Flood: Aqueduct depth hazard × exposure × Huizinga vulnerability ---
    flood_vuln = huizinga_damage(flood_depth_m)
    flood = int(round(1.0 * ASSET_EXPOSURE * flood_vuln * 100))
    # --- Degradation: observed vegetation loss ---
    degradation = int(min(100, max(0, pct_loss)))

    # Two directions, two composites — see the module docstring. Worst hazard drives
    # the risk TO the asset; observed vegetation loss drives the harm BY the asset.
    hazard_composite = max(fire, flood)
    effect_composite = degradation
    return {
        "fire": fire, "flood": flood, "degradation": degradation,
        "hazard_composite": hazard_composite, "hazard_band": band_for(hazard_composite),
        "effect_composite": effect_composite, "effect_band": band_for(effect_composite),
        # documented provenance detail
        "fire_fosberg_ffwi": round(ffwi, 1),
        "fire_severity_dnbr": round(dnbr, 3),
        "flood_depth_100yr_m": round(flood_depth_m, 3),
        "flood_depth_damage_frac": round(flood_vuln, 3),
        "flood_observed_frac": round(observed_flood_frac, 3),
        "asset_exposure": ASSET_EXPOSURE,
        "community_exposure_built_up": round(community_exposure, 4),
    }
