from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import (
    Claim,
    Confidence,
    CrossCheck,
    Disclosure,
    EnvironmentalEffects,
    ImpactMetrics,
    LegalCheck,
    Localization,
    ObservationSnapshot,
    PhysicalHazards,
)
from app.services import queries
from app.services.projects import get_project


@dataclass
class Context:
    text: str
    evidence_ids: list[str]


def _promised(claim: Claim | None) -> object:
    if claim is None:
        return None
    return float(claim.promised_num) if claim.promised_num is not None else claim.promised_text


def build_context(
    db: Session, project_id: str, allowed_evidence_ids: list[str] | None = None
) -> Context:
    """Grounding context for Ask/Memo. Reads only what the LLM needs (confidence, dated
    observations, cross-checks, evidence) directly — not the whole assembled dossier — so a
    project with evidence but incomplete dossier sections still answers."""
    project = get_project(db, project_id)  # 404 if unknown
    evidence = queries.evidence_for_project(db, project_id)
    if allowed_evidence_ids is not None:
        allowed = set(allowed_evidence_ids)
        evidence = [e for e in evidence if e.id in allowed]

    conf = db.get(Confidence, project_id)
    claims = {c.id: c for c in db.scalars(select(Claim).where(Claim.project_id == project_id))}
    checks = db.scalars(
        select(CrossCheck).where(CrossCheck.project_id == project_id).order_by(CrossCheck.ordinal)
    ).all()
    snaps = db.scalars(
        select(ObservationSnapshot)
        .where(ObservationSnapshot.project_id == project_id)
        .order_by(ObservationSnapshot.ordinal)
    ).all()

    disc = db.get(Disclosure, project_id)
    loc = db.get(Localization, project_id)
    haz = db.get(PhysicalHazards, project_id)
    eff = db.get(EnvironmentalEffects, project_id)
    imp = db.get(ImpactMetrics, project_id)
    legal = db.scalars(
        select(LegalCheck).where(LegalCheck.project_id == project_id).order_by(LegalCheck.ordinal)
    ).all()

    head = (
        f"PROJECT {project.id}: {project.name} ({project.asset_type}); "
        f"country={project.country}; financing={project.financing_type}; "
        f"screening={project.screening_status}"
    )
    if conf:
        head += (
            f"; on_track={conf.on_track_pct}%; "
            f"risk_to_asset={conf.risk_score}/{conf.risk_band}; "
            f"rationale={conf.rationale}"
        )
    lines = [head]

    if disc:
        lines.append(
            f"DISCLOSURE: title={disc.title}; issuer={disc.issuer}; "
            f"instrument={disc.instrument}; "
            f"financing_date={disc.financing_date.isoformat() if disc.financing_date else None}; "
            f"doc_ref={disc.doc_ref}; summary={disc.summary}"
        )
    if loc:
        lines.append(
            f"LOCALIZATION: region_hint={loc.region_hint}; "
            f"centroid={loc.centroid_lat},{loc.centroid_lon}; match_score={loc.confidence}; "
            f"margin_to_runner_up={loc.margin}; aoi_assurance={loc.aoi_assurance}; "
            f"has_footprint={loc.has_footprint}; method={loc.method}"
        )
        for alt in loc.alternatives:
            lines.append(f"LOCALIZATION-REJECTED {alt.name}: {alt.reason}")
    for s in snaps:
        lines.append(
            f"OBSERVATION {s.date.isoformat()}: footprint_ha={s.footprint_ha}; "
            f"ndvi={s.ndvi}; {s.note}"
        )
    for cc in checks:
        claim = claims.get(cc.claim_id)
        observed = cc.observed_num if cc.observed_num is not None else cc.observed_text
        lines.append(
            f"CROSS-CHECK {claim.kind if claim else cc.claim_id}: "
            f"promised={_promised(claim)} {claim.unit if claim else ''}; "
            f"observed={observed}; status={cc.status}; variance={cc.variance}"
        )
    # Double materiality — the two directions are labelled so the model cannot blend them.
    if haz:
        lines.append(
            f"RISK-TO-ASSET (environment -> asset; financial materiality): "
            f"fire={haz.fire_score}/{haz.fire_band}; flood={haz.flood_score}/{haz.flood_band}; "
            f"heat={haz.heat_score}/{haz.heat_band}; "
            f"water_stress={haz.water_stress_score}/{haz.water_stress_band}; "
            f"worst={haz.composite_score}/{haz.composite_band} "
            f"(null means not yet computed, not zero risk)"
        )
    if eff:
        lines.append(
            f"IMPACT-ON-ENVIRONMENT (asset -> environment; impact materiality): "
            f"vegetation_loss={eff.vegetation_loss_score}/{eff.vegetation_loss_band}; "
            f"vegetation_change_pct={eff.vegetation_change_pct}; "
            f"deforestation_detected={eff.deforestation_detected}; "
            f"land_disturbance_ha={eff.land_disturbance_ha}; "
            f"water_change_pct={eff.water_change_pct}; "
            f"worst={eff.composite_score}/{eff.composite_band}"
        )
    if imp:
        lines.append(
            f"IMPACT-DELIVERED: generation_gwh={imp.generation_gwh}; "
            f"avoided_emissions_tco2={imp.avoided_emissions_tco2}; "
            f"carbon_stock_tco2={imp.carbon_stock_tco2}; carbon_band={imp.carbon_band}; "
            f"assurance={imp.assurance}; "
            f"co2_intensity={imp.co2_intensity_value} {imp.co2_intensity_unit}; "
            f"built={imp.build_year}; financed={imp.financing_year}; "
            f"additionality={imp.additionality_verdict}"
        )
    for lc in legal:
        lines.append(
            f"LEGAL-CHECK {lc.check_type}: subject={lc.subject}; verdict={lc.verdict}; "
            f"authority={lc.authority}; "
            f"as_of={lc.as_of.isoformat() if lc.as_of else None}; detail={lc.detail}"
        )
    for ev in evidence:
        lines.append(
            f"EVIDENCE {ev.id}: source={ev.source_name}; method={ev.method_id}; "
            f"confidence={ev.confidence}; financial_relevance={ev.financial_relevance}; "
            f"limitations={'; '.join(ev.limitations or [])}"
        )
    return Context(text="\n".join(lines), evidence_ids=[e.id for e in evidence])
