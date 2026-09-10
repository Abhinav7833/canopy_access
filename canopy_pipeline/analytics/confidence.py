"""Project confidence — the single headline number (the product).

The brief: "given a standard disclosure, we localise the financed asset and follow
its build progress with X% confidence." This fuses two things into one figure:

  localisation confidence   (are we sure we found the right asset?)
        ×
  build-progress confidence (is it built, on schedule, at the stated scale?)

Both must hold, so we multiply — a shaky match OR an off-track build pulls the
number down. Output is a %, a status, and the one demonstrable sentence.
"""

# how much each cross-check counts toward "on-track" (build/timing and scale lead)
_CHECK_WEIGHT = {
    "build_onset_vs_financing": 0.40,   # additionality / timing — the key one
    "footprint_area_ha":        0.30,   # built out to the stated scale?
    "generation_gwh_yr":        0.15,
    "co2_avoided_tpy":          0.15,
}
_VERDICT_SCORE = {
    "consistent": 1.0, "partially_consistent": 0.6,
    "insufficient_data": 0.5, "inconsistent": 0.0,
}
_LOC_SCORE = {"high": 0.92, "medium": 0.65, "low": 0.30}


def project_confidence(resolution: dict, cross_check: list) -> dict:
    # localisation: from the match confidence label ("low — ..." -> "low")
    label = str(resolution.get("confidence_label", "low")).split()[0]
    loc = _LOC_SCORE.get(label, 0.30)

    # build progress: weighted blend of the cross-check verdicts
    num = den = 0.0
    for c in cross_check or []:
        w = _CHECK_WEIGHT.get(c.get("claim"), 0.1)
        num += w * _VERDICT_SCORE.get(c.get("verdict"), 0.5)
        den += w
    build = (num / den) if den else 0.5

    overall = round(loc * build, 2)
    status = ("on-track" if overall >= 0.70 else
              "partial — watch" if overall >= 0.45 else
              "off-track — investigate")
    return {
        "localisation_confidence": round(loc, 2),
        "build_progress_confidence": round(build, 2),
        "on_track_confidence": overall,
        "on_track_pct": f"{round(overall * 100)}%",
        "status": status,
    }


def headline_sentence(asset_name: str, conf: dict, resolution: dict) -> str:
    return (f"Given the {asset_name} disclosure, we localised the financed asset "
            f"({str(resolution.get('confidence_label','?')).split()[0]} confidence) "
            f"and its build is {conf['status']} — "
            f"{conf['on_track_pct']} confidence.")
