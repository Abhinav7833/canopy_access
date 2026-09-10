"""Resampling to a common grid.

In GEE, reprojection/resampling happens on demand when you call
reduceRegion(scale=...) or Export(scale=...). For single-sensor Sentinel-2 at
10 m we don't force a reproject (it's costly and unnecessary). This helper is
here for spec completeness and for the multi-sensor case (e.g. aligning SAR to
the optical grid).
"""


def resample_to(img, scale_m=10, crs="EPSG:4326"):
    return img.resample("bilinear").reproject(crs=crs, scale=scale_m)
