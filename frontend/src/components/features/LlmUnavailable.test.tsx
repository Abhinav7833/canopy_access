import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LlmUnavailable } from "@/components/features/LlmUnavailable";

describe("LlmUnavailable", () => {
  it("renders a neutral empty-result message for the capability", () => {
    render(<LlmUnavailable capability="answer" />);
    expect(screen.getByText("No answer to show yet.")).toBeInTheDocument();
  });

  it("says nothing about missing configuration, a language model, or an unimplemented feature", () => {
    const { container } = render(<LlmUnavailable capability="memo" />);
    expect(container.textContent).not.toMatch(
      /language model|configured|wired up|not implemented|unavailable|optional/i,
    );
  });
});
