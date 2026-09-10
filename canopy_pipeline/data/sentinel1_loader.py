"""Sentinel-1 SAR (GRD) loader — flood/water layer, all in GEE.

GEE's S1 collection is already orbit-corrected and calibrated to backscatter
(dB), so no manual SNAP/Gamma0 step. Smooth water reflects radar away -> low
VV backscatter -> we threshold it as water.
"""

import ee

from .. import config
from ..indices.ndwi import ndwi
from ..preprocessing.clipping import clip_to_aoi


def _vv_collection(aoi, window):
    """Filtered Sentinel-1 VV backscatter collection over the AOI + window."""
    start, end = window
    return (ee.ImageCollection("COPERNICUS/S1_GRD")
            .filterBounds(aoi).filterDate(start, end)
            .filter(ee.Filter.eq("instrumentMode", "IW"))
            .filter(ee.Filter.listContains(
                "transmitterReceiverPolarisation", "VV"))
            .select("VV"))


def water_layer(aoi, window, optical_img=None, threshold_db=None):
    """Return (water_mask image, scene count) over the window.

    water = radar-dark (smooth) AND, if an optical composite is given, optically
    wet (NDWI > 0). Requiring both sensors to agree stops dry, smooth desert
    sand — which is also radar-dark — from being mislabelled as water.
    """
    threshold_db = config.SAR_WATER_DB if threshold_db is None else threshold_db
    col = _vv_collection(aoi, window)
    n = col.size().getInfo()
    vv = clip_to_aoi(col.mean(), aoi)
    water = vv.lt(threshold_db)
    if optical_img is not None:
        water = water.And(ndwi(optical_img).gt(0))   # optical must agree
    return water.rename("water"), n


def mean_vv(aoi, window):
    """Mean VV backscatter (dB) over the AOI for a window, plus scene count."""
    col = _vv_collection(aoi, window)
    n = col.size().getInfo()
    if n == 0:
        return None, 0
    val = clip_to_aoi(col.mean(), aoi).reduceRegion(
        ee.Reducer.mean(), aoi, scale=10, maxPixels=1e9).get("VV").getInfo()
    return val, n


def backscatter_change(aoi, before, after):
    """Structural-change signal for build detection.

    Hard structures (solar panels, mounts, buildings) reflect radar back
    strongly, so constructing them RAISES the AOI's mean VV backscatter. A
    positive delta (after - before, in dB) indicates new structures appeared —
    a signal NDVI can't see, since panels and bare ground are both low-NDVI.
    """
    b, nb = mean_vv(aoi, before)
    a, na = mean_vv(aoi, after)
    delta = (a - b) if (a is not None and b is not None) else None
    return {"vv_before": b, "vv_after": a, "vv_delta": delta, "n": min(nb, na)}


def backscatter_timeline(aoi, years, season=("-04-01", "-09-30")):
    """Mean VV backscatter per year — a construction timeline.

    Returns [{year, vv, n}, ...]. A step-up in backscatter dates when the
    structures appeared, so we can check the observed build year against a
    project's self-reported operational date.
    """
    out = []
    for y in years:
        v, n = mean_vv(aoi, (f"{y}{season[0]}", f"{y}{season[1]}"))
        out.append({"year": y, "vv": round(v, 2) if v is not None else None,
                    "n": n})
    return out


def detect_build_year(timeline, threshold_db):
    """First year whose backscatter CHANGES threshold_db from the baseline year,
    in either direction — i.e. the year the structures most likely appeared.

    Direction is terrain-dependent, so we date on magnitude, not sign: hard
    structures RAISE backscatter over smooth ground (e.g. desert), but smooth
    solar panels LOWER it over rougher ground (e.g. farmland). Keying on a rise
    only would miss every panel field built on non-desert terrain."""
    base = timeline[0]["vv"] if timeline else None
    if base is None:
        return None
    for s in timeline[1:]:
        if s["vv"] is not None and abs(s["vv"] - base) >= threshold_db:
            return s["year"]
    return None


def water_fraction(aoi, window, optical_img=None):
    """Fraction of AOI (0-1) that reads as water, plus scene count."""
    water, n = water_layer(aoi, window, optical_img=optical_img)
    if n == 0:
        return 0.0, 0
    frac = water.reduceRegion(
        ee.Reducer.mean(), aoi, scale=10, maxPixels=1e9).get("water").getInfo()
    return (frac or 0.0), n
