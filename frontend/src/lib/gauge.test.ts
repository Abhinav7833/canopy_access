import { describe, expect, it } from "vitest";
import { arcOffset, circumference } from "@/lib/gauge";

describe("gauge", () => {
  const r = 47;
  const circ = 2 * Math.PI * r;

  it("full circumference for a radius", () => {
    expect(circumference(r)).toBeCloseTo(circ, 6);
  });
  it("no offset at 100%", () => {
    expect(arcOffset(100, r)).toBeCloseTo(0, 6);
  });
  it("full offset at 0% and for null", () => {
    expect(arcOffset(0, r)).toBeCloseTo(circ, 6);
    expect(arcOffset(null, r)).toBeCloseTo(circ, 6);
  });
  it("half offset at 50%", () => {
    expect(arcOffset(50, r)).toBeCloseTo(circ / 2, 6);
  });
  it("clamps out-of-range input", () => {
    expect(arcOffset(150, r)).toBeCloseTo(0, 6);
    expect(arcOffset(-20, r)).toBeCloseTo(circ, 6);
  });
});
