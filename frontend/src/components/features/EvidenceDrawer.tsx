"use client";
import { EvidenceCard } from "@/components/features/EvidenceCard";
import { useEvidence } from "@/lib/queries";

export function EvidenceDrawer({
  id,
  open,
  onClose,
}: {
  id: string;
  open: boolean;
  onClose: () => void;
}) {
  const { data, isLoading } = useEvidence(id, open);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-20 flex justify-end">
      <button aria-label="Close evidence" className="absolute inset-0 bg-ink/40" onClick={onClose} />
      <div className="relative flex h-full w-full max-w-md flex-col border-l border-border bg-surface shadow-overlay">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <div>
            <p className="label mb-1">Evidence</p>
            <h2 className="text-sm font-semibold text-ink">Source &amp; methodology</h2>
          </div>
          <button
            aria-label="Close"
            onClick={onClose}
            className="rounded-md p-1.5 text-muted transition-colors hover:bg-surface-muted hover:text-ink"
          >
            ✕
          </button>
        </div>
        <div className="flex-1 overflow-y-auto px-5 py-4">
          {isLoading ? (
            <div className="space-y-3">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="h-24 animate-pulse rounded-card border border-border bg-surface-muted" />
              ))}
            </div>
          ) : data && data.length > 0 ? (
            <div className="space-y-3">
              {data.map((e) => (
                <EvidenceCard key={e.id} evidence={e} />
              ))}
            </div>
          ) : (
            <p className="text-sm text-muted">No evidence recorded for this asset.</p>
          )}
        </div>
      </div>
    </div>
  );
}
