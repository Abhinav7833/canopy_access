"""Regenerate the Esri World Imagery Wayback timelapse frames for the demo AOIs.

DEV TOOL — you do NOT need this to run the app. The frames it produces are committed
under ``seed_data/imagery/<project_id>/`` and are copied into the served asset store by
``scripts/seed.py``, so a fresh checkout already ships a working timelapse. Run this only
to refresh or extend the frame set.

Requires:  pip install pillow requests
Usage:     python scripts/pull_wayback.py                # both demo projects
           python scripts/pull_wayback.py nur_navoi_solar

Source: Esri World Imagery Wayback (public archive, no API key). Each frame is stitched
from Web-Mercator tiles (how MapLibre renders) and cropped to the project's ``aoi_coords``
bbox, then saved as a JPEG named ``wayback_<capture-date>_rgb.jpg`` — the ``rgb`` marks it
as an RGB layer and the date is parsed back out by the imagery endpoint.
"""
from __future__ import annotations

import io
import json
import math
import re
import sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT / "seed_data" / "projects"
IMAGERY = ROOT / "seed_data" / "imagery"
CONFIG_URL = "https://s3-us-west-2.amazonaws.com/config.maptiles.arcgis.com/waybackconfig.json"
UA = {"User-Agent": "canopy-wayback/1.0"}
TILE = 256

# Curated years per project — the frames that tell each story (Nur Navoi: desert -> panel
# field; Gazi Bay: a stable mangrove canopy). One Wayback release per year is chosen.
YEARS = {
    "nur_navoi_solar": [2019, 2021, 2022, 2023, 2024, 2026],
    "mikoko_pamoja": [2019, 2020, 2021, 2022, 2023, 2024],
}


def load_releases() -> list[dict]:
    cfg = requests.get(CONFIG_URL, headers=UA, timeout=30).json()
    rows = []
    for num, meta in cfg.items():
        m = re.search(r"(\d{4}-\d{2}-\d{2})", meta.get("itemTitle", ""))
        if m:
            rows.append({"num": int(num), "date": m.group(1), "url": meta["itemURL"]})
    rows.sort(key=lambda r: r["date"])
    return rows


def _ord(d: str) -> int:
    y, m, day = map(int, d.split("-"))
    return y * 372 + m * 31 + day


def pick(releases: list[dict], year: int) -> dict:
    """The release whose capture date is closest to the year's mid-point (Jul 1)."""
    target = _ord(f"{year}-07-01")
    return min(releases, key=lambda r: abs(_ord(r["date"]) - target))


def bbox(coords: list) -> tuple[float, float, float, float]:
    lons = [p[0] for p in coords]
    lats = [p[1] for p in coords]
    return min(lons), min(lats), max(lons), max(lats)


def deg2px(lat: float, lon: float, z: int) -> tuple[float, float]:
    n = 2 ** z
    x = (lon + 180.0) / 360.0 * n
    y = (1.0 - math.asinh(math.tan(math.radians(lat))) / math.pi) / 2.0 * n
    return x, y


def auto_zoom(b: tuple, target_px: int = 1200) -> int:
    w, s, e, n = b
    for z in range(19, 12, -1):
        if (e - w) / 360.0 * (2 ** z) * TILE <= target_px * 1.35:
            return z
    return 17


def fetch_tile(rel: dict, z: int, x: int, y: int) -> Image.Image:
    url = rel["url"].replace("{level}", str(z)).replace("{row}", str(y)).replace("{col}", str(x))
    try:
        r = requests.get(url, headers=UA, timeout=30)
        if r.ok and r.content[:3] in (b"\xff\xd8\xff", b"\x89PN"):
            return Image.open(io.BytesIO(r.content)).convert("RGB")
    except requests.RequestException:
        pass
    return Image.new("RGB", (TILE, TILE), (30, 30, 30))


def render(rel: dict, b: tuple, z: int) -> Image.Image:
    w, s, e, n = b
    x0, y0 = deg2px(n, w, z)  # north-west corner (pixel space)
    x1, y1 = deg2px(s, e, z)  # south-east corner
    xmin, xmax = math.floor(x0), math.floor(x1)
    ymin, ymax = math.floor(y0), math.floor(y1)
    coords = [(tx, ty) for tx in range(xmin, xmax + 1) for ty in range(ymin, ymax + 1)]
    with ThreadPoolExecutor(max_workers=16) as ex:
        tiles = dict(zip(coords, ex.map(lambda c: fetch_tile(rel, z, c[0], c[1]), coords)))
    mosaic = Image.new("RGB", ((xmax - xmin + 1) * TILE, (ymax - ymin + 1) * TILE))
    for (tx, ty), im in tiles.items():
        mosaic.paste(im, ((tx - xmin) * TILE, (ty - ymin) * TILE))
    crop = mosaic.crop(
        (round((x0 - xmin) * TILE), round((y0 - ymin) * TILE),
         round((x1 - xmin) * TILE), round((y1 - ymin) * TILE))
    )
    crop.thumbnail((1600, 1600))
    return crop


def main(argv: list[str]) -> None:
    ids = argv or list(YEARS)
    releases = load_releases()
    for pid in ids:
        fx = json.loads((PROJECTS / f"{pid}.json").read_text(encoding="utf-8"))
        b = bbox(fx["aoi_coords"])
        z = auto_zoom(b)
        dest = IMAGERY / pid
        dest.mkdir(parents=True, exist_ok=True)
        print(f"{pid}: bbox={b} zoom={z}")
        for year in YEARS.get(pid, []):
            rel = pick(releases, year)
            img = render(rel, b, z)
            out = dest / f"wayback_{rel['date']}_rgb.jpg"
            img.save(out, "JPEG", quality=85)
            print(f"  {year} -> {rel['date']} (release {rel['num']}) {img.size} -> {out.name}")


if __name__ == "__main__":
    main(sys.argv[1:])
