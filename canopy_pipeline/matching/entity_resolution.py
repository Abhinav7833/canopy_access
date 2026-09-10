"""Deterministic entity resolution (WI-3, Path B).

Given a disclosure's attributes (name, capacity, country, developer) — and NO
coordinates — return the best-matching reference asset, with a confidence signal
(the margin to the runner-up). Pure pandas + rapidfuzz. No LLM, no ML. Every
returned field is traceable.

Degrades gracefully: any missing disclosure field is dropped from the score and
the weights renormalise, so a thin disclosure still resolves (at lower confidence)
rather than erroring.
"""
from rapidfuzz import fuzz

# Relative weights; only the fields actually present are used (renormalised).
# region (state/province) is a strong disambiguator between similar nearby plants.
_WEIGHTS = {"name": 0.45, "capacity": 0.25, "region": 0.15,
            "country": 0.10, "developer": 0.05}
_CAP_TOL = 0.20   # capacity within +/-20% counts as a match


def _claim_val(claims, key):
    c = claims.get("claims", {}).get(key)
    return c.get("value") if isinstance(c, dict) else c


def _cap_score(reported, ref_cap):
    """Smooth closeness score: 1.0 at an exact capacity match, declining with the
    relative difference (so 589 MW beats 500 MW for a disclosed 590, even though
    both are within tolerance). >=0.8 (i.e. within ~20%) counts as a match."""
    if reported is None or ref_cap is None or ref_cap == 0:
        return None
    return max(0.0, 1.0 - abs(ref_cap - reported) / reported)


def _row_score(claims, row):
    parts, matched = {}, []
    # name: score against the plant name AND any alt names separately, take the
    # best. Do NOT glue on the phase label ("1", "3", ...) — that stray token was
    # dragging a genuine name match below threshold.
    name = claims.get("name")
    if name:
        nm = name.lower()   # case-insensitive: "de" == "De", "solar" == "Solar"
        cands = [str(row.get(k) or "").lower() for k in ("name", "other_names")]
        parts["name"] = max((fuzz.token_set_ratio(nm, c) for c in cands if c),
                            default=0.0) / 100.0
        if parts["name"] >= 0.85:
            matched.append("name")
    # capacity
    cap = _claim_val(claims, "capacity_mwp") or _claim_val(claims, "capacity_mwac")
    cs = _cap_score(cap, row.get("capacity_mw"))
    if cs is not None:
        parts["capacity"] = cs
        if cs >= 0.8:
            matched.append("capacity")
    # country
    country = claims.get("country")
    if country and row.get("country") is not None:
        ok = country.lower() in str(row["country"]).lower()
        parts["country"] = 1.0 if ok else 0.0
        if ok:
            matched.append("country")
    # region (state / province) — does the GEM state appear in the disclosed region?
    region = claims.get("region")
    if region and row.get("state") is not None and str(row.get("state")):
        ok = str(row["state"]).lower() in region.lower()
        parts["region"] = 1.0 if ok else 0.0
        if ok:
            matched.append("region")
    # developer vs owner/operator
    dev = claims.get("developer")
    if dev:
        owner = f"{row.get('owner') or ''} {row.get('operator') or ''}"
        parts["developer"] = fuzz.partial_ratio(dev.lower(), owner.lower()) / 100.0
        if parts["developer"] >= 0.85:
            matched.append("developer")
    # renormalise weights over present fields
    wsum = sum(_WEIGHTS[k] for k in parts) or 1.0
    score = sum(_WEIGHTS[k] * v for k, v in parts.items()) / wsum
    return score, matched, parts


def resolve_candidate(claims: dict, reference_df) -> dict:
    """Return the best reference match for a disclosure.

    {matched_row, match_score, margin, matched_fields, field_scores,
     candidate_centroid, source, confidence_label}. `margin` = score gap to the
     runner-up (the real confidence signal — a big margin means an unambiguous
     match; a thin margin means "human review").
    """
    scored = []
    for i, row in reference_df.iterrows():
        s, matched, parts = _row_score(claims, row.to_dict())
        scored.append((s, i, matched, parts))
    scored.sort(key=lambda t: t[0], reverse=True)

    if not scored:
        return {"matched_row": None, "match_score": 0.0, "margin": 0.0,
                "matched_fields": [], "confidence_label": "no-candidates"}

    best = scored[0]
    row = reference_df.loc[best[1]].to_dict()
    win_gem = row.get("gem_location_id")
    # runner-up = best-scoring DIFFERENT asset; skip other phases of the SAME plant
    # (same GEM location id), which aren't real ambiguity.
    runner_score = 0.0
    for s, i, _m, _p in scored[1:]:
        if reference_df.loc[i].to_dict().get("gem_location_id") != win_gem:
            runner_score = s
            break
    margin = round(best[0] - runner_score, 3)

    # High confidence when the winner is a strong multi-field match OR clearly
    # ahead of the next DIFFERENT plant. A near-zero margin (many look-alikes)
    # always forces human review, whatever the raw score.
    n_matched = len(best[2])
    if margin < 0.05:
        label = "low — ambiguous, human review"
    elif (best[0] >= 0.90 and n_matched >= 3) or (best[0] >= 0.85 and margin >= 0.15):
        label = "high"
    elif best[0] >= 0.70:
        label = "medium"
    else:
        label = "low — human review"

    return {
        "matched_row": row,
        "match_score": round(best[0], 3),
        "margin": margin,
        "matched_fields": best[2],
        "field_scores": {k: round(v, 3) for k, v in best[3].items()},
        "candidate_centroid": {"lat": row.get("lat"), "lon": row.get("lon")},
        "gem_location_id": row.get("gem_location_id"),
        "location_accuracy": row.get("location_accuracy"),
        "source": row.get("source"),
        "confidence_label": label,
    }
