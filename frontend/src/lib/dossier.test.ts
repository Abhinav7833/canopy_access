import { describe, expect, it } from "vitest";
import { claimLabel } from "@/lib/dossier";

describe("claimLabel", () => {
  it("uses the solar vocabulary for a solar kind", () => {
    expect(claimLabel("generation_gwh", "solar")).toBe("Annual generation");
    expect(claimLabel("area_ha", "solar")).toBe("Panel-field footprint");
  });

  it("uses the mangrove vocabulary for a mangrove kind", () => {
    expect(claimLabel("protected_ha", "mangrove")).toBe("Protected area");
    expect(claimLabel("credits_tco2", "mangrove")).toBe("Carbon credits issued");
  });

  it("falls back to the generic map when the type has no override", () => {
    // mangrove has no `area_ha` override, so the generic label wins.
    expect(claimLabel("area_ha", "mangrove")).toBe("Site area");
    // no asset type at all -> generic map.
    expect(claimLabel("capacity_mw")).toBe("Nameplate capacity");
  });

  it("title-cases an unknown kind", () => {
    expect(claimLabel("some_new_metric", "solar")).toBe("Some New Metric");
  });
});
