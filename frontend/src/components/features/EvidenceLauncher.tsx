"use client";
import { useState } from "react";
import { EvidenceDrawer } from "@/components/features/EvidenceDrawer";

/** Persistent entry point to the per-project evidence sheet (source & methodology),
 * reachable from every dossier tab. Restores the trigger lost when the metrics page —
 * previously the only thing that opened EvidenceDrawer — was removed in the
 * disclosure-direction rebuild. */
export function EvidenceLauncher({ id }: { id: string }) {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        onClick={() => setOpen(true)}
        className="shrink-0 rounded-md border border-border px-3 py-1.5 text-sm font-medium text-muted transition-colors hover:bg-surface-muted hover:text-ink"
      >
        Evidence
      </button>
      <EvidenceDrawer id={id} open={open} onClose={() => setOpen(false)} />
    </>
  );
}
