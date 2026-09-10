import type { ReactNode } from "react";
import type { RiskTone } from "@/lib/format";

const TONES: Record<string, string> = {
  neutral: "bg-surface-muted text-muted border-border",
  low: "bg-risk-low-soft text-risk-low border-risk-low-border",
  medium: "bg-risk-med-soft text-risk-med border-risk-med-border",
  high: "bg-risk-high-soft text-risk-high border-risk-high-border",
  critical: "bg-risk-high-soft text-risk-critical border-risk-high-border",
  accent: "bg-accent-soft text-accent border-accent-border",
};

export function Badge({
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
      className={`inline-flex items-center gap-1.5 rounded-md border px-2 py-0.5 text-xs font-medium ${TONES[tone] ?? TONES.neutral} ${className}`}
    >
      {children}
    </span>
  );
}
