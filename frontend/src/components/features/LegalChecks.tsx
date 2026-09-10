import { Card, CardHeader } from "@/components/ui/Card";
import { Disclosure } from "@/components/ui/Disclosure";
import { StatusPill } from "@/components/ui/StatusPill";
import { TraceChip } from "@/components/features/TraceChip";
import { crossCheckTone, formatDate, titleCase } from "@/lib/format";
import type { LegalCheck } from "@/lib/types";

/** One check, collapsed to its verdict and expandable to the evidence behind it. */
function LegalRow({ check }: { check: LegalCheck }) {
  return (
    <Disclosure
      className="border-b border-border last:border-0"
      summaryClassName="px-5 py-3.5 transition-colors hover:bg-surface-muted"
      bodyClassName="space-y-3.5 px-5 pb-4"
      summary={
        <span className="text-sm">
          <span className="font-medium text-ink">{titleCase(check.check_type)}</span>
          <span aria-hidden className="text-faint">{" · "}</span>
          <span className="text-muted">{check.subject}</span>
        </span>
      }
      aside={
        <StatusPill tone={crossCheckTone(check.verdict)}>{titleCase(check.verdict)}</StatusPill>
      }
    >
      {check.detail && <p className="text-sm leading-relaxed text-ink">{check.detail}</p>}
      {(check.authority || check.as_of) && (
        <div>
          <p className="label">Authority</p>
          <p className="mt-1.5 text-sm text-muted">
            {check.authority}
            {/* The register alone doesn't settle a verdict — "no hits" means nothing without
                the date the register reflects, so with a named authority the date is stated
                even when absent ("as of —"). The two fields are independently nullable, so a
                lone date still shows. */}
            <span className="font-mono text-xs tabular-nums text-faint">
              {check.authority ? " · as of " : "As of "}
              {formatDate(check.as_of)}
            </span>
          </p>
        </div>
      )}
      {check.reference && (
        <div>
          <p className="label">Reference</p>
          <p className="mt-1.5 break-all font-mono text-xs text-muted">{check.reference}</p>
        </div>
      )}
      <TraceChip traces_to={check.trace?.traces_to} />
    </Disclosure>
  );
}

/** The legal cross-reference: a cross-check like the claim rows, so it reads the same way —
 * same verdict vocabulary, same pills. An unchecked register says so rather than passing for
 * a clean result. */
export function LegalChecks({ checks }: { checks: LegalCheck[] }) {
  if (checks.length === 0) return null;
  return (
    <section className="space-y-3">
      <p className="text-sm text-muted">
        Permits, sanctions screening, litigation and ownership of record, cross-referenced
        against the register that would settle each one. Open a row for the finding and where
        it came from.
      </p>
      <Card>
        <CardHeader
          title="Legal &amp; regulatory"
          action={
            <span className="text-xs text-muted">
              {checks.length} check{checks.length === 1 ? "" : "s"}
            </span>
          }
        />
        {checks.map((c) => (
          // Content-stable key: a <details> holds its open/closed state in the DOM by key, so
          // an index would carry an expanded row's state onto a different check if the list
          // were ever reordered or filtered.
          <LegalRow key={`${c.check_type}-${c.subject}`} check={c} />
        ))}
      </Card>
    </section>
  );
}
