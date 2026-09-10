import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { RatingExplainer } from "@/components/features/RatingExplainer";

describe("RatingExplainer", () => {
  it("renders the section heading", () => {
    render(<RatingExplainer />);
    expect(
      screen.getByRole("heading", { name: /one number, and the reasons behind it/i }),
    ).toBeInTheDocument();
  });

  it("explains all three risk bands", () => {
    render(<RatingExplainer />);
    expect(screen.getByText("Low risk")).toBeInTheDocument();
    expect(screen.getByText("Medium risk")).toBeInTheDocument();
    expect(screen.getByText("High risk")).toBeInTheDocument();
  });
});
