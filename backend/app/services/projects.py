import json
import re

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.core.storage import get_storage
from app.models import (
    Confidence,
    CrossCheck,
    CrossCheckEvidence,
    EnvironmentalEffects,
    ImpactMetrics,
    LegalCheck,
    PhysicalHazards,
    Project,
    ProjectBoundary,
    TraceMixin,
)
from app.schemas.project import (
    AlternativeOut,
    ClaimOut,
    ConfidenceOut,
    CrossCheckOut,
    DisclosureOut,
    Dossier,
    DossierTrace,
    EnvironmentalEffectOut,
    HazardScoreOut,
    ImageLayer,
    Imagery,
    ImpactOut,
    LegalCheckOut,
    LocalizationOut,
    PhysicalRiskOut,
    SnapshotOut,
)
from app.services import queries


def get_project(db: Session, project_id: str) -> Project:
    project = db.get(Project, project_id)
    if project is None:
        raise NotFound(f"project {project_id} not found")
    return project


def _summary_row(p: Project, conf: Confidence | None, impact: ImpactMetrics | None = None) -> dict:
    """Project summary with risk_score/risk_band derived from the single `confidences` home."""
    return {
        "id": p.id,
        "name": p.name,
        "asset_type": p.asset_type,
        "country": p.country,
        "financing_type": p.financing_type,
        "status": p.status,
        "risk_score": conf.risk_score if conf else None,
        "risk_band": conf.risk_band if conf else None,
        "avoided_emissions_tco2": impact.avoided_emissions_tco2 if impact else None,
    }


def list_projects(db: Session) -> list[dict]:
    rows = db.execute(
        select(Project, Confidence, ImpactMetrics)
        .outerjoin(Confidence, Confidence.project_id == Project.id)
        .outerjoin(ImpactMetrics, ImpactMetrics.project_id == Project.id)
        .order_by(Project.name)
    ).all()
    return [_summary_row(p, conf, impact) for p, conf, impact in rows]


def get_project_detail(db: Session, project_id: str) -> dict:
    p = get_project(db, project_id)
    return {
        **_summary_row(p, db.get(Confidence, project_id), db.get(ImpactMetrics, project_id)),
        "monitoring_objective": p.monitoring_objective,
        "screening_status": p.screening_status,
    }


def get_boundary_geojson(db: Session, project_id: str) -> dict:
    get_project(db, project_id)  # 404 with a project-level message if it is unknown
    row = db.execute(
        select(ProjectBoundary, func.ST_AsGeoJSON(ProjectBoundary.geom)).where(
            ProjectBoundary.project_id == project_id
        )
    ).first()
    if row is None:
        raise NotFound(f"boundary for {project_id} not found")
    boundary, geojson = row
    return {
        "type": "Feature",
        "geometry": json.loads(geojson),
        "properties": {"project_id": project_id, "area_hectares": boundary.area_hectares},
    }


# A dated capture can encode its date in the asset name (e.g. wayback_2021-09-15_rgb.jpg).
# When the supplying evidence card is undated — a reference/imagery card that carries a whole
# time series under one provenance — fall back to that key date so each frame still sorts and
# labels by its own date rather than collapsing to null.
_KEY_DATE = re.compile(r"(\d{4}-\d{2}-\d{2})")


def _date_from_key(name: str) -> str | None:
    m = _KEY_DATE.search(name)
    return m.group(1) if m else None


def get_imagery(db: Session, project_id: str) -> Imagery:
    get_project(db, project_id)  # 404 if the project is missing
    store = get_storage()
    layers: dict[str, ImageLayer] = {}
    for evidence in queries.evidence_for_project(db, project_id):
        for name in evidence.supporting_assets or []:
            if name in layers:
                continue
            layers[name] = ImageLayer(
                key=name,
                label=name.replace("_", " ").rsplit(".", 1)[0],
                url=store.url_for(f"{project_id}/{name}"),
                kind="rgb" if "rgb" in name else "overlay",
                # An asset's provenance is the provenance of the evidence card supplying it.
                source=evidence.source_name,
                date=(
                    evidence.source_date.isoformat()
                    if evidence.source_date
                    else _date_from_key(name)
                ),
            )
    return Imagery(project_id=project_id, layers=list(layers.values()))


def _trace(o: TraceMixin) -> DossierTrace:
    """Rebuild the provenance value-object from an element's typed trace_* columns."""
    d = o.trace_date
    return DossierTrace(
        source=o.trace_source,
        date=d.isoformat() if d else None,
        method=o.trace_method,
        confidence=o.trace_confidence,
        traces_to=o.trace_traces_to,
    )


def _value(num: float | None, text: str | None) -> float | str | None:
    """A promised/observed value is stored as exactly one of num/text; return the union."""
    return float(num) if num is not None else text


def get_dossier(db: Session, project_id: str) -> Dossier:
    """Assemble the dossier from its normalized tables (single source of truth).

    Sections load through the ``Project`` relationships (ordered by ``ordinal``); each
    is mapped to its typed ``*Out`` schema so the response is validated, not free-form.
    """
    project = get_project(db, project_id)  # 404 if the project itself is unknown
    disc = project.disclosure
    loc = project.localization
    conf = project.confidence_row
    if disc is None or loc is None or conf is None:
        raise NotFound(f"dossier for {project_id} not found")
    legal = db.query(LegalCheck).filter_by(project_id=project_id).order_by(LegalCheck.ordinal).all()
    haz = db.get(PhysicalHazards, project_id)
    eff = db.get(EnvironmentalEffects, project_id)
    imp = db.get(ImpactMetrics, project_id)

    # Evidence ids per cross-check, scoped to this project in one query (no N+1).
    # Ordered by (cross_check_id, evidence_id) so the emitted evidence_ids are
    # deterministic regardless of the planner's scan order.
    ev_by_cc: dict[str, list[str]] = {}
    for link in db.scalars(
        select(CrossCheckEvidence)
        .join(CrossCheck, CrossCheckEvidence.cross_check_id == CrossCheck.id)
        .where(CrossCheck.project_id == project_id)
        .order_by(CrossCheckEvidence.cross_check_id, CrossCheckEvidence.evidence_id)
    ):
        ev_by_cc.setdefault(link.cross_check_id, []).append(link.evidence_id)

    return Dossier(
        project_id=project.id,
        disclosure=DisclosureOut(
            title=disc.title,
            issuer=disc.issuer,
            instrument=disc.instrument,
            financing_date=disc.financing_date.isoformat() if disc.financing_date else None,
            doc_ref=disc.doc_ref,
            region_hint=disc.region_hint,
            summary=disc.summary,
            trace=_trace(disc),
        ),
        claims=[
            ClaimOut(
                id=c.id,
                kind=c.kind,
                promised=_value(c.promised_num, c.promised_text),
                unit=c.unit,
                source_span=c.source_span,
                trace=_trace(c),
            )
            for c in project.claims
        ],
        localization=LocalizationOut(
            region_hint=loc.region_hint,
            located_centroid=(loc.centroid_lon, loc.centroid_lat),
            confidence=loc.confidence,
            margin=loc.margin,
            matched_fields=list(loc.matched_fields or []),
            gem_location_id=loc.gem_location_id,
            reference_source=loc.reference_source,
            aoi_assurance=loc.aoi_assurance,
            has_footprint=loc.has_footprint,
            method=loc.method,
            alternatives_rejected=[
                AlternativeOut(name=a.name, reason=a.reason) for a in loc.alternatives
            ],
            trace=_trace(loc),
        ),
        observation_series=[
            SnapshotOut(
                date=s.date.isoformat(),
                image_key=s.image_key,
                footprint_ha=s.footprint_ha,
                ndvi=s.ndvi,
                note=s.note,
                trace=_trace(s),
            )
            for s in project.snapshots
        ],
        cross_check=[
            CrossCheckOut(
                claim_id=c.claim_id,
                observed=_value(c.observed_num, c.observed_text),
                status=c.status,
                variance=c.variance,
                evidence_ids=ev_by_cc.get(c.id, []),
                trace=_trace(c),
            )
            for c in project.cross_checks
        ],
        legal_checks=[
            LegalCheckOut(
                check_type=lc.check_type,
                subject=lc.subject,
                verdict=lc.verdict,
                detail=lc.detail,
                authority=lc.authority,
                as_of=lc.as_of.isoformat() if lc.as_of else None,
                reference=lc.reference,
                trace=_trace(lc),
            )
            for lc in legal
        ],
        confidence=ConfidenceOut(
            on_track_pct=conf.on_track_pct,
            rationale=conf.rationale,
            drivers=list(conf.drivers or []),
            risk_score=conf.risk_score,
            risk_band=conf.risk_band,
            trace=_trace(conf),
        ),
        physical_risk=(
            PhysicalRiskOut(
                fire=HazardScoreOut(score=haz.fire_score, band=haz.fire_band),
                flood=HazardScoreOut(score=haz.flood_score, band=haz.flood_band),
                heat=HazardScoreOut(score=haz.heat_score, band=haz.heat_band),
                water_stress=HazardScoreOut(
                    score=haz.water_stress_score, band=haz.water_stress_band
                ),
                composite=HazardScoreOut(score=haz.composite_score, band=haz.composite_band),
                fire_ffwi=haz.fire_ffwi,
                fire_dnbr=haz.fire_dnbr,
                fire_severity_class=haz.fire_severity_class,
                flood_depth_100yr_m=haz.flood_depth_100yr_m,
                flood_damage_frac=haz.flood_damage_frac,
                flood_observed_frac=haz.flood_observed_frac,
                asset_exposure=haz.asset_exposure,
            )
            if haz
            else None
        ),
        environmental_effect=(
            EnvironmentalEffectOut(
                vegetation_loss=HazardScoreOut(
                    score=eff.vegetation_loss_score, band=eff.vegetation_loss_band
                ),
                composite=HazardScoreOut(score=eff.composite_score, band=eff.composite_band),
                vegetation_change_pct=eff.vegetation_change_pct,
                deforestation_detected=eff.deforestation_detected,
                water_change_pct=eff.water_change_pct,
                land_disturbance_ha=eff.land_disturbance_ha,
                community_exposure_built_up=eff.community_exposure_built_up,
            )
            if eff
            else None
        ),
        impact=(
            ImpactOut(
                generation_gwh=imp.generation_gwh,
                avoided_emissions_tco2=imp.avoided_emissions_tco2,
                carbon_stock_tco2=imp.carbon_stock_tco2,
                carbon_band=imp.carbon_band,
                assurance=imp.assurance,
                co2_intensity_value=imp.co2_intensity_value,
                co2_intensity_unit=imp.co2_intensity_unit,
                build_year=imp.build_year,
                financing_year=imp.financing_year,
                additionality_verdict=imp.additionality_verdict,
            )
            if imp
            else None
        ),
        memo_ready=True,
    )
