from __future__ import annotations

import json
import sys
import urllib.error
import urllib.request
from datetime import date
from pathlib import Path

from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon
from sqlalchemy.orm import Session

# Make the `app` package importable when this file is run as a standalone script.
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.db import SessionLocal  # noqa: E402
from app.core.storage import get_storage  # noqa: E402
from app.core.vocabulary import CROSS_CHECK_STATUSES, LEGAL_CHECK_TYPES  # noqa: E402
from app.models import (  # noqa: E402
    Claim,
    Confidence,
    CrossCheck,
    CrossCheckEvidence,
    Disclosure,
    EnvironmentalEffects,
    EvidenceItem,
    ImpactMetrics,
    LegalCheck,
    Localization,
    LocalizationAlternative,
    Methodology,
    ObservationSnapshot,
    PhysicalHazards,
    Project,
    ProjectBoundary,
)

# Static methodology reference rows (spec §6.4) — the LLM agent explains metrics from these.
_METHODOLOGIES = [
    {
        "method_id": "build_v1",
        "name": "Build / land-cover change (v1)",
        "description": "Bi-temporal Sentinel-2 change detection plus a Sentinel-1 SAR flood proxy.",
        "data_sources": ["Sentinel-2", "Sentinel-1"],
        "assumptions": ["Median composites approximate seasonal state"],
        "limitations": ["Confirms build/land-cover change, not generation output"],
    },
    {
        "method_id": "ndvi_change_v1",
        "name": "NDVI change (v1)",
        "description": "Bi-temporal NDVI difference from Sentinel-2 surface reflectance.",
        "data_sources": ["Sentinel-2"],
        "assumptions": ["NDVI proxies vegetation vigour"],
        "limitations": ["NDVI is a proxy, not direct ecological impact"],
    },
    {
        "method_id": "carbon_ar_acm0003",
        "name": "Carbon estimate (AR-ACM0003 principle)",
        "description": "Simplified biomass -> carbon -> CO2e, scaled by area.",
        "data_sources": ["Sentinel-2", "GEDI"],
        "assumptions": ["Allometric NDVI -> biomass relationship"],
        "limitations": ["Not MRV-grade; screening only"],
    },
    {
        "method_id": "risk_composite_v1",
        "name": "Composite risk score (v1)",
        "description": "Weighted flood (SAR) + fire (NBR) sub-scores + vegetation instability.",
        "data_sources": ["Sentinel-1", "Sentinel-2"],
        "assumptions": ["Weights tuned for the demo"],
        "limitations": ["Explanatory demo score, not an underwriting model"],
    },
]


def load_fixture(path: Path) -> dict:
    return json.loads(path.read_text())


def _seed_methodologies(session: Session) -> None:
    for m in _METHODOLOGIES:
        session.merge(Methodology(id=m["method_id"], **m))


def _iso_date(value: str | None) -> date | None:
    return date.fromisoformat(value) if value else None


def _trace(t: dict | None) -> dict:
    """Map a fixture trace object onto the typed trace_* columns."""
    t = t or {}
    return dict(
        trace_source=t.get("source"),
        trace_date=_iso_date(t.get("date")),
        trace_method=t.get("method"),
        trace_confidence=t.get("confidence"),
        trace_traces_to=t.get("traces_to"),
    )


def _claim_pk(pid: str, raw_id: str) -> str:
    """Claim ids are project-scoped in the fixtures (e.g. `claim_area_ha`); prefix them so
    they are globally unique in the shared `claims` table."""
    return f"{pid}__{raw_id}"


def _split_value(v: object) -> dict:
    """A promised/observed value is number-or-string -> exactly one typed column."""
    if isinstance(v, bool):  # guard: bool is an int subclass
        return {"num": None, "text": str(v)}
    if isinstance(v, (int, float)):
        return {"num": v, "text": None}
    return {"num": None, "text": str(v)}


def _validate_fixture(fx: dict) -> None:
    """Fixture-only checks, run before anything is written so a bad fixture reports itself
    rather than surfacing as a constraint violation mid-insert."""
    for r in fx.get("cross_check", []):
        if r["status"] not in CROSS_CHECK_STATUSES:
            raise ValueError(
                f"{fx['id']}: cross_check {r['claim_id']} has verdict {r['status']!r}, "
                f"not one of {list(CROSS_CHECK_STATUSES)}"
            )
    for lc in fx.get("legal_checks", []):
        if lc["verdict"] not in CROSS_CHECK_STATUSES:
            raise ValueError(
                f"{fx['id']}: legal_check {lc['subject']!r} has verdict {lc['verdict']!r}, "
                f"not one of {list(CROSS_CHECK_STATUSES)}"
            )
        if lc["check_type"] not in LEGAL_CHECK_TYPES:
            raise ValueError(
                f"{fx['id']}: legal_check {lc['subject']!r} has type {lc['check_type']!r}, "
                f"not one of {list(LEGAL_CHECK_TYPES)}"
            )

    # Double materiality: the hazard composite is the worst hazard TO the asset and nothing
    # else. A fixture that folds the harm the asset causes back into it would silently undo
    # the separation, so the ingestion gate refuses it rather than storing a mixed number.
    pr = (fx.get("metrics") or {}).get("physical_risk") or {}
    if pr:
        hazards = {k: v for k, v in pr.items() if k not in ("composite", "detail")}
        scores = [(v or {}).get("score") for v in hazards.values()]
        worst = max([s for s in scores if s is not None], default=None)
        stated = (pr.get("composite") or {}).get("score")
        if worst is not None and stated is not None and stated != worst:
            raise ValueError(
                f"{fx['id']}: physical_risk composite is {stated}, but the worst hazard "
                f"({', '.join(sorted(hazards))}) is {worst}. The composite must be the worst "
                f"hazard to the asset and must not absorb an environmental-effect score."
            )


def seed_project(session: Session, fx: dict) -> str:
    pid = fx["id"]
    _validate_fixture(fx)
    # Idempotent reseed: drop any prior rows for this project first (child tables CASCADE)
    # so a fixture that removes a claim/snapshot/cross-check never leaves orphans behind.
    session.query(Project).filter_by(id=pid).delete(synchronize_session=False)
    session.flush()
    session.merge(
        Project(
            id=pid,
            name=fx["name"],
            asset_type=fx["asset_type"],
            country=fx.get("country"),
            financing_type=fx.get("financing_type"),
            monitoring_objective=fx.get("monitoring_objective"),
            status=fx.get("status", "monitored"),
            screening_status=fx.get("screening_status"),
        )
    )
    poly = Polygon(fx["aoi_coords"])
    session.merge(
        ProjectBoundary(
            id=f"{pid}_boundary",
            project_id=pid,
            geom=from_shape(poly, srid=4326),
            source="demo_fixture",
            area_hectares=fx.get("area_hectares"),
        )
    )
    session.flush()  # the project must exist before its FK-linked sections are inserted

    d = fx["disclosure"]
    session.merge(
        Disclosure(
            project_id=pid,
            title=d["title"],
            issuer=d.get("issuer"),
            instrument=d.get("instrument"),
            financing_date=_iso_date(d.get("financing_date")),
            doc_ref=d.get("doc_ref"),
            region_hint=d.get("region_hint"),
            summary=d.get("summary"),
            **_trace(d.get("trace")),
        )
    )

    for i, c in enumerate(fx["claims"]):
        pv = _split_value(c["promised"])
        session.merge(
            Claim(
                id=_claim_pk(pid, c["id"]),
                project_id=pid,
                ordinal=i,
                kind=c["kind"],
                promised_num=pv["num"],
                promised_text=pv["text"],
                unit=c.get("unit"),
                source_span=c.get("source_span"),
                **_trace(c.get("trace")),
            )
        )

    loc = fx["localization"]
    lon, lat = loc["located_centroid"]
    session.merge(
        Localization(
            project_id=pid,
            region_hint=loc.get("region_hint"),
            centroid_lon=lon,
            centroid_lat=lat,
            confidence=loc.get("confidence"),
            margin=loc.get("margin"),
            matched_fields=loc.get("matched_fields", []),
            gem_location_id=loc.get("gem_location_id"),
            reference_source=loc.get("reference_source"),
            aoi_assurance=loc.get("aoi_assurance"),
            has_footprint=loc.get("has_footprint"),
            method=loc.get("method"),
            **_trace(loc.get("trace")),
        )
    )
    session.query(LocalizationAlternative).filter_by(project_id=pid).delete()
    for i, a in enumerate(loc.get("alternatives_rejected", [])):
        session.add(
            LocalizationAlternative(project_id=pid, ordinal=i, name=a["name"], reason=a["reason"])
        )

    for i, s in enumerate(fx["observation_series"]):
        session.merge(
            ObservationSnapshot(
                id=f"{pid}_snap_{i}",
                project_id=pid,
                ordinal=i,
                date=date.fromisoformat(s["date"]),
                image_key=s.get("image_key"),
                footprint_ha=s.get("footprint_ha"),
                ndvi=s.get("ndvi"),
                note=s.get("note"),
                **_trace(s.get("trace")),
            )
        )

    for e in fx["evidence"]:
        session.merge(
            EvidenceItem(
                id=e["id"],
                project_id=pid,
                source_name=e["source_name"],
                source_date=_iso_date(e.get("source_date")),
                method_id=e.get("method_id"),
                confidence=e.get("confidence"),
                limitations=e.get("limitations", []),
                financial_relevance=e.get("financial_relevance"),
                supporting_assets=e.get("supporting_assets", []),
            )
        )

    for i, lc in enumerate(fx.get("legal_checks", [])):
        session.merge(
            LegalCheck(
                id=f"{pid}_legal_{i}",
                project_id=pid,
                ordinal=i,
                check_type=lc["check_type"],
                subject=lc["subject"],
                verdict=lc["verdict"],
                detail=lc.get("detail"),
                authority=lc.get("authority"),
                as_of=_iso_date(lc.get("as_of")),
                reference=lc.get("reference"),
                **_trace(lc.get("trace")),
            )
        )

    for i, r in enumerate(fx["cross_check"]):
        cc_id = f"{pid}_cc_{i}"
        ov = _split_value(r["observed"])
        session.merge(
            CrossCheck(
                id=cc_id,
                project_id=pid,
                ordinal=i,
                claim_id=_claim_pk(pid, r["claim_id"]),
                observed_num=ov["num"],
                observed_text=ov["text"],
                status=r["status"],
                variance=r.get("variance"),
                **_trace(r.get("trace")),
            )
        )
        session.query(CrossCheckEvidence).filter_by(cross_check_id=cc_id).delete()
        for eid in r.get("evidence_ids", []):
            session.add(CrossCheckEvidence(cross_check_id=cc_id, evidence_id=eid))

    cf = fx["confidence"]
    # The headline risk score IS the worst hazard to the asset — derived, not authored a
    # second time, so the portfolio badge and the "Risk to the asset" card cannot disagree.
    # It deliberately excludes the harm the asset causes; that is the other direction and
    # has its own composite.
    hazard = (fx.get("metrics") or {}).get("physical_risk", {}).get("composite") or {}
    session.merge(
        Confidence(
            project_id=pid,
            on_track_pct=cf["on_track_pct"],
            rationale=cf.get("rationale"),
            drivers=cf.get("drivers", []),
            risk_score=hazard.get("score", cf.get("risk_score")),
            risk_band=hazard.get("band", cf.get("risk_band")),
            **_trace(cf.get("trace")),
        )
    )

    metrics = fx.get("metrics") or {}

    def _band(section: dict, key: str) -> tuple:
        s = section.get(key) or {}
        return s.get("score"), s.get("band")

    pr = metrics.get("physical_risk")
    if pr:
        fire_s, fire_b = _band(pr, "fire")
        flood_s, flood_b = _band(pr, "flood")
        heat_s, heat_b = _band(pr, "heat")
        water_s, water_b = _band(pr, "water_stress")
        comp_s, comp_b = _band(pr, "composite")
        detail = pr.get("detail") or {}
        session.merge(
            PhysicalHazards(
                project_id=pid,
                fire_score=fire_s,
                fire_band=fire_b,
                flood_score=flood_s,
                flood_band=flood_b,
                heat_score=heat_s,
                heat_band=heat_b,
                water_stress_score=water_s,
                water_stress_band=water_b,
                composite_score=comp_s,
                composite_band=comp_b,
                fire_ffwi=detail.get("fire_ffwi"),
                fire_dnbr=detail.get("fire_dnbr"),
                fire_severity_class=detail.get("fire_severity_class"),
                flood_depth_100yr_m=detail.get("flood_depth_100yr_m"),
                flood_damage_frac=detail.get("flood_damage_frac"),
                flood_observed_frac=detail.get("flood_observed_frac"),
                asset_exposure=detail.get("asset_exposure"),
            )
        )
    ee = metrics.get("environmental_effect")
    if ee:
        veg_s, veg_b = _band(ee, "vegetation_loss")
        comp_s, comp_b = _band(ee, "composite")
        session.merge(
            EnvironmentalEffects(
                project_id=pid,
                vegetation_loss_score=veg_s,
                vegetation_loss_band=veg_b,
                composite_score=comp_s,
                composite_band=comp_b,
                vegetation_change_pct=ee.get("vegetation_change_pct"),
                deforestation_detected=ee.get("deforestation_detected"),
                water_change_pct=ee.get("water_change_pct"),
                land_disturbance_ha=ee.get("land_disturbance_ha"),
                community_exposure_built_up=ee.get("community_exposure_built_up"),
            )
        )
    im = metrics.get("impact")
    if im:
        session.merge(
            ImpactMetrics(
                project_id=pid,
                generation_gwh=im.get("generation_gwh"),
                avoided_emissions_tco2=im.get("avoided_emissions_tco2"),
                carbon_stock_tco2=im.get("carbon_stock_tco2"),
                carbon_band=im.get("carbon_band"),
                assurance=im.get("assurance"),
                co2_intensity_value=im.get("co2_intensity_value"),
                co2_intensity_unit=im.get("co2_intensity_unit"),
                build_year=im.get("build_year"),
                financing_year=im.get("financing_year"),
                additionality_verdict=im.get("additionality_verdict"),
            )
        )

    session.flush()
    _assert_traceable(session, pid, fx)
    return pid


def _assert_traceable(session: Session, pid: str, fx: dict) -> None:
    """A project must carry its core evidence chain, and every cross-check must resolve to a
    claim + evidence, and every snapshot image to an asset."""
    for section in ("claims", "evidence", "cross_check", "observation_series"):
        if not fx.get(section):
            raise ValueError(f"{pid}: fixture is missing a non-empty '{section}'")
    claim_ids = {c.id for c in session.query(Claim).filter_by(project_id=pid)}
    ev_ids = {e.id for e in session.query(EvidenceItem).filter_by(project_id=pid)}
    assets = {a for e in fx["evidence"] for a in e.get("supporting_assets", [])}
    for r in fx["cross_check"]:
        if _claim_pk(pid, r["claim_id"]) not in claim_ids:
            raise ValueError(f"{pid}: cross_check references unknown claim {r['claim_id']}")
        for eid in r.get("evidence_ids", []):
            if eid not in ev_ids:
                raise ValueError(f"{pid}: cross_check references unknown evidence {eid}")
    for s in fx["observation_series"]:
        # A snapshot without an image_key is a dated measurement we hold no capture for;
        # one that names a key must resolve to an asset some evidence card supplies.
        if s.get("image_key") and s["image_key"] not in assets:
            raise ValueError(
                f"{pid}: snapshot image_key {s['image_key']} not in any evidence assets"
            )


# --- Real AOI imagery (Esri World Imagery, fetched server-side) -------------
# The browser blocks remote tile hosts, so imagery is fetched here during
# seeding and served from the app's own /static. Esri's `export` endpoint
# returns one georeferenced PNG for the exact AOI bbox — no key, no tiling.
_ESRI_EXPORT = (
    "https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/"
    "MapServer/export?bbox={bbox}&bboxSR=4326&imageSR=4326&size={w},{h}&format=png&f=image"
)


def _aoi_bbox(coords: list) -> tuple[float, float, float, float]:
    lons = [p[0] for p in coords]
    lats = [p[1] for p in coords]
    return (min(lons), min(lats), max(lons), max(lats))


def fetch_aoi_imagery(coords: list, max_px: int = 1024) -> bytes | None:
    """Fetch a real satellite image of the AOI from Esri World Imagery.

    Returns PNG bytes georeferenced to the AOI bbox (EPSG:4326, matching how the
    frontend pins the image), or None if the fetch fails — callers fall back to a
    placeholder so seeding still works offline.
    """
    minlon, minlat, maxlon, maxlat = _aoi_bbox(coords)
    dlon, dlat = maxlon - minlon, maxlat - minlat
    if dlon <= 0 or dlat <= 0:
        return None
    if dlon >= dlat:
        w, h = max_px, max(1, round(max_px * dlat / dlon))
    else:
        w, h = max(1, round(max_px * dlon / dlat)), max_px
    url = _ESRI_EXPORT.format(bbox=f"{minlon},{minlat},{maxlon},{maxlat}", w=w, h=h)
    req = urllib.request.Request(url, headers={"User-Agent": "canopy-seed/1.0"})
    try:
        with urllib.request.urlopen(req, timeout=20) as resp:
            data = resp.read()
    except (urllib.error.URLError, TimeoutError, OSError):
        return None
    return data if data[:8] == b"\x89PNG\r\n\x1a\n" else None


# The only image this seeder can source itself: a current Esri view of the AOI.
AOI_REFERENCE_ASSET = "aoi_reference_rgb.png"

# Pre-pulled imagery that ships with the repo (e.g. the Esri Wayback timelapse frames),
# stored per project under seed_data/imagery/<project_id>/<asset>.
IMAGERY_DIR = Path(__file__).resolve().parents[1] / "seed_data" / "imagery"


def ensure_assets(fx: dict) -> list[str]:
    """Store every referenced asset we can source; report any still missing.

    Two sources, tried in order: a file shipped under seed_data/imagery/<pid>/ (the dated
    Wayback timelapse frames), else — for the AOI reference frame only — a live Esri fetch.
    The seeder still never invents pixels and never copies one frame under a second name; a
    missing asset stays missing (the API serves one fewer layer) and is returned here.
    """
    store = get_storage()
    pid = fx["id"]
    names = {a for card in fx["evidence"] for a in card.get("supporting_assets", [])}
    for name in names:
        key = f"{pid}/{name}"
        if store.path_for(key).exists():
            continue
        local = IMAGERY_DIR / pid / name
        if local.exists():
            store.save(key, local.read_bytes())
        elif name == AOI_REFERENCE_ASSET:
            data = fetch_aoi_imagery(fx["aoi_coords"])
            if data is not None:
                store.save(key, data)
    return sorted(n for n in names if not store.path_for(f"{pid}/{n}").exists())


def main() -> None:
    """Seed every fixture in seed_data/projects (or the paths passed as args)."""
    fixtures_dir = Path(__file__).resolve().parents[1] / "seed_data" / "projects"
    paths = [Path(a) for a in sys.argv[1:]] or sorted(fixtures_dir.glob("*.json"))
    session = SessionLocal()
    try:
        _seed_methodologies(session)  # global reference data — seeded once, not per project
        for path in paths:
            fx = load_fixture(path)
            pid = seed_project(session, fx)
            session.commit()
            missing = ensure_assets(fx)
            status = f"missing imagery: {', '.join(missing)}" if missing else "imagery complete"
            print(f"seeded {pid} ({status})")
    finally:
        session.close()


if __name__ == "__main__":
    main()
