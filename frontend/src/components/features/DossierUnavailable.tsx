"use client";
import { EmptyState } from "@/components/ui/Card";
import { ApiError } from "@/lib/api";

/** The right non-data state for a dossier-driven page. A project can be listed (DB-backed)
 * without a dossier fixture yet — that 404 is a "not recorded yet" empty state, not a
 * failure — so only genuine errors get the alarming backend-unreachable card. `noun` names
 * the missing layer (e.g. "disclosure", "confidence"). */
export function DossierUnavailable({ error, noun }: { error: unknown; noun: string }) {
  const notSeeded = error instanceof ApiError && error.status === 404;
  if (notSeeded)
    return <EmptyState>No {noun} has been recorded for this asset yet.</EmptyState>;
  return (
    <div className="rounded-card border border-risk-high-border bg-risk-high-soft px-5 py-4 text-sm text-risk-high">
      Could not load the {noun}. Confirm the backend is running on <code>:8001</code>.
    </div>
  );
}
