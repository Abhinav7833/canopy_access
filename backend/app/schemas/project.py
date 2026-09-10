from pydantic import BaseModel, ConfigDict

from app.core.vocabulary import CrossCheckStatus, LegalCheckType


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    asset_type: str
    country: str | None = None
    financing_type: str | None = None
    status: str
    risk_score: int | None = None
    risk_band: str | None = None
    avoided_emissions_tco2: float | None = None


class ProjectDetail(ProjectSummary):
    monitoring_objective: str | None = None
    screening_status: str | None = None


class ImageLayer(BaseModel):
    key: str
    label: str
    url: str
    kind: str  # "rgb" | "overlay"
    # Provenance of the stored pixels, taken from the evidence card that supplies them.
    # `date` is None for an undated reference frame (as opposed to a dated capture).
    source: str | None = None
    date: str | None = None


class Imagery(BaseModel):
    project_id: str
    layers: list[ImageLayer]


class DossierTrace(BaseModel):
    """Provenance value-object attached to every dossier element."""

    source: str | None = None
    date: str | None = None
    method: str | None = None
    confidence: str | None = None
    traces_to: str | None = None


class DisclosureOut(BaseModel):
    title: str
    issuer: str | None = None
    instrument: str | None = None
    financing_date: str | None = None
    doc_ref: str | None = None
    region_hint: str | None = None
    summary: str | None = None
    trace: DossierTrace


class ClaimOut(BaseModel):
    id: str
    kind: str
    promised: float | str | None = None  # union reconstructed from promised_num/promised_text
    unit: str | None = None
    source_span: str | None = None
    trace: DossierTrace


class AlternativeOut(BaseModel):
    name: str
    reason: str


class LocalizationOut(BaseModel):
    region_hint: str | None = None
    located_centroid: tuple[float, float]
    confidence: float | None = None
    # Why the match won, and how trustworthy the resulting AOI is.
    margin: float | None = None
    matched_fields: list[str] = []
    gem_location_id: str | None = None
    reference_source: str | None = None
    aoi_assurance: str | None = None
    has_footprint: bool | None = None
    method: str | None = None
    alternatives_rejected: list[AlternativeOut] = []
    trace: DossierTrace


class SnapshotOut(BaseModel):
    date: str
    image_key: str | None = None
    footprint_ha: float | None = None
    ndvi: float | None = None
    note: str | None = None
    trace: DossierTrace


class CrossCheckOut(BaseModel):
    claim_id: str
    observed: float | str | None = None  # union reconstructed from observed_num/observed_text
    status: CrossCheckStatus
    variance: str | None = None
    evidence_ids: list[str] = []
    trace: DossierTrace


class LegalCheckOut(BaseModel):
    """A legal/regulatory cross-reference, carrying the same verdict vocabulary as a claim
    cross-check. `authority` and `as_of` are what make the verdict readable."""

    check_type: LegalCheckType
    subject: str
    verdict: CrossCheckStatus
    detail: str | None = None
    authority: str | None = None
    as_of: str | None = None
    reference: str | None = None
    trace: DossierTrace


class ConfidenceOut(BaseModel):
    on_track_pct: int
    rationale: str | None = None
    drivers: list[str] = []
    risk_score: int | None = None
    risk_band: str | None = None
    trace: DossierTrace


class HazardScoreOut(BaseModel):
    score: int | None = None
    band: str | None = None


class PhysicalRiskOut(BaseModel):
    """Environment -> asset. Financial materiality: what danger nature poses to the asset."""

    fire: HazardScoreOut
    flood: HazardScoreOut
    heat: HazardScoreOut
    water_stress: HazardScoreOut
    composite: HazardScoreOut
    # Derivation detail, so the score can be interrogated rather than taken on trust.
    fire_ffwi: float | None = None
    fire_dnbr: float | None = None
    fire_severity_class: str | None = None
    flood_depth_100yr_m: float | None = None
    flood_damage_frac: float | None = None
    flood_observed_frac: float | None = None
    asset_exposure: float | None = None


class EnvironmentalEffectOut(BaseModel):
    """Asset -> environment. Impact materiality: what harm the asset does to its surroundings."""

    vegetation_loss: HazardScoreOut
    composite: HazardScoreOut
    vegetation_change_pct: float | None = None
    deforestation_detected: bool | None = None
    water_change_pct: float | None = None
    land_disturbance_ha: float | None = None
    community_exposure_built_up: float | None = None


class ImpactOut(BaseModel):
    generation_gwh: float | None = None
    avoided_emissions_tco2: float | None = None
    carbon_stock_tco2: float | None = None
    carbon_band: str | None = None
    assurance: str | None = None
    co2_intensity_value: float | None = None
    co2_intensity_unit: str | None = None
    build_year: int | None = None
    financing_year: int | None = None
    additionality_verdict: str | None = None


class Dossier(BaseModel):
    """Precomputed disclosure -> locate -> observe -> cross-check -> confidence narrative.

    Assembled from the normalized dossier tables (single source of truth, see
    docs/specs/2026-07-17-dossier-normalization-design.md). Fully typed: the wire
    contract mirrors the database, so a malformed section fails validation rather
    than passing through untyped.
    """

    project_id: str
    disclosure: DisclosureOut
    claims: list[ClaimOut] = []
    localization: LocalizationOut
    observation_series: list[SnapshotOut] = []
    cross_check: list[CrossCheckOut] = []
    legal_checks: list[LegalCheckOut] = []
    confidence: ConfidenceOut
    # The two directions of double materiality, deliberately separate fields: nothing in the
    # contract lets a consumer merge them back into a single score.
    physical_risk: PhysicalRiskOut | None = None
    environmental_effect: EnvironmentalEffectOut | None = None
    impact: ImpactOut | None = None
    memo_ready: bool = False
