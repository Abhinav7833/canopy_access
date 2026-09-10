"""Annual time-series helpers — treat metrics as trajectories, not endpoints.

Instead of only comparing a first date vs a last date, we sample one composite
per year (the SAME season each year, to avoid seasonal bias) and fit a trend
through the whole series. A single cloudy/anomalous year can't then dominate the
conclusion, and we can see the shape of the change, not just its endpoints.
"""

import ee

from ..data.sentinel2_loader import build_composite
from ..indices.ndvi import ndvi


def ndvi_timeline(aoi, years, season, cloud_pct):
    """Mean NDVI per year -> [{year, ndvi, n}, ...].

    `season` is a ("-MM-DD", "-MM-DD") pair applied to every year so each point
    is measured in the same season.
    """
    out = []
    for y in years:
        img, n = build_composite(aoi, (f"{y}{season[0]}", f"{y}{season[1]}"),
                                 cloud_pct)
        if n == 0:
            out.append({"year": y, "ndvi": None, "n": 0})
            continue
        val = ndvi(img).reduceRegion(
            ee.Reducer.mean(), aoi, scale=10, maxPixels=1e9).get("NDVI").getInfo()
        out.append({"year": y,
                    "ndvi": round(val, 3) if val is not None else None, "n": n})
    return out


def slope_per_year(series, key="ndvi"):
    """Least-squares slope (units of `key` per year) through the series.

    Positive = improving over time; negative = declining. More robust than
    end-minus-start because it uses every year.
    """
    pts = [(s["year"], s[key]) for s in series if s.get(key) is not None]
    if len(pts) < 2:
        return None
    n = len(pts)
    sx = sum(x for x, _ in pts)
    sy = sum(y for _, y in pts)
    sxx = sum(x * x for x, _ in pts)
    sxy = sum(x * y for x, y in pts)
    denom = n * sxx - sx * sx
    return None if denom == 0 else round((n * sxy - sx * sy) / denom, 4)


def series_std(series, key="ndvi"):
    """Interannual scatter (sample std) of the series values.

    Used as a noise floor: a fitted trend is only treated as a real signal when
    the total change it implies exceeds this year-to-year variability. Guards
    against reading a slope out of a noisy series (e.g. one outlier year).
    """
    vals = [s[key] for s in series if s.get(key) is not None]
    if len(vals) < 2:
        return None
    m = sum(vals) / len(vals)
    var = sum((v - m) ** 2 for v in vals) / (len(vals) - 1)
    return round(var ** 0.5, 4)
