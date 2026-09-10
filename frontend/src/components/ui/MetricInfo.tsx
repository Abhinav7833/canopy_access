"use client";
import { useEffect, useId, useLayoutEffect, useRef, useState, type ReactNode } from "react";
import { createPortal } from "react-dom";
import { DIRECTION_LABEL, METRICS, scaleLine, type MetricKey } from "@/lib/metrics";

const PANEL_W = 288;
const GAP = 8;
const EDGE = 12;

/** Anchors the open panel to its trigger, in viewport coordinates.
 *
 * The panel is `position: fixed` rather than absolute: several of these triggers sit inside
 * `overflow-hidden` cards and table shells, which would clip an absolutely positioned box.
 * Nothing in the layout establishes a containing block (no transform/filter ancestors), so
 * the trigger's rect is exact.
 *
 * Position is written straight to the node rather than held in state — it is a measurement of
 * the DOM fed back to the DOM, and routing it through a render would cascade one on every
 * scroll frame. The panel mounts hidden and this reveals it once placed. */
function useAnchoredPosition(
  open: boolean,
  triggerRef: React.RefObject<HTMLButtonElement | null>,
  panelRef: React.RefObject<HTMLDivElement | null>,
) {
  useLayoutEffect(() => {
    if (!open) return;
    const place = () => {
      const trigger = triggerRef.current;
      const panel = panelRef.current;
      if (!trigger || !panel) return;
      const r = trigger.getBoundingClientRect();
      const h = panel.offsetHeight;
      // Prefer below; flip above only when below would overflow and above actually fits.
      const below = r.bottom + GAP;
      const fitsBelow = below + h + EDGE <= window.innerHeight;
      const fitsAbove = r.top - GAP - h >= EDGE;
      const top = fitsBelow || !fitsAbove ? below : r.top - GAP - h;
      // Centre on the trigger, then clamp so the panel never leaves the viewport.
      const centred = r.left + r.width / 2 - PANEL_W / 2;
      const left = Math.min(Math.max(EDGE, centred), window.innerWidth - PANEL_W - EDGE);
      panel.style.top = `${top}px`;
      panel.style.left = `${left}px`;
      panel.style.visibility = "visible";
    };
    place();
    // `true` captures scrolls on any ancestor, not just the window.
    window.addEventListener("scroll", place, true);
    window.addEventListener("resize", place);
    return () => {
      window.removeEventListener("scroll", place, true);
      window.removeEventListener("resize", place);
    };
  }, [open, triggerRef, panelRef]); // refs are stable; listed to satisfy exhaustive-deps
}

/** One shared element, not a component: identical by reference across every trigger, so React
 * skips reconciling the subtree. */
const INFO_GLYPH = (
  <svg
    viewBox="0 0 16 16"
    width="14"
    height="14"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    aria-hidden
  >
    <circle cx="8" cy="8" r="6.25" />
    <path d="M8 7.4v3.4" strokeLinecap="round" />
    <circle cx="8" cy="5.1" r="0.85" fill="currentColor" stroke="none" />
  </svg>
);

/** What a number means and on what scale, on hover, focus or tap.
 *
 * Hover alone would leave the explanation invisible on touch and to screen readers, so the
 * trigger is a real button: pointer, keyboard and tap all open the same panel, and the panel
 * is wired by `aria-describedby` so it is announced rather than merely drawn. */
export function MetricInfo({
  metric,
  showScale = true,
}: {
  metric: MetricKey;
  /** Pass false where the surrounding surface already states the scale — a hazard card puts
   * it in one footer for the whole list, and repeating it per row would put the same sentence
   * on screen twice at once. */
  showScale?: boolean;
}) {
  const doc = METRICS[metric];
  const id = useId();
  const [open, setOpen] = useState(false);
  const triggerRef = useRef<HTMLButtonElement>(null);
  const panelRef = useRef<HTMLDivElement>(null);
  const closeTimer = useRef<ReturnType<typeof setTimeout> | null>(null);
  useAnchoredPosition(open, triggerRef, panelRef);

  const cancelClose = () => {
    if (closeTimer.current) clearTimeout(closeTimer.current);
    closeTimer.current = null;
  };
  const openNow = () => {
    cancelClose();
    setOpen(true);
  };
  // Close after a short grace period, not instantly: the panel is portalled to the body, so it
  // isn't a DOM child of the trigger, and moving the pointer from the icon across the gap into
  // the panel briefly leaves both. The panel's own mouseenter cancels this, so it stays up to
  // be read or have its reference text selected.
  const scheduleClose = () => {
    cancelClose();
    closeTimer.current = setTimeout(() => setOpen(false), 120);
  };
  useEffect(() => cancelClose, []);

  useEffect(() => {
    if (!open) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === "Escape") {
        setOpen(false);
        triggerRef.current?.focus();
      }
    };
    const onPointerDown = (e: PointerEvent) => {
      const t = e.target as Node;
      if (!triggerRef.current?.contains(t) && !panelRef.current?.contains(t)) setOpen(false);
    };
    document.addEventListener("keydown", onKey);
    document.addEventListener("pointerdown", onPointerDown);
    return () => {
      document.removeEventListener("keydown", onKey);
      document.removeEventListener("pointerdown", onPointerDown);
    };
  }, [open]);

  return (
    <span className="inline-flex" onMouseEnter={openNow} onMouseLeave={scheduleClose}>
      <button
        ref={triggerRef}
        type="button"
        aria-label={`About ${doc.label}`}
        aria-expanded={open}
        aria-describedby={open ? id : undefined}
        onFocus={openNow}
        onBlur={scheduleClose}
        // Opens, never toggles: a tap focuses the button first, so toggling here would make
        // the panel flash open and shut on touch. Dismissal is Escape or a tap outside.
        onClick={openNow}
        className="inline-flex items-center justify-center rounded-full text-faint transition-colors hover:text-accent focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-accent"
      >
        {INFO_GLYPH}
      </button>
      {/* Portalled to the body: triggers sit inside `<p>` and `<span>` elements, where a
          block-level panel would be invalid HTML and break hydration. It also puts the panel
          past any card's stacking context. Never runs on the server — `open` starts false. */}
      {open &&
        createPortal(
          <div
            ref={panelRef}
            id={id}
            role="tooltip"
            onMouseEnter={openNow}
            onMouseLeave={scheduleClose}
            style={{
              position: "fixed",
              top: 0,
              left: 0,
              width: PANEL_W,
              // Mounts hidden; the layout effect measures it, places it and reveals it — all
              // before the browser paints, so it never appears in the wrong spot.
              visibility: "hidden",
            }}
            className="z-50 rounded-card border border-border bg-surface p-3.5 text-left shadow-overlay"
          >
            <p className="label">{doc.label}</p>
            <p className="mt-1.5 text-sm leading-relaxed text-ink">{doc.summary}</p>
            {showScale && doc.scale && (
              <p className="mt-2 font-mono text-xs leading-relaxed text-muted">
                {scaleLine(doc.scale)}
              </p>
            )}
            {doc.inputs && (
              <p className="mt-2.5 border-t border-border pt-2.5 text-xs leading-relaxed text-muted">
                {doc.inputs}
              </p>
            )}
          </div>,
          document.body,
        )}
    </span>
  );
}

/** A metric's name with its description trigger — the shape every call site wants.
 *
 * `children` overrides the visible text for the case where the metric is presented by its
 * value rather than its name (the AOI assurance line); the trigger still announces the
 * registry label, so the accessible name stays stable. */
export function MetricLabel({
  metric,
  children,
  className = "",
  labelClassName = "",
  showScale = true,
}: {
  metric: MetricKey;
  children?: ReactNode;
  className?: string;
  labelClassName?: string;
  showScale?: boolean;
}) {
  return (
    <span className={`inline-flex items-center gap-1.5 ${className}`}>
      <span className={labelClassName}>{children ?? METRICS[metric].label}</span>
      <MetricInfo metric={metric} showScale={showScale} />
    </span>
  );
}

/** The always-visible half of the fix: direction stated on the page, so a screenshot or a
 * touch reader still gets it. */
export function ScaleCue({ metric, className = "" }: { metric: MetricKey; className?: string }) {
  const scale = METRICS[metric].scale;
  if (!scale) return null;
  return <span className={`label ${className}`}>{DIRECTION_LABEL[scale.direction]}</span>;
}
