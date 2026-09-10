"""Vector outputs — AOI (and later risk zones) as GeoJSON.

Echoes the input AOI as a GeoJSON Feature with area_hectares added, ready for
the frontend / hand-off. Risk-zone classification is a later addition.
"""

import ee


def aoi_feature(aoi, area_ha: float) -> dict:
    """The AOI polygon as a GeoJSON Feature dict, with area_hectares."""
    return ee.Feature(aoi, {"area_hectares": round(area_ha, 1)}).getInfo()
