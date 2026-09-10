"use client";
import { ConfidenceRating } from "@/components/features/ConfidenceRating";
import { useDossier, useProject } from "@/lib/queries";
import { titleCase } from "@/lib/format";

/** Persistent per-project header. The headline is the dossier's on-track confidence,
 * shown as a rating gauge alongside the risk band (see
 * docs/specs/2026-07-13-canopy-disclosure-direction.md). Falls back to the project's own
 * risk_score/band if the dossier isn't available so the header degrades gracefully. */
export function ProjectHeader({ id }: { id: string }) {
  const { data: p, isError } = useProject(id);
  const { data: dossier } = useDossier(id);
  if (isError) return null;
  if (!p) {
    return <div className="h-10 w-72 animate-pulse rounded bg-surface-muted" />;
  }
  const meta = [titleCase(p.asset_type), p.country, titleCase(p.financing_type)].filter(
    (x): x is string => Boolean(x) && x !== "—",
  );
  const onTrackPct = dossier?.confidence?.on_track_pct ?? null;
  const band = dossier?.confidence?.risk_band ?? p.risk_band;
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{p.name}</h1>
        <p className="mt-1 text-sm text-muted">{meta.join("  ·  ")}</p>
      </div>
      {band && <ConfidenceRating pct={onTrackPct} band={band} />}
    </div>
  );
}
