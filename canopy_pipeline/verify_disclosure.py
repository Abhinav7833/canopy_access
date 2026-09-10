"""Path B — disclosure-only entry point (additive; does NOT modify Path A).

If you already have coordinates/AOI, keep using `run_pipeline(req)` directly —
that path is untouched. This module is only for the case where you start from a
*disclosure* and have no coordinates:

    claims  ->  resolve_candidate (GEM)  ->  AOI  ->  run_pipeline (UNCHANGED)

Graceful degradation is built in: the AOI comes from the best source available
(real OSM/Catastro footprint > GEM point box), and every fallback is labelled so
a missing source downgrades confidence instead of crashing.
"""
import json
import os

from .matching import load_gem_solar, resolve_candidate

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_FOOTPRINTS = os.path.join(_ROOT, "handover", "pizarro_nunez_aois.geojson")


# ---- AOI resolution (graceful: footprint > GEM point box) -------------------

def _bbox_ring(coords_iter):
    xs = [c[0] for c in coords_iter]
    ys = [c[1] for c in coords_iter]
    w, e, s, n = min(xs), max(xs), min(ys), max(ys)
    return [[[w, n], [e, n], [e, s], [w, s], [w, n]]]


def _all_coords(geom):
    t = geom["type"]
    if t == "Polygon":
        return [pt for ring in geom["coordinates"] for pt in ring]
    if t == "MultiPolygon":
        return [pt for poly in geom["coordinates"] for ring in poly for pt in ring]
    return []


def _box_from_point(lat, lon, area_ha):
    # square box whose area ~ area_ha, centred on the GEM point (approximate AOI)
    side_m = (max(area_ha, 50) * 1e4) ** 0.5
    half = side_m / 2 / 111000.0
    return [[[lon - half, lat + half], [lon + half, lat + half],
             [lon + half, lat - half], [lon - half, lat - half],
             [lon - half, lat + half]]]


def _resolve_aoi(candidate, claims, footprints_path=_FOOTPRINTS):
    """Return (aoi_coords_for_pipeline, footprint_geometry, assurance, area_ha)."""
    asset_id = claims.get("asset_id")
    gem_id = candidate.get("gem_location_id")
    if footprints_path and os.path.exists(footprints_path):
        fc = json.load(open(footprints_path))
        for f in fc["features"]:
            p = f["properties"]
            if p.get("asset_id") == asset_id or p.get("gem_location_id") == gem_id:
                geom = f["geometry"]
                # existing build_aoi expects a single polygon ring; use the
                # footprint ring for a Polygon, its bbox for a MultiPolygon.
                if geom["type"] == "Polygon":
                    ring = geom["coordinates"]
                else:
                    ring = _bbox_ring(_all_coords(geom))
                return ring, geom, "observed-footprint (OSM)", p.get("observed_area_ha")
    # fallback: approximate box from the GEM point
    cen = candidate.get("candidate_centroid", {})
    lat, lon = cen.get("lat"), cen.get("lon")
    area = (claims.get("claims", {}).get("area_ha", {}) or {}).get("value", 200)
    if lat is None or lon is None:
        return None, None, "unresolved — no footprint and no GEM point", None
    return _box_from_point(lat, lon, area), None, "approximate — GEM point box (no footprint)", None


# ---- request adapter (to the EXISTING pipeline's req shape) ------------------

def _year(v):
    try:
        return int(str(v)[:4])
    except (TypeError, ValueError):
        return None


def _build_request(claims, aoi_coords):
    c = claims.get("claims", {})
    fin = _year((c.get("financing_date") or {}).get("value"))
    before_y = (fin - 1) if fin else 2019
    return {
        "analysis_id": claims.get("asset_id"),
        "analysis_type": "risk_only",
        "asset_type": "solar",           # Path A branches on this exactly as before
        "country": claims.get("country"),  # selects the correct grid emission factor
        "aoi_coords": aoi_coords,
        "before": (f"{before_y}-05-01", f"{before_y}-09-30"),
        "after": ("2024-05-01", "2024-09-30"),
        "cloud_pct": 20,
        "capacity_mw": (c.get("capacity_mwp") or {}).get("value"),
        "reported_gwh_yr": (c.get("generation_gwh_yr") or {}).get("value"),
        "reported_tco2_avoided_yr": (c.get("co2_avoided_tpy") or {}).get("value"),
    }


# ---- orchestrator -----------------------------------------------------------

def verify_disclosure(claims: dict, reference_df=None, run=None,
                      footprints_path=_FOOTPRINTS) -> dict:
    """Disclosure -> localised AOI -> (optional) existing pipeline run.

    `run` is the existing `run_pipeline` callable, injected so this module never
    imports Earth Engine unless you actually run the EO stage. If `run` is None,
    returns everything up to (and including) the request handed to Path A —
    useful for the precompute-offline demo.
    """
    if reference_df is None:
        country = claims.get("country")
        # aggregate phase-rows into whole plants so a disclosed TOTAL capacity
        # matches the summed phases, not just the biggest single phase.
        reference_df = load_gem_solar(country=country, aggregate=True)

    candidate = resolve_candidate(claims, reference_df)
    aoi_coords, footprint, aoi_assurance, area_ha = _resolve_aoi(
        candidate, claims, footprints_path)
    request = _build_request(claims, aoi_coords) if aoi_coords else None

    result = {
        "asset_id": claims.get("asset_id"),
        "resolution": {
            "match_score": candidate.get("match_score"),
            "margin": candidate.get("margin"),
            "matched_fields": candidate.get("matched_fields"),
            "confidence_label": candidate.get("confidence_label"),
            "gem_location_id": candidate.get("gem_location_id"),
            "centroid": candidate.get("candidate_centroid"),
            "source": candidate.get("source"),
        },
        "aoi": {"assurance": aoi_assurance, "observed_area_ha": area_ha,
                "has_footprint": footprint is not None},
        "request": request,
        "observed": None,
        "status": "resolved" if request else "unresolved",
    }
    if request and run is not None:
        observed = run(request)   # <-- EXISTING run_pipeline, unchanged
        # the pipeline runs on a single AOI (a bounding box for a multi-block site);
        # attach the true MEASURED footprint area so the scale check uses the panels,
        # not the box. General: for a single-polygon plant this equals the AOI area.
        if observed and area_ha is not None and observed.get("metadata"):
            observed["metadata"]["footprint_area_hectares"] = area_ha
        result["observed"] = observed
        result["status"] = "completed"
    return result
