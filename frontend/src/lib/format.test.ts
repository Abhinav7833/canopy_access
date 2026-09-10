import { describe, expect, it } from "vitest";
import { crossCheckTone } from "@/lib/format";

describe("crossCheckTone", () => {
  it("reads green only when the observation agrees with the claim", () => {
    expect(crossCheckTone("consistent")).toBe("low");
  });

  it("does not read green when only part of the claim could be reached", () => {
    // A proxy that agrees is not a verified claim; amber keeps the caveat visible.
    expect(crossCheckTone("partially_consistent")).toBe("medium");
  });

  it("escalates a contradicted claim to red", () => {
    expect(crossCheckTone("inconsistent")).toBe("high");
  });

  it("stays neutral — never reassuring — when a check cannot be judged", () => {
    expect(crossCheckTone("insufficient_data")).toBe("neutral");
    expect(crossCheckTone(null)).toBe("neutral");
    expect(crossCheckTone("met")).toBe("neutral"); // retired vocabulary must not read green
  });
});
