/** What every number on screen means, and on what scale.
 *
 * The dossier shows figures on three different scales with opposite polarity — a risk score
 * where 100 is bad sits beside an on-track percentage where 100 is good, both painted from
 * the same green→red ramp. This registry is the single home for the definitions, so the
 * screens can't drift from each other, and `MetricInfo` renders them uniformly.
 *
 * Content rule: everything here is read off the scoring code. No invented magnitudes, and no
 * named methodology for a metric that doesn't have one. */

export type MetricDirection = "higher-worse" | "higher-better";

export type MetricScale = {
  /** Endpoints, not a pre-rendered string, so the unit a screen prints beside a value and the
   * range a description reads both come from here. */
  min: number;
  max: number;
  /** Suffix on the endpoints and on the value itself, e.g. "%". */
  unit?: string;
  direction: MetricDirection;
};

export type MetricDoc = {
  label: string;
  /** What the metric means, in one sentence. */
  summary: string;
  scale?: MetricScale;
  /** What feeds it — and the caveat, where the honest answer is narrower than the label. */
  inputs?: string;
};

export const DIRECTION_LABEL: Record<MetricDirection, string> = {
  "higher-worse": "Higher = more risk",
  "higher-better": "Higher = better",
};

/** Hazards score as a percent of the worst case. The band cutoffs behind Low/Medium/High
 * (`band_for` in canopy_pipeline/analytics/risk_scoring.py) are deliberately not printed:
 * the band itself is already on screen as a chip, and enumerating the thresholds beside it
 * is detail nobody reads. */
export const HAZARD_SCALE: MetricScale = {
  min: 0,
  max: 100,
  unit: "%",
  direction: "higher-worse",
};

/** "0–100% · higher = more risk" — the one composition of a scale into prose. Every surface
 * that states a scale goes through here, so they cannot word it differently. (A screen that
 * needs the bare range prints `scale.max` directly; there's no caller for the endpoints alone.) */
export function scaleLine(scale: MetricScale): string {
  const range = `${scale.min}–${scale.max}${scale.unit ?? ""}`;
  return `${range} · ${DIRECTION_LABEL[scale.direction].toLowerCase()}`;
}

const DEFS = {
  // ---- Confidence: the headline pair, the one place polarity is genuinely confusing ----
  onTrackConfidence: {
    label: "On-track confidence",
    summary:
      "How confident we are that this asset is where it was claimed to be and is being built as disclosed.",
    scale: { min: 0, max: 100, unit: "%", direction: "higher-better" },
    inputs:
      "Localization confidence multiplied by build-progress confidence, so a shaky match or an off-track build pulls it down on its own. Build progress is a weighted blend of the cross-checks, led by build timing against financing.",
  },
  riskScore: {
    label: "Risk score",
    summary: "Physical hazard to the asset — what danger nature poses to it.",
    scale: HAZARD_SCALE,
    inputs:
      "The physical-hazard composite: the worst of fire and flood, not an average. It excludes the asset's own impact on the environment, which is scored separately and never merged into this number.",
  },

  // ---- Risk to the asset ----
  fire: {
    label: "Fire",
    summary: "Wildfire danger to the asset.",
    scale: HAZARD_SCALE,
    inputs: "Fire-weather hazard, scaled by how much burnable fuel is present at the site.",
  },
  flood: {
    label: "Flood",
    summary: "Flood danger to the asset.",
    scale: HAZARD_SCALE,
    inputs:
      "Modeled 100-year flood depth at the site, converted to expected damage by a published depth-damage curve.",
  },
  heat: {
    label: "Heat",
    summary: "Not scored for this asset.",
    inputs:
      "No heat model is wired into the pipeline yet, so this row stays empty rather than showing a placeholder figure.",
  },
  waterStress: {
    label: "Water stress",
    summary: "Not scored for this asset.",
    inputs:
      "No water-stress model is wired into the pipeline yet, so this row stays empty rather than showing a placeholder figure.",
  },
  hazardComposite: {
    label: "Composite",
    summary: "The single figure for hazard to the asset.",
    scale: HAZARD_SCALE,
    inputs:
      "The worst of the scored hazards, not an average — one severe hazard is not offset by calm ones. This is the number carried up to the risk score.",
  },

  // ---- Impact on the environment ----
  vegetationLoss: {
    label: "Vegetation loss",
    summary: "Vegetation observed lost in and around the asset footprint.",
    scale: HAZARD_SCALE,
    inputs: "Measured from the satellite record, not from the disclosure.",
  },
  effectComposite: {
    label: "Composite",
    summary: "The single figure for harm done by the asset.",
    scale: HAZARD_SCALE,
    inputs:
      "Kept separate from hazard to the asset on purpose: a combined number would rise both when the asset is endangered and when it causes harm, and those call for opposite actions.",
  },
  landDisturbance: {
    label: "Land disturbed",
    summary: "Ground area altered by the asset, in hectares.",
    inputs: "Measured from the located boundary, so it inherits that boundary's accuracy.",
  },
  waterChange: {
    label: "Water change",
    summary: "Change in surface water observed at the site, as a percentage.",
    // Deliberately unscaled: this is a signed change, not a 0–100 score, and a rise is not
    // automatically the bad direction — claiming one would be inventing a reading.
    inputs: "Measured from the satellite record across the monitored period.",
  },

  // ---- Impact figures ----
  generation: {
    label: "Generation",
    summary: "Modeled annual electricity output, in gigawatt-hours per year.",
    inputs: "Modeled from the asset's disclosed capacity — not an independent meter reading.",
  },
  avoidedEmissions: {
    label: "Avoided emissions",
    summary:
      "Modeled emissions avoided each year versus the grid this asset displaces, in tonnes of CO2 equivalent.",
    inputs: "Modeled from generation and grid intensity — not a measured or audited figure.",
  },
  carbonStock: {
    label: "Carbon stock",
    summary: "Carbon held on site, in tonnes of CO2 equivalent.",
    inputs:
      "A standing-stock estimate from the satellite record. Where the band says so, it is a conservative lower bound covering above-ground biomass only.",
  },
  co2Intensity: {
    label: "CO₂ intensity",
    summary: "Emissions per unit of output.",
    inputs: "The unit shown alongside the value states what it is measured against.",
  },
  assurance: {
    label: "Assurance",
    summary: "How firm the impact figures are, and who stands behind them.",
    inputs: "Stated so modeled figures are not read as audited ones.",
  },
  additionality: {
    label: "Additionality",
    summary: "Whether the build started after the financing, as the claim implies it should.",
    inputs:
      "Compares observed build onset against the financing year. Consistent means the satellite record supports the ordering; it does not prove the financing caused the build.",
  },

  // ---- Locate ----
  localizationConfidence: {
    label: "Localization confidence",
    summary: "How confident we are that the located area is the asset the disclosure describes.",
    scale: { min: 0, max: 100, unit: "%", direction: "higher-better" },
    inputs: "From matching the disclosed region against candidate sites.",
  },
  aoiAssurance: {
    label: "AOI assurance",
    summary: "How the asset boundary was established, and how exact it is.",
    inputs: "Every area figure downstream inherits this boundary's accuracy.",
  },

  // ---- Portfolio ----
  avgRiskScore: {
    label: "Avg. risk score",
    summary: "Mean physical-hazard score across the assets that have one.",
    scale: HAZARD_SCALE,
    inputs: "Assets without a score are left out of the average rather than counted as zero.",
  },
  highCritical: {
    label: "High / critical",
    summary: "How many assets sit in the top two risk bands.",
    inputs: "Counted from each asset's band, not from a second pass over the scores.",
  },
  rating: {
    label: "Rating",
    summary: "Each asset's physical-hazard score with the band it falls in.",
    scale: HAZARD_SCALE,
    inputs: "Open an asset to see the signals behind its rating.",
  },
} satisfies Record<string, MetricDoc>;

/** Keys are inferred from the definitions above; values are widened to `MetricDoc` so a
 * caller holding an arbitrary `MetricKey` can read `.scale` without narrowing per key. */
export type MetricKey = keyof typeof DEFS;
export const METRICS: Record<MetricKey, MetricDoc> = DEFS;
