import { fireEvent, render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LegalChecks } from "@/components/features/LegalChecks";
import type { LegalCheck } from "@/lib/types";

const permit: LegalCheck = {
  check_type: "permit",
  subject: "Construction and operating permits",
  verdict: "insufficient_data",
  detail: "No permit register is connected, so no independent check has been performed.",
  authority: "Uzbekistan national permit register",
  as_of: null,
  reference: "nur_navoi_impact_report_2022.pdf#s3",
  trace: {
    source: "disclosure",
    date: "2020-12-01",
    method: "Disclosure reading",
    confidence: "medium",
    traces_to: "disclosure",
  },
};

const ownership: LegalCheck = {
  check_type: "ownership",
  subject: "Masdar (Nur Navoi Solar FE LLC)",
  verdict: "partially_consistent",
  detail: "Sponsor of record is named in the financing disclosure.",
  authority: "Issuer disclosure",
  as_of: "2020-12-01",
  reference: null,
  trace: undefined,
};

/** A <details> row is expanded iff its element carries the `open` attribute. */
const rowFor = (subject: string): HTMLDetailsElement => {
  const summary = screen.getByText(subject).closest("summary");
  if (!summary) throw new Error(`no summary for ${subject}`);
  return summary.parentElement as HTMLDetailsElement;
};

describe("LegalChecks", () => {
  it("renders nothing when there are no checks", () => {
    const { container } = render(<LegalChecks checks={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("lists every check with its verdict, and counts them", () => {
    render(<LegalChecks checks={[ownership, permit]} />);
    expect(screen.getByText("Ownership")).toBeInTheDocument();
    expect(screen.getByText("Permit")).toBeInTheDocument();
    expect(screen.getByText("Insufficient Data")).toBeInTheDocument();
    expect(screen.getByText("2 checks")).toBeInTheDocument();
  });

  it("keeps the finding and reference collapsed until the row is opened", () => {
    render(<LegalChecks checks={[permit]} />);
    // The detail text is in the DOM but inside a closed <details>, so it is not shown.
    expect(rowFor(permit.subject).open).toBe(false);

    fireEvent.click(screen.getByText(permit.subject));
    const row = rowFor(permit.subject);
    expect(row.open).toBe(true);
    expect(within(row).getByText(/no permit register is connected/i)).toBeInTheDocument();
    expect(within(row).getByText(permit.reference!)).toBeInTheDocument();
    expect(within(row).getByText(/← disclosure/)).toBeInTheDocument();
  });

  it("shows an unreachable register as insufficient, never as consistent", () => {
    render(<LegalChecks checks={[permit]} />);
    expect(screen.queryByText("Consistent")).not.toBeInTheDocument();
    expect(screen.getByText("Insufficient Data")).toBeInTheDocument();
  });

  it("states the register with its as-of date, so 'no hits' is dated", () => {
    render(<LegalChecks checks={[ownership]} />);
    fireEvent.click(screen.getByText(ownership.subject));
    const row = rowFor(ownership.subject);
    expect(within(row).getByText(/issuer disclosure/i)).toBeInTheDocument();
    expect(within(row).getByText(/as of/i)).toBeInTheDocument();
  });

  it("opens rows independently of one another", () => {
    render(<LegalChecks checks={[ownership, permit]} />);
    fireEvent.click(screen.getByText(permit.subject));
    expect(rowFor(permit.subject).open).toBe(true);
    expect(rowFor(ownership.subject).open).toBe(false);
  });

  it("pluralizes the count only when there is more than one check", () => {
    const { rerender } = render(<LegalChecks checks={[permit]} />);
    expect(screen.getByText("1 check")).toBeInTheDocument();
    rerender(<LegalChecks checks={[permit, ownership]} />);
    expect(screen.getByText("2 checks")).toBeInTheDocument();
  });

  it("keeps the register date when the authority name is missing", () => {
    // authority and as_of are independently nullable; a lone date must still show.
    const datedOnly: LegalCheck = { ...permit, authority: null, as_of: "2025-06-01" };
    render(<LegalChecks checks={[datedOnly]} />);
    fireEvent.click(screen.getByText(datedOnly.subject));
    expect(within(rowFor(datedOnly.subject)).getByText(/as of/i)).toBeInTheDocument();
  });
});
