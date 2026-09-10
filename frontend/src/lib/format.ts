/** Presentation helpers: turn raw API values into display-ready strings. */

/** Title Case every word: "development_finance" -> "Development Finance". */
export function titleCase(value: string | null | undefined): string {
  if (!value) return "—";
  return value
    .replace(/[_-]+/g, " ")
    .trim()
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

export function formatNumber(
  value: number | null | undefined,
  opts: { decimals?: number; unit?: string | null } = {},
): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const { decimals, unit } = opts;
  const n = value.toLocaleString("en-US", {
    minimumFractionDigits: decimals ?? 0,
    maximumFractionDigits: decimals ?? 2,
  });
  return unit ? `${n} ${unit}` : n;
}

/** 0.72 -> "72%"; already-percent metrics can pass asRatio=false. */
export function formatPercent(value: number | null | undefined, asRatio = false): string {
  if (value === null || value === undefined || Number.isNaN(value)) return "—";
  const pct = asRatio ? value * 100 : value;
  return `${pct.toLocaleString("en-US", { maximumFractionDigits: 1 })}%`;
}

export function formatDate(value: string | null | undefined): string {
  if (!value) return "—";
  // Date-only / month-only values are parsed as UTC so the calendar day/month
  // shown never shifts backward for users west of UTC.
  if (/^\d{4}-\d{2}$/.test(value)) {
    const d = new Date(`${value}-01T00:00:00Z`);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleDateString("en-US", { year: "numeric", month: "short", timeZone: "UTC" });
  }
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) {
    const d = new Date(`${value}T00:00:00Z`);
    if (Number.isNaN(d.getTime())) return value;
    return d.toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "2-digit",
      timeZone: "UTC",
    });
  }
  const d = new Date(value);
  if (Number.isNaN(d.getTime())) return value;
  return d.toLocaleDateString("en-US", { year: "numeric", month: "short", day: "2-digit" });
}

export type RiskTone = "low" | "medium" | "high" | "critical" | "neutral";

/** Map a risk band string to a semantic tone used by badges / meters. */
export function riskTone(band: string | null | undefined): RiskTone {
  switch ((band ?? "").toLowerCase()) {
    case "low":
      return "low";
    case "medium":
      return "medium";
    case "high":
      return "high";
    case "critical":
      return "critical";
    default:
      return "neutral";
  }
}

/** Confidence is "good when high" — invert onto the risk ramp so high confidence reads green. */
export function confidenceTone(confidence: string | null | undefined): RiskTone {
  switch ((confidence ?? "").toLowerCase()) {
    case "high":
      return "low";
    case "medium":
      return "medium";
    case "low":
      return "high";
    default:
      return "neutral";
  }
}

/** Cutoffs for a numeric confidence ratio — named rather than inline so the two thresholds
 * `confidenceValueTone` applies read as one scale. Frontend-owned: the API returns a raw float. */
const CONFIDENCE_HIGH = 0.75;
const CONFIDENCE_MEDIUM = 0.5;

/** Numeric confidence ratio (0-1, e.g. localization.confidence) -> tone, on the same
 * "high confidence reads green" scale as confidenceTone (which takes the string
 * high/medium/low form instead). */
export function confidenceValueTone(value: number | null | undefined): RiskTone {
  if (value === null || value === undefined || Number.isNaN(value)) return "neutral";
  if (value >= CONFIDENCE_HIGH) return "low";
  if (value >= CONFIDENCE_MEDIUM) return "medium";
  return "high";
}

/** Cross-check verdict -> tone. Agreement reads green; agreement only on the observable part
 * reads amber, since the claim itself stays unverified; a contradicted claim is the one thing
 * here that escalates to red. An unjudgeable check is neutral, not reassuring. */
export function crossCheckTone(status: string | null | undefined): RiskTone {
  switch ((status ?? "").toLowerCase()) {
    case "consistent":
      return "low";
    case "partially_consistent":
      return "medium";
    case "inconsistent":
      return "high";
    default:
      return "neutral";
  }
}

/** Canonical tone → Tailwind class maps — the single source for risk/confidence coloring. */
export const TONE_BG: Record<RiskTone, string> = {
  low: "bg-risk-low",
  medium: "bg-risk-med",
  high: "bg-risk-high",
  critical: "bg-risk-critical",
  neutral: "bg-faint",
};

export const TONE_TEXT: Record<RiskTone, string> = {
  low: "text-risk-low",
  medium: "text-risk-med",
  high: "text-risk-high",
  critical: "text-risk-critical",
  neutral: "text-muted",
};
