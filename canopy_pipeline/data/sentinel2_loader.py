"""Sentinel-2 MSI (L2A) loader — all in Google Earth Engine.

(The spec names SentinelHub here; per the Master Guide we do everything in GEE,
so this loads the analysis-ready COPERNICUS/S2_SR_HARMONIZED collection.)
"""

import ee

from ..preprocessing.cloud_masking import mask_s2
from ..preprocessing.normalization import to_reflectance
from ..preprocessing.clipping import clip_to_aoi

COLLECTION = "COPERNICUS/S2_SR_HARMONIZED"


def load_collection(aoi, window, cloud_pct):
    """Filtered raw scene collection over the AOI + date window."""
    start, end = window
    return (ee.ImageCollection(COLLECTION)
            .filterBounds(aoi).filterDate(start, end)
            .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", cloud_pct)))


def build_composite(aoi, window, cloud_pct):
    """Cloud-masked, reflectance-scaled, clipped median composite.

    Returns (composite image, scene count).
    """
    col = load_collection(aoi, window, cloud_pct)
    n = col.size().getInfo()
    print(f"  S2 {window[0]}..{window[1]}: {n} scenes")
    clean = col.map(mask_s2).map(to_reflectance)
    return clip_to_aoi(clean.median(), aoi), n
