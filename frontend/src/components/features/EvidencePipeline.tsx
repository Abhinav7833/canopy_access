/** The disclosure → confidence narrative as a numbered, connected 5-node strip — the "how it
 * works" explainer on the landing page. Presentation only; the final node (the confidence rating,
 * the product) is accented as the arrival point. Nodes are static by design — the hero CTA is the
 * single conversion path — which keeps this a pure server component, reusable later as an in-app
 * rail. Order is the story (see docs/specs/2026-07-13-canopy-disclosure-direction.md). */
const STAGES = [
  { label: "Disclosure", detail: "The financed claims, exactly as disclosed." },
  { label: "Locate", detail: "The claimed region, resolved to one asset." },
  { label: "Observe", detail: "Sentinel snapshots tracking build progress over time." },
  { label: "Cross-check", detail: "Promised versus what the satellite record shows." },
  { label: "Confidence", detail: "One explained rating, every figure traced to its evidence." },
];

export function EvidencePipeline({ className = "" }: { className?: string }) {
  return (
    <ol className={`relative grid grid-cols-1 gap-8 md:grid-cols-5 md:gap-0 ${className}`}>
      {/* Connector rail: one hairline behind the badges, spanning badge-1's centre to badge-5's
          (5 equal 20%-wide columns → centres at 10/30/50/70/90%). Badges paint over it. */}
      <span
        aria-hidden
        className="pointer-events-none absolute inset-x-[10%] top-5 hidden h-px -translate-y-1/2 bg-border md:block"
      />
      {STAGES.map((stage, i) => {
        const isLast = i === STAGES.length - 1;
        return (
          <li
            key={stage.label}
            className="flex items-start gap-4 md:flex-col md:items-center md:gap-3 md:px-3 md:text-center"
          >
            <span
              className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-full border font-mono text-sm ${
                isLast
                  ? "border-accent-border bg-accent text-accent-ink"
                  : "border-border bg-surface text-ink"
              }`}
            >
              {i + 1}
            </span>
            <div>
              <h3 className="text-[15px] font-medium text-ink">{stage.label}</h3>
              <p className="mt-1 text-sm leading-relaxed text-muted">{stage.detail}</p>
            </div>
          </li>
        );
      })}
    </ol>
  );
}
