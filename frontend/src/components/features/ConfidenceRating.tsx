"use client";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { arcOffset, circumference } from "@/lib/gauge";
import { riskTone } from "@/lib/format";

const STROKE: Record<string, string> = {
  low: "var(--color-risk-low)",
  medium: "var(--color-risk-med)",
  high: "var(--color-risk-high)",
  critical: "var(--color-risk-critical)",
  neutral: "var(--color-faint)",
};

/** The dossier's on-track confidence, presented as a rating: a band-colored SVG gauge
 * with the score and risk band. The one number the committee acts on. */
export function ConfidenceRating({
  pct,
  band,
  size = 116,
}: {
  pct: number | null;
  band: string | null;
  size?: number;
}) {
  const stroke = 9;
  const r = size / 2 - stroke;
  const circ = circumference(r);
  const target = arcOffset(pct, r);
  const tone = riskTone(band);

  // Start empty on the server (deterministic → no hydration mismatch), then fill on
  // mount. Reduced-motion is handled globally in globals.css (transition-duration → ~0),
  // so we intentionally don't read matchMedia here (that would desync SSR vs client).
  const [offset, setOffset] = useState(circ);
  useEffect(() => {
    const raf = requestAnimationFrame(() => requestAnimationFrame(() => setOffset(target)));
    return () => cancelAnimationFrame(raf);
  }, [target]);

  const c = size / 2;
  return (
    <div className="flex items-center gap-4">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="-rotate-90"
          role="img"
          aria-label={`On-track confidence ${pct ?? "unknown"} percent${band ? `, ${band} risk` : ""}`}
        >
          <circle cx={c} cy={c} r={r} fill="none" stroke="var(--color-border-strong)" strokeWidth={stroke} />
          <circle
            cx={c}
            cy={c}
            r={r}
            fill="none"
            stroke={STROKE[tone] ?? STROKE.neutral}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            style={{ transition: "stroke-dashoffset 1s cubic-bezier(.2,.7,.2,1)" }}
          />
        </svg>
        <div className="absolute inset-0 grid place-content-center text-center">
          <div className="font-mono text-3xl font-semibold leading-none tabular-nums text-ink">
            {pct ?? "—"}
            <span className="align-top text-sm font-normal text-muted">%</span>
          </div>
          <div className="label mt-1.5">On track</div>
        </div>
      </div>
      {band && (
        <div className="flex flex-col items-start gap-1.5">
          <span className="label">Risk band</span>
          <Badge tone={tone}>{band}</Badge>
        </div>
      )}
    </div>
  );
}
