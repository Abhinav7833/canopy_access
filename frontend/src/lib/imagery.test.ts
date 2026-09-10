import { describe, expect, it } from "vitest";
import { layerUrl, referenceFrame } from "@/lib/imagery";
import type { ImageLayer, Imagery } from "@/lib/types";

const layer = (key: string, date: string | null): ImageLayer => ({
  key,
  label: key,
  url: `/static/p1/${key}`,
  kind: "rgb",
  source: date ? "Sentinel-2" : "Esri World Imagery",
  date,
});

const imagery = (layers: ImageLayer[]): Imagery => ({ project_id: "p1", layers });

describe("referenceFrame", () => {
  it("prefers the most recent capture over an undated reference frame", () => {
    const dated = layer("dated_2021_09_rgb.png", "2021-09-15");
    const picked = referenceFrame(imagery([layer("aoi_reference_rgb.png", null), dated]));
    expect(picked).toBe(dated);
  });

  it("falls back to the undated reference frame when nothing is dated", () => {
    const reference = layer("aoi_reference_rgb.png", null);
    expect(referenceFrame(imagery([reference]))).toBe(reference);
  });

  it("ignores non-rgb layers and tolerates missing imagery", () => {
    const overlay = { ...layer("change_overlay.png", "2021-09-15"), kind: "overlay" as const };
    expect(referenceFrame(imagery([overlay]))).toBeUndefined();
    expect(referenceFrame(undefined)).toBeUndefined();
  });
});

describe("layerUrl", () => {
  it("resolves an exact key", () => {
    const l = layer("aoi_reference_rgb.png", null);
    expect(layerUrl(imagery([l]), l.key)).toBe(l.url);
  });

  it("resolves a key that arrives with a path prefix or casing drift", () => {
    const l = layer("aoi_reference_rgb.png", null);
    expect(layerUrl(imagery([l]), "nur_navoi_solar/AOI_Reference_RGB.png")).toBe(l.url);
  });

  it("returns nothing for a snapshot with no capture", () => {
    expect(layerUrl(imagery([layer("aoi_reference_rgb.png", null)]), null)).toBeUndefined();
  });
});
