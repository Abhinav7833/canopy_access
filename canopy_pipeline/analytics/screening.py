"""Screening verdict + confidence + one-line finding.

A few transparent if-statements — defensible in Q&A. Branches on asset type:
vegetation assets (forest/mangrove) are judged on NDVI + change; non-vegetation
assets (solar/wind) can't use NDVI, so they get a build/change-based partial
verdict (spec §7.3).
"""

from .. import config

VEG_ASSETS = ("forest_restoration", "mangrove", "reforestation")


def is_vegetation(asset_type: str) -> bool:
    return asset_type in VEG_ASSETS


def confidence(n_scenes: int, coverage: float = 1.0) -> float:
    """Heuristic 0-1 index from scene count, tempered by valid-data coverage.

    `coverage` is the fraction of the AOI that had usable (non-cloud) pixels in
    the after composite — so a run with few clear pixels is scored lower even if
    it had enough scenes. (NDVI temporal variance can be folded in later.)
    """
    base = (0.87 if n_scenes >= 6
            else 0.6 if n_scenes >= config.MIN_SCENES else 0.3)
    cov = 1.0 if coverage is None else min(1.0, max(0.0, coverage))
    return round(base * (0.5 + 0.5 * cov), 2)   # low coverage drags it down


def status(asset_type, trend, pct_gain, pct_loss, n_scenes,
           significant=True) -> str:
    """`trend` is the ROBUST trend over the window (annual slope x span), not the
    two-point endpoint delta. `significant` is False when that trend does not
    exceed the series' interannual variability — a noisy near-zero trend is then
    treated as "no trend", not as growth or decline."""
    if n_scenes < config.MIN_SCENES:
        return "Insufficient data"
    if not is_vegetation(asset_type):
        # non-vegetation asset; MRV limited -> partial by design (§7.3)
        return "Partially consistent"
    # No trend distinguishable from year-to-year noise -> can't confirm either way.
    if not significant:
        return "Partially consistent"
    # Clear, sustained degradation -> inconsistent, whatever the change magnitude.
    if trend < -0.15:
        return "Inconsistent"
    # Mild decline: worrying only when driven by actual vegetation LOSS
    # (not by gain — total churn includes greening).
    if trend < -0.05:
        return "Inconsistent" if pct_loss > 15 else "Partially consistent"
    # Stable or improving vegetation. Real loss pockets are still worth flagging.
    if pct_loss > 15:
        return "Partially consistent"
    return "Consistent"


# Assurance-aligned phrasing (ISAE 3000 / ISSA 5000). EO alone supports
# limited-assurance language — a negative "nothing came to our attention" form.
ASSURANCE = {
    "Consistent":
        "Based on the evidence, nothing came to our attention indicating the "
        "observed change is inconsistent with the stated activity. "
        "(limited assurance)",
    "Partially consistent":
        "Some indicators are consistent; others could not be corroborated from "
        "Earth observation alone and warrant human review.",
    "Inconsistent":
        "The evidence indicates observed change not consistent with the stated "
        "activity — recommend investigation.",
    "Insufficient data":
        "Insufficient cloud-free / valid observations to form a conclusion.",
}


def assurance_statement(status):
    return ASSURANCE.get(status, "")


def main_finding(asset_type, ndvi_slope, significant, pct_gain, pct_loss,
                 sar_delta, build_detected, build_year=None) -> str:
    if not is_vegetation(asset_type):
        d = f"{sar_delta:+.1f} dB" if sar_delta is not None else "n/a"
        if build_detected:
            yr = f" around {build_year}" if build_year else ""
            return (f"Structures detected{yr}: radar backscatter {d} "
                    f"(construction / operation signal).")
        return f"No structural change: radar backscatter {d}."
    slope = ndvi_slope or 0.0
    if not significant:
        trend_txt = (f"NDVI stable ({slope:+.3f}/yr, within interannual "
                     f"variability)")
    elif slope > 0:
        trend_txt = f"NDVI rising ({slope:+.3f}/yr)"
    else:
        trend_txt = f"NDVI declining ({slope:+.3f}/yr)"
    return (f"{trend_txt}; {pct_gain:.0f}% gain / {pct_loss:.0f}% loss "
            f"within window.")
