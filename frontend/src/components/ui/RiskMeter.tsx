import { Badge } from "@/components/ui/Badge";
import { riskTone, TONE_BG, type RiskTone } from "@/lib/format";

export function RiskBar({
  score,
  tone,
  className = "",
}: {
  score: number | null;
  tone: RiskTone;
  className?: string;
}) {
  const pct = Math.max(0, Math.min(100, score ?? 0));
  return (
    <div className={`h-1.5 overflow-hidden rounded-full bg-surface-muted ${className}`}>
      <div className={`h-full rounded-full ${TONE_BG[tone]}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

/** Compact rating for table cells: the numeric score (neutral, tabular) paired with its risk
 * band as a filled chip — the same score+band language the ConfidenceRating gauge uses. */
export function RiskScore({
  score,
  band,
  className = "",
}: {
  score: number | null;
  band: string | null;
  className?: string;
}) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="font-mono text-sm font-semibold tabular-nums text-ink">{score ?? "—"}</span>
      {band ? (
        <Badge tone={riskTone(band)}>{band}</Badge>
      ) : (
        <span className="text-faint">—</span>
      )}
    </div>
  );
}
