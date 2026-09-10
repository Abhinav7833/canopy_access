"""Raster outputs.

Two kinds:
  - rgb_preview_url(): an INSTANT PNG thumbnail (no batch wait) for the UI.
  - export_geotiffs(): async batch COG GeoTIFF tasks. This PRODUCES the files
    (to Google Drive here) and returns the task handles / paths.

The actual upload to production cloud storage + deployment is Cem's job
(spec §8.2: "Uploads the files Luna produces"). This module stops at producing
files and handing back references — the seam where Cem plugs in.
"""

import ee


def rgb_preview_url(img, aoi) -> str:
    """Instant true-colour PNG preview URL."""
    vis = {"bands": ["B4", "B3", "B2"], "min": 0, "max": 0.3}
    return img.visualize(**vis).getThumbURL({"region": aoi, "dimensions": 512})


def geotiff_url(image, aoi):
    """Immediate download URL for a single-band GeoTIFF of the AOI.

    Uses getDownloadURL (works for small demo AOIs). Returns None on failure so
    a URL hiccup never crashes the run.
    """
    try:
        return image.getDownloadURL({
            "region": aoi, "scale": 10, "crs": "EPSG:4326",
            "format": "GEO_TIFF"})
    except Exception as e:            # pragma: no cover - network/size guard
        print("  geotiff_url failed:", e)
        return None


def export_geotiffs(analysis_id: str, layers: dict, aoi) -> dict:
    """Start async COG exports. `layers` = {name: ee.Image}. Poll .status()."""
    tasks = {}
    for name, image in layers.items():
        t = ee.batch.Export.image.toDrive(
            image=image, description=f"{analysis_id}_{name}",
            folder="canopy_demo", region=aoi, scale=10,
            crs="EPSG:4326", maxPixels=1e9)
        t.start()
        tasks[name] = t
    return tasks
