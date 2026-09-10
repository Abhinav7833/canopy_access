import { act, fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";
import { MetricInfo, MetricLabel, ScaleCue } from "@/components/ui/MetricInfo";

const trigger = (name: RegExp) => screen.getByRole("button", { name });
const wrapperOf = (name: RegExp) => trigger(name).parentElement as HTMLElement;

/** Real focus (so `toHaveFocus` means what it says), flushed through React. */
const focus = (el: HTMLElement) => act(() => el.focus());

describe("MetricInfo", () => {
  it("stays closed until asked", () => {
    render(<MetricInfo metric="riskScore" />);
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    expect(trigger(/about risk score/i)).toHaveAttribute("aria-expanded", "false");
  });

  it("opens on keyboard focus, so the description is not hover-only", () => {
    render(<MetricInfo metric="riskScore" />);
    focus(trigger(/about risk score/i));
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
  });

  it("opens on tap without flashing shut", () => {
    render(<MetricInfo metric="riskScore" />);
    const button = trigger(/about risk score/i);
    // A tap focuses the button and then clicks it — both must leave the panel open.
    focus(button);
    fireEvent.click(button);
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
  });

  it("closes on Escape and returns focus to the trigger", () => {
    render(<MetricInfo metric="riskScore" />);
    const button = trigger(/about risk score/i);
    focus(button);
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
    fireEvent.keyDown(document, { key: "Escape" });
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    expect(button).toHaveFocus();
  });

  it("closes on a pointer press outside it", () => {
    render(<MetricInfo metric="riskScore" />);
    fireEvent.click(trigger(/about risk score/i));
    expect(screen.getByRole("tooltip")).toBeInTheDocument();
    fireEvent.pointerDown(document.body);
    expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
  });

  it("stays open while the pointer moves off the icon onto the panel", () => {
    // The panel is portalled to the body, so moving toward it leaves the trigger's wrapper;
    // the grace period plus the panel's own hover must keep it up to be read.
    vi.useFakeTimers();
    try {
      render(<MetricInfo metric="riskScore" />);
      fireEvent.mouseEnter(wrapperOf(/about risk score/i));
      expect(screen.getByRole("tooltip")).toBeInTheDocument();
      fireEvent.mouseLeave(wrapperOf(/about risk score/i)); // schedules close
      fireEvent.mouseEnter(screen.getByRole("tooltip")); // cancels it
      act(() => vi.advanceTimersByTime(300));
      expect(screen.getByRole("tooltip")).toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("closes shortly after the pointer leaves both the icon and the panel", () => {
    vi.useFakeTimers();
    try {
      render(<MetricInfo metric="riskScore" />);
      fireEvent.mouseEnter(wrapperOf(/about risk score/i));
      fireEvent.mouseLeave(wrapperOf(/about risk score/i));
      act(() => vi.advanceTimersByTime(300));
      expect(screen.queryByRole("tooltip")).not.toBeInTheDocument();
    } finally {
      vi.useRealTimers();
    }
  });

  it("portals the panel out of its trigger's parent", () => {
    // Triggers sit inside <p> and <span> elements. A block-level panel nested there is
    // invalid HTML and breaks hydration, so the panel must land on the body instead.
    render(
      <p>
        <MetricInfo metric="riskScore" />
      </p>,
    );
    fireEvent.click(trigger(/about risk score/i));
    expect(screen.getByRole("tooltip").parentElement).toBe(document.body);
  });

  it("describes the trigger by the open panel", () => {
    render(<MetricInfo metric="riskScore" />);
    const button = trigger(/about risk score/i);
    fireEvent.click(button);
    expect(button).toHaveAttribute("aria-describedby", screen.getByRole("tooltip").id);
    expect(button).toHaveAttribute("aria-expanded", "true");
  });

  it("states the range as a percent and the direction, without a band ladder", () => {
    render(<MetricInfo metric="riskScore" />);
    fireEvent.click(trigger(/about risk score/i));
    const panel = screen.getByRole("tooltip");
    expect(panel).toHaveTextContent("0–100%");
    expect(panel).toHaveTextContent(/higher = more risk/i);
    // The band chip is already on screen; the tooltip does not re-enumerate the cutoffs.
    expect(panel).not.toHaveTextContent("Low <25");
  });

  it("omits the scale when the surface already states it", () => {
    // The hazard cards state the scale once in a footer; repeating it per row would put the
    // same sentence on screen twice at once.
    render(<MetricInfo metric="riskScore" showScale={false} />);
    fireEvent.click(trigger(/about risk score/i));
    const panel = screen.getByRole("tooltip");
    expect(panel).not.toHaveTextContent("0–100%");
    // What the metric means and what feeds it still show — that is the row-specific part.
    expect(panel).toHaveTextContent(/physical hazard to the asset/i);
    expect(panel).toHaveTextContent(/worst of fire and flood/i);
  });

  it("says the composite is the worst hazard, not an average", () => {
    render(<MetricInfo metric="hazardComposite" />);
    fireEvent.click(trigger(/about composite/i));
    expect(screen.getByRole("tooltip")).toHaveTextContent(/not an average/i);
  });

  it("says heat is unscored rather than inventing a method for it", () => {
    render(<MetricInfo metric="heat" />);
    fireEvent.click(trigger(/about heat/i));
    const panel = screen.getByRole("tooltip");
    expect(panel).toHaveTextContent(/not scored/i);
    // An unscored metric must not claim a scale.
    expect(panel).not.toHaveTextContent("0–100");
  });
});

describe("MetricLabel", () => {
  it("renders the registry label beside its trigger", () => {
    render(<MetricLabel metric="fire" />);
    expect(screen.getByText("Fire")).toBeInTheDocument();
    expect(trigger(/about fire/i)).toBeInTheDocument();
  });
});

describe("ScaleCue", () => {
  it("states direction on the page for the two opposing headline metrics", () => {
    const { rerender } = render(<ScaleCue metric="riskScore" />);
    expect(screen.getByText("Higher = more risk")).toBeInTheDocument();
    rerender(<ScaleCue metric="onTrackConfidence" />);
    expect(screen.getByText("Higher = better")).toBeInTheDocument();
  });

  it("renders nothing for a metric that has no scale", () => {
    const { container } = render(<ScaleCue metric="heat" />);
    expect(container).toBeEmptyDOMElement();
  });
});
