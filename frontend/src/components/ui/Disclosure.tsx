import type { ReactNode } from "react";

/** Shared by every expandable-row surface (the legal checks, the confidence explainer), so the
 * chevron, the marker reset and the open/closed rotation live in one place. */
const CHEVRON = (
  <svg
    viewBox="0 0 16 16"
    width="14"
    height="14"
    fill="none"
    stroke="currentColor"
    strokeWidth="1.5"
    strokeLinecap="round"
    strokeLinejoin="round"
    aria-hidden
  >
    <path d="M4 6.5 8 10.5 12 6.5" />
  </svg>
);

/** A click-to-expand region built on native `<details>/<summary>`.
 *
 * The element carries the behaviour we'd otherwise hand-roll: keyboard activation, the
 * expanded/collapsed state being announced, and independent open state. (Note a collapsed
 * `<details>` hides its body in print too — a row left closed won't appear in a PDF, so pass
 * `defaultOpen` for content that must survive being circulated.)
 *
 * This owns only the generic chrome; padding, borders and hover come from the caller via
 * `summaryClassName`/`bodyClassName`, because a full-width row in a card and a compact inline
 * toggle want different spacing. `aside` sits between the summary text and the chevron, for a
 * status pill or count that belongs on the collapsed row. */
export function Disclosure({
  summary,
  aside,
  children,
  defaultOpen = false,
  className = "",
  summaryClassName = "",
  bodyClassName = "",
}: {
  summary: ReactNode;
  aside?: ReactNode;
  children: ReactNode;
  defaultOpen?: boolean;
  className?: string;
  summaryClassName?: string;
  bodyClassName?: string;
}) {
  return (
    <details open={defaultOpen || undefined} className={`group ${className}`}>
      <summary
        className={`flex cursor-pointer list-none items-start justify-between gap-4 [&::-webkit-details-marker]:hidden ${summaryClassName}`}
      >
        <span className="min-w-0">{summary}</span>
        <span className="flex shrink-0 items-center gap-2.5">
          {aside}
          <span className="text-faint transition-transform group-open:rotate-180">{CHEVRON}</span>
        </span>
      </summary>
      <div className={bodyClassName}>{children}</div>
    </details>
  );
}
