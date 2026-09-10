import { Badge } from "@/components/ui/Badge";
import { Card, CardBody } from "@/components/ui/Card";
import type { Evidence } from "@/lib/types";
import { confidenceTone, formatDate, titleCase } from "@/lib/format";

export function EvidenceCard({ evidence }: { evidence: Evidence }) {
  const tone = evidence.confidence ? confidenceTone(evidence.confidence) : undefined;
  return (
    <Card>
      <CardBody className="space-y-3">
        <div className="flex items-center justify-between gap-2">
          <span className="font-mono text-xs text-faint">{evidence.id}</span>
          {evidence.confidence && <Badge tone={tone}>{titleCase(evidence.confidence)} confidence</Badge>}
        </div>
        <div>
          <p className="text-sm font-medium text-ink">{evidence.source_name}</p>
          {/* Undated reference material carries neither a capture date nor a method, so the
              line is dropped rather than rendered as a bare no-data placeholder. */}
          {(evidence.source_date || evidence.method_id) && (
            <p className="mt-0.5 text-xs text-muted">
              {[
                evidence.source_date && formatDate(evidence.source_date),
                evidence.method_id && titleCase(evidence.method_id),
              ]
                .filter(Boolean)
                .join(" · ")}
            </p>
          )}
        </div>
        {evidence.financial_relevance && (
          <p className="text-sm leading-relaxed text-muted">{evidence.financial_relevance}</p>
        )}
        {evidence.limitations.length > 0 && (
          <div>
            <p className="label mb-1.5">Limitations</p>
            <ul className="space-y-1 text-xs text-muted">
              {evidence.limitations.map((l, i) => (
                <li key={i} className="flex gap-1.5">
                  <span className="text-faint">—</span>
                  <span>{l}</span>
                </li>
              ))}
            </ul>
          </div>
        )}
        {evidence.supporting_assets.length > 0 && (
          <div className="flex flex-wrap gap-1.5">
            {evidence.supporting_assets.map((a) => (
              <span
                key={a}
                className="rounded-md border border-border bg-surface-muted px-1.5 py-0.5 font-mono text-[11px] text-muted"
              >
                {a}
              </span>
            ))}
          </div>
        )}
      </CardBody>
    </Card>
  );
}
