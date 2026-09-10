from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base
from app.core.vocabulary import CROSS_CHECK_STATUSES, LEGAL_CHECK_TYPES


class TraceMixin:
    """Provenance value-object shared by every dossier element (typed, not JSONB)."""

    trace_source: Mapped[str | None] = mapped_column(String, nullable=True)
    trace_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    trace_method: Mapped[str | None] = mapped_column(String, nullable=True)
    trace_confidence: Mapped[str | None] = mapped_column(String, nullable=True)
    trace_traces_to: Mapped[str | None] = mapped_column(String, nullable=True)


class Disclosure(Base, TraceMixin):
    __tablename__ = "disclosures"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    title: Mapped[str] = mapped_column(String)
    issuer: Mapped[str | None] = mapped_column(String, nullable=True)
    instrument: Mapped[str | None] = mapped_column(String, nullable=True)
    financing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    doc_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    region_hint: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Claim(Base, TraceMixin):
    __tablename__ = "claims"
    __table_args__ = (
        CheckConstraint(
            "(promised_num IS NULL) <> (promised_text IS NULL)", name="ck_claim_promised_one_of"
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String)
    promised_num: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    promised_text: Mapped[str | None] = mapped_column(String, nullable=True)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    source_span: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Localization(Base, TraceMixin):
    __tablename__ = "localizations"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    region_hint: Mapped[str | None] = mapped_column(String, nullable=True)
    centroid_lon: Mapped[float] = mapped_column(Float)
    centroid_lat: Mapped[float] = mapped_column(Float)
    # `confidence` is the match score itself; `margin` is the gap to the runner-up, which is
    # the sharper signal — a wide margin means an unambiguous match, a thin one means several
    # look-alikes and a human should look (canopy_pipeline/matching/entity_resolution.py).
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    margin: Mapped[float | None] = mapped_column(Float, nullable=True)
    matched_fields: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    gem_location_id: Mapped[str | None] = mapped_column(String, nullable=True)
    reference_source: Mapped[str | None] = mapped_column(String, nullable=True)
    # How trustworthy the AOI itself is: a digitised footprint or a box round a point. Every
    # area figure downstream inherits this, so it travels with the localisation.
    aoi_assurance: Mapped[str | None] = mapped_column(String, nullable=True)
    has_footprint: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    method: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alternatives: Mapped[list[LocalizationAlternative]] = relationship(
        cascade="all, delete-orphan", order_by="LocalizationAlternative.ordinal"
    )


class LocalizationAlternative(Base):
    __tablename__ = "localization_alternatives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("localizations.project_id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(String)


class ObservationSnapshot(Base, TraceMixin):
    __tablename__ = "observation_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    date: Mapped[date] = mapped_column(Date)
    # Null until a dated capture backs this observation — the reference frame served by
    # /imagery is AOI-wide provenance, not the image any one snapshot was measured from.
    image_key: Mapped[str | None] = mapped_column(String, nullable=True)
    footprint_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    ndvi: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class LegalCheck(Base, TraceMixin):
    """Legal and regulatory cross-reference: permits, sanctions screening, litigation and
    ownership of record.

    A cross-check like any other — same verdict vocabulary, same provenance trace — because
    that is how it was asked for: "when you say cross-check, that's one of the things that we
    also want to cross-check on the plant". `authority` and `as_of` are what make a verdict
    readable: "no hits" means nothing without naming the register and the date it reflects,
    and an unreachable register is `insufficient_data`, never a reassuring `consistent`."""

    __tablename__ = "legal_checks"
    __table_args__ = (
        CheckConstraint(
            "verdict IN ({})".format(", ".join(f"'{s}'" for s in CROSS_CHECK_STATUSES)),
            name="ck_legalcheck_verdict_vocabulary",
        ),
        CheckConstraint(
            "check_type IN ({})".format(", ".join(f"'{s}'" for s in LEGAL_CHECK_TYPES)),
            name="ck_legalcheck_type_vocabulary",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    check_type: Mapped[str] = mapped_column(String)
    subject: Mapped[str] = mapped_column(String)
    verdict: Mapped[str] = mapped_column(String)
    detail: Mapped[str | None] = mapped_column(String, nullable=True)
    authority: Mapped[str | None] = mapped_column(String, nullable=True)
    as_of: Mapped[date | None] = mapped_column(Date, nullable=True)
    reference: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrossCheck(Base, TraceMixin):
    __tablename__ = "cross_checks"
    __table_args__ = (
        CheckConstraint(
            "(observed_num IS NULL) <> (observed_text IS NULL)",
            name="ck_crosscheck_observed_one_of",
        ),
        # The verdict vocabulary is a property of the data, not a convention of whichever
        # writer produced it — an off-spec verdict fails at write time, where it belongs.
        CheckConstraint(
            "status IN ({})".format(", ".join(f"'{s}'" for s in CROSS_CHECK_STATUSES)),
            name="ck_crosscheck_status_vocabulary",
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), index=True
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"), index=True)
    observed_num: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    observed_text: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    variance: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evidence_links: Mapped[list[CrossCheckEvidence]] = relationship(cascade="all, delete-orphan")


class CrossCheckEvidence(Base):
    __tablename__ = "cross_check_evidence"

    cross_check_id: Mapped[str] = mapped_column(
        ForeignKey("cross_checks.id", ondelete="CASCADE"), primary_key=True
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("evidence_items.id", ondelete="CASCADE"), primary_key=True, index=True
    )


class Confidence(Base, TraceMixin):
    __tablename__ = "confidences"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    on_track_pct: Mapped[int] = mapped_column(Integer)
    rationale: Mapped[str | None] = mapped_column(String, nullable=True)
    drivers: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_band: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class PhysicalHazards(Base):
    """**Environment -> asset**: what danger nature poses to the financed asset.

    One half of the double-materiality pair (financial materiality). Holds only outside-in
    hazards; vegetation loss lives in `EnvironmentalEffects` because it runs the other way.
    `composite_score` is the worst hazard and must never absorb an effect score — mixing the
    directions produces a number that rises both when the asset is endangered and when it
    causes harm, which are opposite findings. Provenance columns carry the derivation so the
    score is defensible rather than asserted (canopy_pipeline/analytics/risk_scoring.py)."""

    __tablename__ = "physical_hazards"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    fire_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    fire_band: Mapped[str | None] = mapped_column(String, nullable=True)
    flood_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    flood_band: Mapped[str | None] = mapped_column(String, nullable=True)
    heat_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    heat_band: Mapped[str | None] = mapped_column(String, nullable=True)
    water_stress_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    water_stress_band: Mapped[str | None] = mapped_column(String, nullable=True)
    composite_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    composite_band: Mapped[str | None] = mapped_column(String, nullable=True)
    # Derivation detail (Hazard x Exposure x Vulnerability, IPCC AR6).
    fire_ffwi: Mapped[float | None] = mapped_column(Float, nullable=True)
    fire_dnbr: Mapped[float | None] = mapped_column(Float, nullable=True)
    fire_severity_class: Mapped[str | None] = mapped_column(String, nullable=True)
    flood_depth_100yr_m: Mapped[float | None] = mapped_column(Float, nullable=True)
    flood_damage_frac: Mapped[float | None] = mapped_column(Float, nullable=True)
    flood_observed_frac: Mapped[float | None] = mapped_column(Float, nullable=True)
    asset_exposure: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class EnvironmentalEffects(Base):
    """**Asset -> environment**: what harm the financed asset does to its surroundings.

    The other half of the double-materiality pair (impact materiality). Vegetation loss moved
    here from the hazard table: it is caused BY the asset, so scoring it alongside fire and
    flood conflated two opposite readings. The positive half of this same direction (delivered
    generation, avoided emissions, carbon stock) lives in `ImpactMetrics` and is presented
    beside it."""

    __tablename__ = "environmental_effects"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    vegetation_loss_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    vegetation_loss_band: Mapped[str | None] = mapped_column(String, nullable=True)
    vegetation_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    deforestation_detected: Mapped[bool | None] = mapped_column(Boolean, nullable=True)
    water_change_pct: Mapped[float | None] = mapped_column(Float, nullable=True)
    land_disturbance_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    community_exposure_built_up: Mapped[float | None] = mapped_column(Float, nullable=True)
    composite_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    composite_band: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class ImpactMetrics(Base):
    """Impact + additionality metrics. Asset-type-dependent (all nullable so one table fits both):
    solar carries generation / avoided emissions; mangrove carries carbon stock + band. Authored
    until the real PVWatts / ESA-CCI pipeline is wired."""

    __tablename__ = "impact_metrics"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    generation_gwh: Mapped[float | None] = mapped_column(Float, nullable=True)
    avoided_emissions_tco2: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbon_stock_tco2: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbon_band: Mapped[str | None] = mapped_column(String, nullable=True)
    assurance: Mapped[str | None] = mapped_column(String, nullable=True)
    co2_intensity_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    co2_intensity_unit: Mapped[str | None] = mapped_column(String, nullable=True)
    build_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    financing_year: Mapped[int | None] = mapped_column(Integer, nullable=True)
    additionality_verdict: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
