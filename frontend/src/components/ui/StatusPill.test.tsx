import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusPill } from "@/components/ui/StatusPill";

describe("StatusPill", () => {
  it("renders its label", () => {
    render(<StatusPill tone="low">On track</StatusPill>);
    expect(screen.getByText("On track")).toBeInTheDocument();
  });

  it("colors the dot by tone", () => {
    const { container } = render(<StatusPill tone="medium">Behind</StatusPill>);
    const dot = container.querySelector("[aria-hidden]");
    expect(dot).not.toBeNull();
    expect(dot?.className).toContain("bg-risk-med");
  });

  it("defaults to a neutral dot", () => {
    const { container } = render(<StatusPill>Unknown</StatusPill>);
    const dot = container.querySelector("[aria-hidden]");
    expect(dot?.className).toContain("bg-faint");
  });
});
