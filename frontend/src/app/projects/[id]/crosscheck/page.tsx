"use client";
import { use } from "react";
import { Badge } from "@/components/ui/Badge";
import { StatusPill } from "@/components/ui/StatusPill";
import { CardSkeleton, EmptyState } from "@/components/ui/Card";
import { Table, Thead, Th, Tbody, Td } from "@/components/ui/Table";
import { DossierUnavailable } from "@/components/features/DossierUnavailable";
import { LegalChecks } from "@/components/features/LegalChecks";
import { claimLabel, formatClaimValue } from "@/lib/dossier";
import { crossCheckTone, titleCase } from "@/lib/format";
import { useDossier, useProject } from "@/lib/queries";

/** Step 4 of the narrative: promised (from the disclosure) vs observed (from the imagery
 * series), one row per claim — the moment the claim either holds up or doesn't. */
export default function CrossCheck({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: dossier, isLoading, isError, error } = useDossier(id);
  const { data: project } = useProject(id);

  if (isError) return <DossierUnavailable error={error} noun="cross-check" />;
  if (isLoading || !dossier) return <CardSkeleton />;

  const claimsById = new Map(dossier.claims.map((c) => [c.id, c]));
  const rows = dossier.cross_check;
  const legal = dossier.legal_checks ?? [];

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted">
        Each disclosed claim, promised versus what the satellite record actually shows: the moment
        a financed claim either holds up or doesn&apos;t. The variance and the evidence behind every
        row are shown.
      </p>

      {rows.length > 0 ? (
        <Table>
          <Thead>
            <tr>
              <Th>Claim</Th>
              <Th align="right">Promised</Th>
              <Th>Observed</Th>
              <Th align="center">Status</Th>
              <Th>Variance</Th>
              <Th>Evidence</Th>
            </tr>
          </Thead>
          <Tbody>
            {rows.map((r) => {
              const claim = claimsById.get(r.claim_id);
              return (
                <tr key={r.claim_id} className="border-b border-border align-top last:border-0">
                  <Td className="font-medium">
                    {claim ? claimLabel(claim.kind, project?.asset_type) : r.claim_id}
                  </Td>
                  <Td align="right" className="font-mono tabular-nums">
                    {claim ? formatClaimValue(claim.kind, claim.promised, claim.unit) : "—"}
                  </Td>
                  <Td className="text-muted">
                    {claim ? formatClaimValue(claim.kind, r.observed, claim.unit) : String(r.observed)}
                  </Td>
                  <Td align="center">
                    <StatusPill tone={crossCheckTone(r.status)}>{titleCase(r.status)}</StatusPill>
                  </Td>
                  <Td className="text-muted">{r.variance}</Td>
                  <Td>
                    <div className="flex flex-wrap gap-1.5">
                      {r.evidence_ids.map((e) => (
                        <Badge key={e} className="font-mono">
                          {e}
                        </Badge>
                      ))}
                    </div>
                  </Td>
                </tr>
              );
            })}
          </Tbody>
        </Table>
      ) : (
        <EmptyState>No cross-check results yet.</EmptyState>
      )}

      <LegalChecks checks={legal} />
    </div>
  );
}
