"use client";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { use } from "react";
import { LlmUnavailable } from "@/components/features/LlmUnavailable";
import { MemoView } from "@/components/features/MemoView";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { ApiError, api, isLlmUnavailable } from "@/lib/api";
import { formatDate, titleCase } from "@/lib/format";
import { reportKey, useLatestReport } from "@/lib/queries";

export default function Memo({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const queryClient = useQueryClient();
  // The generated memo lives in the query cache (persisted across tab switches by the app-level
  // QueryClient), loaded from the last saved memo on mount. The generate mutation writes the
  // fresh one straight into that cache, so navigating away and back never loses it.
  const { data: report, isLoading, isError: loadError } = useLatestReport(id);
  const m = useMutation({
    mutationFn: () => api.createReport(id, {}),
    // Cancel any in-flight load first, so a slow GET can't resolve after the POST and
    // overwrite the freshly generated memo in the cache.
    onMutate: () => queryClient.cancelQueries({ queryKey: reportKey(id) }),
    onSuccess: (created) => queryClient.setQueryData(reportKey(id), created),
  });

  const unavailable = isLlmUnavailable(m.error);
  // Skeleton while either the initial load or a generation is in flight; `isLoading` already
  // implies no cached report, so it needs no extra guard.
  const busy = m.isPending || isLoading;
  // A failed load of an existing memo is distinct from a failed generation: don't let it fall
  // through to the "no memo yet" empty state and nudge a redundant regeneration.
  const showLoadError = loadError && !report;

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted">
        A grounded monitoring memo drawn only from this asset&apos;s stored evidence. Every claim it
        makes cites the evidence behind it.
      </p>
      <Card>
        <CardHeader
          title="Monitoring memo"
          action={
            <button
              onClick={() => m.mutate()}
              disabled={busy}
              className="rounded-md bg-accent px-3 py-2 text-sm font-medium text-accent-ink transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
            >
              {m.isPending ? "Generating…" : report ? "Regenerate memo" : "Generate memo"}
            </button>
          }
        />
        <CardBody>
          <p className="text-xs text-faint">
            Produces a grounded finance memo drawn from this asset&apos;s stored evidence, citing
            every claim made.
          </p>
        </CardBody>
      </Card>

      {busy && (
        <div className="h-64 animate-pulse rounded-card border border-border bg-surface" />
      )}

      {m.isError && unavailable && <LlmUnavailable capability="memo" />}

      {m.isError && !unavailable && (
        <div className="rounded-card border border-risk-high-border bg-risk-high-soft px-5 py-4 text-sm text-risk-high">
          Memo generation failed. {m.error instanceof ApiError ? m.error.message : "Please try again."}
        </div>
      )}

      {!busy && !m.isError && showLoadError && (
        <div className="rounded-card border border-risk-high-border bg-risk-high-soft px-5 py-4 text-sm text-risk-high">
          Could not load this asset&apos;s memo. Retry, or generate a fresh one above.
        </div>
      )}

      {!busy && !m.isError && !showLoadError && !report && (
        <div className="rounded-card border border-border bg-surface px-5 py-12 text-center text-sm text-muted shadow-card">
          Generate a memo to see a cited finance write-up here.
        </div>
      )}

      {report && !m.isPending && (
        <Card>
          <CardHeader
            title="Finance memo"
            action={
              <span className="font-mono text-xs tabular-nums text-muted">
                {report.id} · {titleCase(report.report_type)} · Generated{" "}
                {formatDate(report.generated_at)}
              </span>
            }
          />
          <CardBody className="space-y-5">
            {report.content ? (
              <MemoView content={report.content} />
            ) : (
              <p className="text-sm text-muted">No content returned.</p>
            )}
            <div className="border-t border-border pt-4">
              <p className="label mb-2">Evidence cited</p>
              {(report.evidence_ids ?? []).length > 0 ? (
                <div className="flex flex-wrap gap-1.5">
                  {report.evidence_ids.map((eid) => (
                    <Badge key={eid} className="font-mono">
                      {eid}
                    </Badge>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-faint">No evidence citations recorded.</p>
              )}
            </div>
          </CardBody>
        </Card>
      )}
    </div>
  );
}
