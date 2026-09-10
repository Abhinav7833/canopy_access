"""Bi-temporal NDVI change detection.

Subtract before-NDVI from after-NDVI per pixel: negative = loss, positive =
gain. Threshold the magnitude into a binary change mask and measure the % of
AOI that changed. Works for vegetation loss AND for build/land-cover change.
"""

import ee

from .. import config


def detect(nd_before, nd_after, aoi, threshold=None):
    """Bi-temporal NDVI change, split into gain vs loss.

    Returns (signed dNDVI image, binary change mask, % changed, % gained, % lost).
    Reporting gain and loss separately means growth is never mistaken for loss.
    """
    threshold = config.CHANGE_NDVI_THRESHOLD if threshold is None else threshold
    diff = nd_after.subtract(nd_before).rename("dNDVI")
    change = diff.abs().gt(threshold).rename("change")
    gain = diff.gt(threshold).rename("gain")            # vegetation increased
    loss = diff.lt(-threshold).rename("loss")           # vegetation decreased
    stacked = change.addBands(gain).addBands(loss)
    m = stacked.reduceRegion(
        ee.Reducer.mean(), aoi, scale=10, maxPixels=1e9).getInfo()
    pct  = (m.get("change") or 0.0) * 100
    pgain = (m.get("gain") or 0.0) * 100
    ploss = (m.get("loss") or 0.0) * 100
    return diff, change, pct, pgain, ploss
