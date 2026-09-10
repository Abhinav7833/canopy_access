import type { ReactNode } from "react";
import { MetricLabel } from "@/components/ui/MetricInfo";
import { METRICS, scaleLine, type MetricKey } from "@/lib/metrics";

/** A labelled figure.
 *
 * Pass `metric` rather than `label` whenever the figure is one the registry describes: the
 * label, the description trigger and the scale caption all come from the registry, so a tile
 * cannot end up stating a scale in wording no other screen uses. `label` remains for the
 * handful of tiles that are not metrics ("Assets", "Evidence"). */
export function Stat({
  metric,
  label,
  value,
  sub,
  tone = "default",
}: {
  metric?: MetricKey;
  label?: ReactNode;
  value: ReactNode;
  /** Overrides the registry's scale caption when the tile has something more useful to say. */
  sub?: ReactNode;
  tone?: "default" | "accent";
}) {
  const scale = metric ? METRICS[metric].scale : undefined;
  // When no `sub` overrides it, the caption already prints the scale line — so the info
  // popover must not print it a second time right below.
  const captionIsScale = !sub && !!scale;
  const caption = sub ?? (scale ? scaleLine(scale) : undefined);
  return (
    <div className="rounded-card border border-border bg-surface p-4 shadow-card">
      <p className="label">
        {metric ? <MetricLabel metric={metric} showScale={!captionIsScale} /> : label}
      </p>
      <p
        className={`mt-2 font-mono text-2xl font-semibold tabular-nums ${
          tone === "accent" ? "text-accent" : "text-ink"
        }`}
      >
        {value}
      </p>
      {caption && <div className="mt-1 text-xs text-muted">{caption}</div>}
    </div>
  );
}
