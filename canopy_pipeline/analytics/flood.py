"""Flood — two documented, complementary metrics.

  1. OBSERVED flood  (did it flood in the window?)  — Sentinel-1 VH with Otsu
     automatic thresholding (UN-SPIDER Recommended Practice, Otsu 1979),
     differenced against JRC permanent water, with an optical NDWI cross-check.
  2. Flood EXPOSURE  (could it flood?)  — WRI Aqueduct 100-yr depth -> Huizinga
     depth-damage (handled in risk_scoring / reference).

These answer different questions, so both are reported — not merged.
"""

import ee

from ..data.reference import permanent_water
from ..indices.ndwi import ndwi


def otsu_threshold(histogram):
    """Otsu (1979) optimal threshold from a band histogram — the value that
    maximises between-class variance. Standard GEE implementation."""
    histogram = ee.Dictionary(histogram)
    counts = ee.Array(histogram.get("histogram"))
    means = ee.Array(histogram.get("bucketMeans"))
    size = means.length().get([0])
    total = counts.reduce(ee.Reducer.sum(), [0]).get([0])
    sums = means.multiply(counts).reduce(ee.Reducer.sum(), [0]).get([0])
    mean = sums.divide(total)
    indices = ee.List.sequence(1, size)

    def bss(i):
        a_counts = counts.slice(0, 0, i)
        a_count = a_counts.reduce(ee.Reducer.sum(), [0]).get([0])
        a_means = means.slice(0, 0, i)
        a_mean = a_means.multiply(a_counts).reduce(
            ee.Reducer.sum(), [0]).get([0]).divide(a_count)
        b_count = total.subtract(a_count)
        b_mean = sums.subtract(a_count.multiply(a_mean)).divide(b_count)
        return a_count.multiply(a_mean.subtract(mean).pow(2)).add(
            b_count.multiply(b_mean.subtract(mean).pow(2)))

    bss_values = indices.map(lambda i: bss(ee.Number(i)))
    return means.sort(ee.Array(bss_values)).get([-1])


def observed_flood_fraction(aoi, window, optical_img=None):
    """Fraction of AOI (0-1) flagged as NEW flooding in the window."""
    start, end = window
    col = (ee.ImageCollection("COPERNICUS/S1_GRD")
           .filterBounds(aoi).filterDate(start, end)
           .filter(ee.Filter.eq("instrumentMode", "IW"))
           .filter(ee.Filter.listContains(
               "transmitterReceiverPolarisation", "VH"))
           .select("VH"))
    if col.size().getInfo() == 0:
        return 0.0
    vh = col.mean().clip(aoi)
    hist = vh.reduceRegion(
        ee.Reducer.histogram(255), aoi, scale=30, maxPixels=1e9).get("VH")
    thr = otsu_threshold(hist)
    water = vh.lt(ee.Image.constant(ee.Number(thr)))          # radar-dark = water
    water = water.And(permanent_water(aoi).Not())            # exclude permanent
    if optical_img is not None:
        water = water.And(ndwi(optical_img).gt(0))           # optical must agree
    frac = water.rename("flood").reduceRegion(
        ee.Reducer.mean(), aoi, scale=10, maxPixels=1e9).get("flood").getInfo()
    return frac if frac is not None else 0.0
