import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { Disclosure } from "@/components/ui/Disclosure";

const row = (): HTMLDetailsElement =>
  screen.getByText("Summary text").closest("details") as HTMLDetailsElement;

describe("Disclosure", () => {
  it("renders the summary and its aside, with the body hidden until opened", () => {
    render(
      <Disclosure summary="Summary text" aside={<span>Aside</span>}>
        <p>Body text</p>
      </Disclosure>,
    );
    expect(screen.getByText("Summary text")).toBeInTheDocument();
    expect(screen.getByText("Aside")).toBeInTheDocument();
    // The body is in the DOM (native <details>) but the element is collapsed.
    expect(row().open).toBe(false);
  });

  it("starts open when asked", () => {
    render(
      <Disclosure summary="Summary text" defaultOpen>
        <p>Body text</p>
      </Disclosure>,
    );
    expect(row().open).toBe(true);
  });

  it("toggles open on summary click", () => {
    render(
      <Disclosure summary="Summary text">
        <p>Body text</p>
      </Disclosure>,
    );
    const details = row();
    expect(details.open).toBe(false);
    // jsdom implements the native toggle on the <summary>.
    screen.getByText("Summary text").closest("summary")!.click();
    expect(details.open).toBe(true);
  });

  it("applies caller-controlled classes so a row and an inline toggle can differ", () => {
    render(
      <Disclosure
        summary="Summary text"
        className="border-b"
        summaryClassName="px-5"
        bodyClassName="pt-3"
      >
        <p>Body text</p>
      </Disclosure>,
    );
    expect(row()).toHaveClass("border-b");
    expect(screen.getByText("Summary text").closest("summary")).toHaveClass("px-5");
    expect(screen.getByText("Body text").parentElement).toHaveClass("pt-3");
  });
});
