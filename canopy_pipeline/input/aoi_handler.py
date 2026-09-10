"""AOI handling — GeoJSON polygon -> ee.Geometry, plus area check.

Coords are always [longitude, latitude] (lon first — the classic trip-up).
"""

import ee


def box_from_center(lon: float, lat: float, half_deg: float) -> list:
    """A square AOI ring of side 2*half_deg degrees around a centre point.

    Handy for starting from a Source-Pack centre coordinate before the exact
    polygon is confirmed.
    """
    h = half_deg
    return [[
        [lon - h, lat + h], [lon + h, lat + h],
        [lon + h, lat - h], [lon - h, lat - h],
        [lon - h, lat + h],
    ]]


def build_aoi(req: dict) -> ee.Geometry:
    """Request -> ee.Geometry.Polygon."""
    return ee.Geometry.Polygon(req["aoi_coords"])


def area_hectares(aoi: ee.Geometry) -> float:
    """AOI area in hectares. area() returns m^2; /1e4 -> ha."""
    return aoi.area(maxError=1).divide(1e4).getInfo()
