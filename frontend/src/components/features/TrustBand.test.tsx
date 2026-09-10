import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { TrustBand } from "@/components/features/TrustBand";

describe("TrustBand", () => {
  it("renders the three methodology pillars", () => {
    render(<TrustBand />);
    expect(screen.getByRole("heading", { name: "Independent evidence" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "Everything cited" })).toBeInTheDocument();
    expect(screen.getByRole("heading", { name: "One explained rating" })).toBeInTheDocument();
  });

  it("makes no fabricated trust signals (no logos/testimonials/compliance badges)", () => {
    // Guards the design spec's hard rule: credibility comes from describing the real method,
    // never fake customer imagery or compliance claims.
    const { container } = render(<TrustBand />);
    expect(container.querySelector("img")).toBeNull();
    expect(screen.queryByText(/SOC-?2|ISO 27001|trusted by|our customers/i)).toBeNull();
  });
});
