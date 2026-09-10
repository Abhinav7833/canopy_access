import type { ReactNode } from "react";

export function Card({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return (
    <div className={`rounded-card border border-border bg-surface shadow-card ${className}`}>
      {children}
    </div>
  );
}

export function CardHeader({ title, action }: { title: ReactNode; action?: ReactNode }) {
  return (
    <div className="flex items-center justify-between gap-3 border-b border-border px-5 py-3">
      <h3 className="text-sm font-semibold text-ink">{title}</h3>
      {action}
    </div>
  );
}

export function CardBody({
  children,
  className = "",
}: {
  children: ReactNode;
  className?: string;
}) {
  return <div className={`px-5 py-4 ${className}`}>{children}</div>;
}

/** Card-shaped loading placeholder. Shared by the dossier pages so their loading chrome
 * lives in one place, next to `DossierUnavailable` (their error/empty state). */
export function CardSkeleton({ className = "h-64" }: { className?: string }) {
  return <div className={`animate-pulse rounded-card border border-border bg-surface ${className}`} />;
}

/** Loaded-but-empty state: a centered message in a card shell. Distinct from
 * `DossierUnavailable` (which is for the error / not-seeded-yet case). */
export function EmptyState({ children }: { children: ReactNode }) {
  return (
    <div className="rounded-card border border-border bg-surface px-5 py-12 text-center text-sm text-muted shadow-card">
      {children}
    </div>
  );
}
