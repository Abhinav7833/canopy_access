"use client";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { PageHeader } from "@/components/ui/PageHeader";
import { Stat } from "@/components/ui/Stat";
import { Badge } from "@/components/ui/Badge";
import { Table, Thead, Th, Tbody, Td } from "@/components/ui/Table";
import { RiskScore } from "@/components/ui/RiskMeter";
import { MetricLabel } from "@/components/ui/MetricInfo";
import { useProjects } from "@/lib/queries";
import { titleCase } from "@/lib/format";
import { PRIMARY_PROJECT_ID } from "@/lib/config";

export default function Home() {
  const { data, isLoading, isError } = useProjects();
  const router = useRouter();
  const projects = data ?? [];
  const scored = projects.filter((p) => p.risk_score != null);
  const avg = scored.length
    ? Math.round(scored.reduce((s, p) => s + (p.risk_score ?? 0), 0) / scored.length)
    : null;
  const highCount = projects.filter((p) =>
    ["high", "critical"].includes((p.risk_band ?? "").toLowerCase()),
  ).length;
  const totalAvoided = projects.reduce((s, p) => s + (p.avoided_emissions_tco2 ?? 0), 0);

  return (
    <div className="mx-auto max-w-6xl px-6 py-8 space-y-6">
      <PageHeader
        eyebrow="Portfolio"
        title="Monitored assets"
        description="Disclosure-anchored evidence for financed green assets: each claim located, tracked over time, and cross-checked against the satellite record, then resolved to one explained rating."
      />

      <div className="grid grid-cols-2 gap-4 sm:grid-cols-3 lg:grid-cols-5">
        <Stat label="Assets" value={isLoading || isError ? "—" : projects.length} />
        <Stat metric="avgRiskScore" value={isLoading || isError ? "—" : (avg ?? "—")} />
        <Stat
          metric="highCritical"
          value={
            <span className={highCount ? "text-risk-high" : undefined}>
              {isLoading || isError ? "—" : highCount}
            </span>
          }
        />
        <Stat
          metric="avoidedEmissions"
          value={isLoading || isError || !totalAvoided ? "—" : totalAvoided.toLocaleString()}
          sub="tCO2e/yr, modeled"
        />
        <Stat
          label="Evidence"
          value="Independent"
          sub="Satellite + disclosure, every figure cited"
          tone="accent"
        />
      </div>

      {isError ? (
        <div className="rounded-card border border-risk-high-border bg-risk-high-soft px-5 py-4 text-sm text-risk-high">
          Could not reach the API. Confirm the backend is running on <code>:8001</code>.
        </div>
      ) : isLoading ? (
        <TableSkeleton />
      ) : projects.length === 0 ? (
        <div className="rounded-card border border-border bg-surface px-5 py-12 text-center text-sm text-muted shadow-card">
          No monitored assets yet.
        </div>
      ) : (
        <Table>
          <Thead>
            <tr>
              <Th>Asset</Th>
              <Th>Type</Th>
              <Th>Country</Th>
              <Th>Financing</Th>
              <Th align="right">
                <MetricLabel metric="rating" />
              </Th>
              <Th>Status</Th>
            </tr>
          </Thead>
          <Tbody>
            {projects.map((p) => (
              <tr
                key={p.id}
                onClick={() => router.push(`/projects/${p.id}`)}
                className="cursor-pointer border-b border-border transition-colors last:border-0 hover:bg-surface-muted"
              >
                <Td>
                  <span className="flex items-center gap-2">
                    <Link
                      href={`/projects/${p.id}`}
                      onClick={(e) => e.stopPropagation()}
                      className="font-medium text-ink hover:text-accent"
                    >
                      {p.name}
                    </Link>
                    {p.id === PRIMARY_PROJECT_ID && <Badge tone="accent">Primary</Badge>}
                  </span>
                  <span className="mt-0.5 block font-mono text-xs text-faint">{p.id}</span>
                </Td>
                <Td className="text-muted">{titleCase(p.asset_type)}</Td>
                <Td className="text-muted">{p.country ?? "—"}</Td>
                <Td className="text-muted">{titleCase(p.financing_type)}</Td>
                <Td align="right">
                  <RiskScore score={p.risk_score} band={p.risk_band} className="justify-end" />
                </Td>
                <Td className="text-muted">{titleCase(p.status)}</Td>
              </tr>
            ))}
          </Tbody>
        </Table>
      )}
    </div>
  );
}

function TableSkeleton() {
  return (
    <div className="overflow-hidden rounded-card border border-border bg-surface shadow-card">
      <div className="h-10 border-b border-border bg-surface-muted" />
      {Array.from({ length: 3 }).map((_, i) => (
        <div key={i} className="flex items-center gap-4 border-b border-border px-4 py-4 last:border-0">
          <div className="h-4 w-48 animate-pulse rounded bg-surface-muted" />
          <div className="ml-auto h-4 w-24 animate-pulse rounded bg-surface-muted" />
        </div>
      ))}
    </div>
  );
}
