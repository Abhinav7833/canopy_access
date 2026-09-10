import { render, screen, within } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { EvidencePipeline } from "@/components/features/EvidencePipeline";

describe("EvidencePipeline", () => {
  it("renders the five stages in narrative order", () => {
    render(<EvidencePipeline />);
    const labels = screen.getAllByRole("listitem").map((li) => li.querySelector("h3")?.textContent);
    expect(labels).toEqual(["Disclosure", "Locate", "Observe", "Cross-check", "Confidence"]);
  });

  it("numbers the stages one through five", () => {
    render(<EvidencePipeline />);
    screen.getAllByRole("listitem").forEach((li, i) => {
      expect(within(li).getByText(String(i + 1))).toBeInTheDocument();
    });
  });

  it("accents only the final confidence node", () => {
    const { container } = render(<EvidencePipeline />);
    const badges = container.querySelectorAll("ol > li > span");
    expect(badges).toHaveLength(5);
    expect(badges[0].classList.contains("bg-accent")).toBe(false);
    expect(badges[badges.length - 1].classList.contains("bg-accent")).toBe(true);
  });
});
