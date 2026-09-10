import type { ReactNode } from "react";
import { TONE_BG, type RiskTone } from "@/lib/format";

const DOT: Record<string, string> = {
  ...TONE_BG,
  accent: "bg-accent",
};

/** A status as a semantic dot + label — the quiet counterpart to the filled `Badge` (which we
 * reserve for risk bands). The dot carries the color; the text carries the meaning, so the dot
 * is aria-hidden. Used for cross-check outcomes (met / on-track / behind / variance). */
export function StatusPill({
  tone = "neutral",
  children,
  className = "",
}: {
  tone?: RiskTone | "accent";
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap text-xs font-medium text-ink ${className}`}
    >
      <span
        aria-hidden
        className={`h-1.5 w-1.5 shrink-0 rounded-full ${DOT[tone] ?? DOT.neutral}`}
      />
      {children}
    </span>
  );
}
