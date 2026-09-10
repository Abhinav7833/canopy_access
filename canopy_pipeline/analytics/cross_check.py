"""Cross-check stage (WI-5, Path B) — reported vs observed.

Pits each disclosed claim against the observed/estimated value and emits a
verdict + delta + assurance label. This is the actual *verification* output: not
"here is a number" but "the disclosure says X, we observe Y, and here is how far
apart they are and how much we trust it."

Every check degrades to `insufficient_data` when an input is missing — never
raises. Verdicts use ISAE 3000 / ISSA 5000 limited-assurance phrasing.
"""

VERDICTS = ("consistent", "partially_consistent", "inconsistent", "insufficient_data")

# capacity -> plausible footprint band (ha per MW). Utility PV ~1.5-3 ha/MW.
_HA_PER_MW = (1.5, 3.0)


def _claim(claims, key):
    c = claims.get("claims", {}).get(key)
    return c.get("value") if isinstance(c, dict) else None


def _year(v):
    try:
        return int(str(v)[:4])
    except (TypeError, ValueError):
        return None


def _rec(claim, reported, observed, delta, verdict, assurance, note, confidence=None):
    assert verdict in VERDICTS
    return {"claim": claim, "reported": reported, "observed": observed,
            "delta": delta, "verdict": verdict, "assurance_label": assurance,
            "confidence": confidence, "note": note}


def _check_scale(claims, observed):
    cap = _claim(claims, "capacity_mwp")
    md = observed.get("metadata") or {}
    # prefer the real MEASURED footprint area (sum of the actual polygon blocks)
    # over the AOI area, which for a multi-block site is the bounding box (it counts
    # the empty gaps between blocks). Falls back to the AOI area when no footprint.
    obs_area = md.get("footprint_area_hectares") or md.get("aoi_area_hectares")
    rep_area = _claim(claims, "area_ha")
    if cap is None or obs_area is None:
        return _rec("footprint_area_ha", rep_area, obs_area, None, "insufficient_data",
                    "needs-ground-truth", "Missing capacity or observed area.")
    lo, hi = cap * _HA_PER_MW[0], cap * _HA_PER_MW[1]
    in_band = lo <= obs_area <= hi
    delta = round(obs_area - rep_area, 1) if rep_area else None
    if in_band:
        v, note = "consistent", (
            f"Observed footprint {obs_area:.0f} ha sits within the capacity-implied "
            f"band {lo:.0f}-{hi:.0f} ha ({cap} MW). Nothing came to our attention "
            f"indicating the footprint is inconsistent with the disclosed scale.")
    else:
        v, note = "partially_consistent", (
            f"Observed {obs_area:.0f} ha is outside the capacity-implied band "
            f"{lo:.0f}-{hi:.0f} ha; the difference to the reported {rep_area} ha may be "
            f"exclusion zones / phasing and warrants human review.")
    return _rec("footprint_area_ha", rep_area, round(obs_area, 1), delta, v,
                "observed", note)


def _check_timing(claims, observed):
    """The additionality proxy: did the build come AFTER the financing?"""
    fin = _year(_claim(claims, "financing_date"))
    ev = (observed.get("evidence") or [{}])[0]
    build_onset = ev.get("build_year_estimate") or observed.get("build_year")
    if fin is None or build_onset is None:
        return _rec("build_onset_vs_financing", fin, build_onset, None,
                    "insufficient_data", "needs-ground-truth",
                    "Build-onset year could not be dated from EO in this window "
                    "(the additionality check is only as strong as build-dating).")
    if build_onset >= fin:
        v, note = "consistent", (
            f"Observed build onset ({build_onset}) is at/after the disclosed financing "
            f"year ({fin}) — consistent with new, additional capacity funded by the "
            f"stated use-of-proceeds.")
    else:
        v, note = "inconsistent", (
            f"Observed build onset ({build_onset}) predates the disclosed financing "
            f"year ({fin}) — the capacity may not be additional to the financing; "
            f"recommend investigation.")
    return _rec("build_onset_vs_financing", fin, build_onset, build_onset - fin, v,
                "observed", note)


def _check_band(claims, observed, claim_key, est_lo_key, est_hi_key, label):
    reported = _claim(claims, claim_key)
    gen = ((observed.get("evidence") or [{}])[0]).get("generation_estimate") or {}
    lo, hi = gen.get(est_lo_key), gen.get(est_hi_key)
    if reported is None or lo is None:
        return _rec(claim_key, reported, [lo, hi], None, "insufficient_data",
                    "modelled", f"Missing reported or modelled {label}.")
    # our estimate is a deliberate conservative lower bound; consistent if reported
    # is at or above it (as expected), inconsistent only if reported is far BELOW.
    if reported >= lo * 0.85:
        v, note = "partially_consistent", (
            f"Modelled {label} {lo:.0f}-{hi:.0f} is a conservative lower bound; the "
            f"reported {reported} is consistent with it (EO cannot meter output — this "
            f"corroborates order of magnitude, not the exact figure).")
    else:
        v, note = "inconsistent", (
            f"Reported {label} ({reported}) is materially below even our conservative "
            f"lower-bound estimate ({lo:.0f}-{hi:.0f}) — recommend investigation.")
    return _rec(claim_key, reported, [round(lo), round(hi)],
                round(reported - lo), v, "modelled", note)


def cross_check(claims: dict, observed: dict) -> list:
    """Return the reported-vs-observed record set for one disclosure."""
    if not observed:
        return [_rec("all", None, None, None, "insufficient_data", "needs-ground-truth",
                     "No observed output (pipeline did not run).")]
    return [
        _check_scale(claims, observed),
        _check_timing(claims, observed),
        _check_band(claims, observed, "generation_gwh_yr",
                    "est_gwh_fixed_tilt", "est_gwh_tracking", "generation (GWh/yr)"),
        _check_band(claims, observed, "co2_avoided_tpy",
                    "est_tco2_avoided_fixed", "est_tco2_avoided_tracking",
                    "avoided emissions (tCO2/yr)"),
    ]
