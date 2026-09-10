export interface ProjectSummary {
  id: string;
  name: string;
  asset_type: string;
  country: string | null;
  financing_type: string | null;
  status: string;
  risk_score: number | null;
  risk_band: string | null;
  avoided_emissions_tco2?: number | null;
}
export interface ProjectDetail extends ProjectSummary {
  monitoring_objective: string | null;
  screening_status: string | null;
}
export interface ImageLayer {
  key: string;
  label: string;
  url: string;
  kind: "rgb" | "overlay";
  /** Provenance of the stored pixels. `date` is null for an undated reference frame. */
  source: string | null;
  date: string | null;
}
export interface Imagery {
  project_id: string;
  layers: ImageLayer[];
}
export interface Evidence {
  id: string;
  source_name: string;
  source_date: string | null;
  method_id: string | null;
  confidence: string | null;
  limitations: string[];
  financial_relevance: string | null;
  supporting_assets: string[];
}
export interface AskResponse {
  answer: string;
  evidence_used: string[];
  confidence: string;
  limitations: string[];
  unsupported_claims_refused: string[];
}
export interface Report {
  id: string;
  project_id: string;
  report_type: string;
  content: string | null;
  evidence_ids: string[];
  generated_at: string;
}
export type Boundary = {
  type: "Feature";
  geometry: { type: string; coordinates: number[][][] };
  properties: { project_id: string; area_hectares: number | null };
};

/* ------------------------------------------------------------------ *
 * Dossier — the precomputed disclosure -> locate -> observe ->
 * cross-check -> confidence narrative. Mirrors backend/app/schemas/
 * project.py::Dossier and the seed_data/projects/<id>.dossier.json
 * fixtures. Every value below optionally carries a `trace` — the
 * minimal evidence-graph pointer back to the disclosure or a claim.
 * ------------------------------------------------------------------ */
export interface DossierTrace {
  source: string;
  date: string | null;
  method: string;
  confidence: string;
  traces_to: string;
}
export interface Disclosure {
  title: string;
  issuer: string;
  instrument: string;
  financing_date: string | null;
  doc_ref: string;
  region_hint: string;
  summary: string;
  trace?: DossierTrace;
}
export type ClaimKind = "capacity_mw" | "area_ha" | "cod_date" | "timeline_months" | string;
export interface Claim {
  id: string;
  kind: ClaimKind;
  promised: number | string;
  unit: string;
  source_span: string;
  trace?: DossierTrace;
}
export interface AlternativeRejected {
  name: string;
  reason: string;
}
export interface Localization {
  region_hint: string;
  located_centroid: [number, number];
  /** `confidence` is the match score; `margin` is the gap to the runner-up — the sharper
   * signal, since a thin margin means look-alikes rather than an unambiguous match. */
  confidence: number;
  margin: number | null;
  matched_fields: string[];
  gem_location_id: string | null;
  reference_source: string | null;
  /** Whether the AOI is a digitised footprint or a box round a point. Every area figure
   * downstream inherits this distinction. */
  aoi_assurance: string | null;
  has_footprint: boolean | null;
  method: string;
  alternatives_rejected: AlternativeRejected[];
  trace?: DossierTrace;
}
export interface ObservationSeriesPoint {
  date: string;
  /** Null until a dated capture backs this observation. */
  image_key: string | null;
  footprint_ha: number | null;
  ndvi: number | null;
  note: string;
  trace?: DossierTrace;
}
/** The pipeline spec's verdict vocabulary: a cross-check either agrees with the claim, agrees
 * on the part the observation can reach, contradicts it, or cannot judge it. */
export type CrossCheckStatus =
  | "consistent"
  | "partially_consistent"
  | "inconsistent"
  | "insufficient_data";
export interface CrossCheckItem {
  claim_id: string;
  observed: number | string;
  status: CrossCheckStatus;
  variance: string;
  evidence_ids: string[];
  trace?: DossierTrace;
}
export interface Confidence {
  on_track_pct: number;
  rationale: string;
  drivers: string[];
  risk_score: number | null;
  risk_band: string | null;
  trace?: DossierTrace;
}
export interface HazardScore {
  score: number | null;
  band: string | null;
}
/** Environment → asset. Financial materiality: what danger nature poses to the asset. */
export interface PhysicalRisk {
  fire: HazardScore;
  flood: HazardScore;
  heat: HazardScore;
  water_stress: HazardScore;
  composite: HazardScore;
  fire_ffwi: number | null;
  fire_dnbr: number | null;
  fire_severity_class: string | null;
  flood_depth_100yr_m: number | null;
  flood_damage_frac: number | null;
  flood_observed_frac: number | null;
  asset_exposure: number | null;
}
/** Asset → environment. Impact materiality: what harm the asset does to its surroundings. */
export interface EnvironmentalEffect {
  vegetation_loss: HazardScore;
  composite: HazardScore;
  vegetation_change_pct: number | null;
  deforestation_detected: boolean | null;
  water_change_pct: number | null;
  land_disturbance_ha: number | null;
  community_exposure_built_up: number | null;
}
export interface Impact {
  generation_gwh: number | null;
  avoided_emissions_tco2: number | null;
  carbon_stock_tco2: number | null;
  carbon_band: string | null;
  assurance: string | null;
  co2_intensity_value: number | null;
  co2_intensity_unit: string | null;
  build_year: number | null;
  financing_year: number | null;
  additionality_verdict: string | null;
}
export type LegalCheckType = "permit" | "sanction" | "litigation" | "ownership";
/** A legal/regulatory cross-reference. Same verdict vocabulary as a claim cross-check —
 * an unreachable register reads `insufficient_data`, never a reassuring `consistent`. */
export interface LegalCheck {
  check_type: LegalCheckType;
  subject: string;
  verdict: CrossCheckStatus;
  detail: string | null;
  authority: string | null;
  as_of: string | null;
  reference: string | null;
  trace?: DossierTrace;
}
export interface Dossier {
  project_id: string;
  disclosure: Disclosure;
  claims: Claim[];
  localization: Localization;
  observation_series: ObservationSeriesPoint[];
  cross_check: CrossCheckItem[];
  legal_checks: LegalCheck[];
  confidence: Confidence;
  physical_risk: PhysicalRisk | null;
  environmental_effect: EnvironmentalEffect | null;
  impact: Impact | null;
  memo_ready: boolean;
}
