"""Walk-forward backtest (WI-6) — prove the coordinate claim.

Hide the name and the coordinates. From a region-level hint alone
({country, developer, capacity, financing_date}), can the reference-match land on
the RIGHT plant, and can we confirm the build happened after financing? This is
the internal validation the brief demands before we present the localisation claim.

(Abhinav's pixel localiser is stubbed here — it returns the locked WI-1 footprint,
so the geometric IoU is 1.0 by construction; the meaningful score for Luna's
reference layer is 'did we pick the correct plant from a name-less hint'.)
"""
import json
from ..matching import resolve_candidate


def backtest_localisation(claim_path, truth_gem_id, reference_df, build_bundle=None):
    claims = json.load(open(claim_path))
    # region-level hint: DROP the name, keep only attributes a disclosure gives
    hint = {
        "country": claims.get("country"),
        "region": claims.get("region"),
        "developer": claims.get("developer"),
        "claims": {"capacity_mwp": claims.get("claims", {}).get("capacity_mwp")},
    }
    r = resolve_candidate(hint, reference_df)
    localised_correct = (r.get("gem_location_id") == truth_gem_id)

    # timing (from a prior observation bundle, if given)
    timing = None
    if build_bundle:
        for c in build_bundle.get("cross_check", []):
            if c["claim"] == "build_onset_vs_financing":
                timing = c
    return {
        "asset": claims.get("name"),
        "hint_fields": ["country", "region", "developer", "capacity_mwp"],  # NO name, NO coords
        "localised_to_gem": r.get("gem_location_id"),
        "truth_gem": truth_gem_id,
        "localised_correct": localised_correct,
        "match_score": r.get("match_score"),
        "margin": r.get("margin"),
        "confidence": r.get("confidence_label"),
        "iou_vs_locked_footprint": 1.0,   # stub localiser == locked polygon
        "build_timing": (timing or {}).get("verdict"),
        "pass": bool(localised_correct and (timing or {}).get("verdict") == "consistent"),
    }
