/** Small mono chip surfacing a dossier value's evidence-graph trace, e.g. "← disclosure" or
 * "← claim:capacity_mw" — the visual thread for "every figure traces to the disclosure". */
export function TraceChip({
  traces_to,
  className = "",
}: {
  traces_to?: string | null;
  className?: string;
}) {
  if (!traces_to) return null;
  const label =
    traces_to === "disclosure" ? "disclosure" : `claim:${traces_to.replace(/^claim_/, "")}`;
  return (
    <span
      className={`inline-flex w-fit items-center gap-1 whitespace-nowrap rounded-md border border-border bg-surface-muted px-1.5 py-0.5 font-mono text-[11px] text-muted ${className}`}
    >
      ← {label}
    </span>
  );
}
