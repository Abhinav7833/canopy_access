import { describe, expect, it } from "vitest";
import { HAZARD_SCALE, METRICS, scaleLine, type MetricDoc } from "@/lib/metrics";

const entries = Object.entries(METRICS) as [string, MetricDoc][];

describe("metric registry", () => {
  it("gives every metric a label and a one-sentence summary", () => {
    for (const [key, doc] of entries) {
      expect(doc.label, key).toBeTruthy();
      expect(doc.summary, key).toBeTruthy();
    }
  });

  it("gives every scored metric endpoints and a direction", () => {
    for (const [key, doc] of entries) {
      if (!doc.scale) continue;
      expect(doc.scale.max, key).toBeGreaterThan(doc.scale.min);
      expect(["higher-worse", "higher-better"], key).toContain(doc.scale.direction);
    }
  });

  it("puts every hazard on the one shared scale object", () => {
    for (const key of [
      "fire",
      "flood",
      "hazardComposite",
      "vegetationLoss",
      "effectComposite",
      "riskScore",
      "avgRiskScore",
      "rating",
    ] as const) {
      expect(METRICS[key].scale, key).toBe(HAZARD_SCALE);
    }
  });

  it("states the scale as a percent, without enumerating band cutoffs", () => {
    // The band is already on screen as a chip; the tooltip states the scale, not the ladder.
    expect(scaleLine(HAZARD_SCALE)).toBe("0–100% · higher = more risk");
    for (const doc of Object.values(METRICS)) {
      if (doc.scale) expect(doc.scale).not.toHaveProperty("bands");
    }
  });

  it("marks the two confidence metrics as higher-is-better", () => {
    expect(METRICS.onTrackConfidence.scale?.direction).toBe("higher-better");
    expect(METRICS.localizationConfidence.scale?.direction).toBe("higher-better");
  });

  it("claims no scale for the metrics the pipeline does not score", () => {
    // heat and water_stress are declared in the API schema but no module computes them and
    // no fixture supplies them, so they must not carry a fabricated scale or method.
    for (const key of ["heat", "waterStress"] as const) {
      expect(METRICS[key].scale, key).toBeUndefined();
      expect(METRICS[key].summary, key).toMatch(/not scored/i);
    }
  });

  it("keeps the two materiality directions described as separate, never merged", () => {
    expect(METRICS.riskScore.inputs).toMatch(/excludes/i);
    expect(METRICS.effectComposite.inputs).toMatch(/separate/i);
  });
});
