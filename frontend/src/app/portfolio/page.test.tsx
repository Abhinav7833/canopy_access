import { render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import type { ProjectSummary } from "@/lib/types";
import Home from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const project: ProjectSummary = {
  id: "nur_navoi_solar",
  name: "Navoi Solar",
  asset_type: "solar",
  country: "Uzbekistan",
  financing_type: "green_bond",
  status: "active",
  risk_score: 42,
  risk_band: "medium",
};

vi.mock("@/lib/queries", () => ({
  useProjects: () => ({ data: [project], isLoading: false, isError: false }),
}));

describe("Home (portfolio)", () => {
  it("renders a link to the project's detail page with the project name", () => {
    render(<Home />);
    const link = screen.getByRole("link", { name: "Navoi Solar" });
    expect(link).toHaveAttribute("href", `/projects/${project.id}`);
  });

  it("renders the risk band for each asset", () => {
    render(<Home />);
    // Regression guard: the portfolio must surface the risk band (Badge) per row, inside the
    // merged Rating column's RiskScore.
    expect(screen.getByText(project.risk_band!)).toBeInTheDocument();
  });
});
