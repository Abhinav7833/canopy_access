"use client";
import { use } from "react";
import { Card, CardBody, CardHeader, CardSkeleton, EmptyState } from "@/components/ui/Card";
import { PageHeader } from "@/components/ui/PageHeader";
import { Table, Thead, Th, Tbody, Td } from "@/components/ui/Table";
import { TraceChip } from "@/components/features/TraceChip";
import { DossierUnavailable } from "@/components/features/DossierUnavailable";
import { claimLabel, formatClaimValue } from "@/lib/dossier";
import { formatDate } from "@/lib/format";
import { useDossier, useProject } from "@/lib/queries";

/** Step 1 of the narrative: the disclosure document + the claims extracted from it.
 * "Every number starts here" — nothing downstream (locate, observe, cross-check,
 * confidence) exists without a claim traceable back to this screen. */
export default function Disclosure({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: dossier, isLoading, isError, error } = useDossier(id);
  const { data: project } = useProject(id);

  if (isError) return <DossierUnavailable error={error} noun="disclosure" />;
  if (isLoading || !dossier) return <CardSkeleton />;

  const { disclosure, claims } = dossier;

  return (
    <div className="space-y-6">
      <PageHeader
        eyebrow="Disclosure"
        title={disclosure.title}
        description="The financed claims, exactly as disclosed: the baseline every downstream figure is checked against. Nothing here is verified yet; that starts at Locate."
      />

      <Card>
        <CardHeader title="Source document" action={<TraceChip traces_to={disclosure.trace?.traces_to} />} />
        <CardBody className="space-y-4">
          <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <div>
              <p className="label mb-1">Issuer</p>
              <p className="text-sm text-ink">{disclosure.issuer}</p>
            </div>
            <div>
              <p className="label mb-1">Instrument</p>
              <p className="text-sm text-ink">{disclosure.instrument}</p>
            </div>
            <div>
              <p className="label mb-1">Financing date</p>
              <p className="text-sm text-ink">{formatDate(disclosure.financing_date)}</p>
            </div>
            <div>
              <p className="label mb-1">Region hint</p>
              <p className="text-sm text-ink">{disclosure.region_hint}</p>
            </div>
          </div>
          <p className="border-t border-border pt-4 text-[15px] leading-relaxed text-ink">
            {disclosure.summary}
          </p>
          <p className="font-mono text-xs text-faint">{disclosure.doc_ref}</p>
        </CardBody>
      </Card>

      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-sm font-semibold text-ink">Claims extracted</h2>
          <p className="mt-0.5 text-xs text-muted">Each is the promise a downstream screen must corroborate.</p>
        </div>
        <span className="text-xs text-muted">{claims.length} from this document</span>
      </div>

      {claims.length > 0 ? (
        <Table>
          <Thead>
            <tr>
              <Th>Claim</Th>
              <Th align="right">Promised</Th>
              <Th>Unit</Th>
              <Th>Source</Th>
            </tr>
          </Thead>
          <Tbody>
            {claims.map((c) => (
              <tr key={c.id} className="border-b border-border align-top last:border-0">
                <Td className="font-medium">{claimLabel(c.kind, project?.asset_type)}</Td>
                <Td align="right" className="font-mono tabular-nums">
                  {formatClaimValue(c.kind, c.promised, c.unit)}
                </Td>
                <Td className="text-muted">{c.unit}</Td>
                <Td>
                  <p className="max-w-md text-xs leading-relaxed text-muted">
                    {c.source_span}
                  </p>
                </Td>
              </tr>
            ))}
          </Tbody>
        </Table>
      ) : (
        <EmptyState>No claims extracted for this asset.</EmptyState>
      )}
    </div>
  );
}
