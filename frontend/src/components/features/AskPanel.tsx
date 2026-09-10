"use client";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Card, CardBody, CardHeader } from "@/components/ui/Card";
import { LlmUnavailable } from "@/components/features/LlmUnavailable";
import { ApiError, api, isLlmUnavailable } from "@/lib/api";
import { confidenceTone, titleCase } from "@/lib/format";

export function AskPanel({ id }: { id: string }) {
  const [q, setQ] = useState("");
  const m = useMutation({ mutationFn: (question: string) => api.ask(id, { question }) });

  const unavailable = isLlmUnavailable(m.error);

  return (
    <div className="space-y-6">
      <p className="text-sm text-muted">
        Interrogate this asset&apos;s evidence directly: a bounded Q&amp;A that cites the evidence it
        uses and refuses claims the evidence doesn&apos;t support.
      </p>
      <Card>
        <CardHeader title="Ask a question" />
        <CardBody>
          <form
            onSubmit={(e) => {
              e.preventDefault();
              if (q.trim()) m.mutate(q);
            }}
            className="flex gap-2"
          >
            <input
              value={q}
              onChange={(e) => setQ(e.target.value)}
              placeholder="Ask about this asset's evidence…"
              className="flex-1 rounded-md border border-border bg-surface px-3 py-2 text-sm text-ink placeholder:text-faint focus:border-accent focus:outline-none"
            />
            <button
              type="submit"
              disabled={m.isPending || !q.trim()}
              className="rounded-md bg-accent px-4 py-2 text-sm font-medium text-accent-ink transition-colors hover:bg-accent-hover disabled:cursor-not-allowed disabled:opacity-50"
            >
              {m.isPending ? "Asking…" : "Ask"}
            </button>
          </form>
          <p className="mt-2 text-xs text-faint">
            Answers are bounded to this asset&apos;s stored evidence and cite the evidence used.
          </p>
        </CardBody>
      </Card>

      {m.isPending && (
        <div className="h-32 animate-pulse rounded-card border border-border bg-surface" />
      )}

      {m.isError && unavailable && <LlmUnavailable capability="answer" />}

      {m.isError && !unavailable && (
        <div className="rounded-card border border-risk-high-border bg-risk-high-soft px-5 py-4 text-sm text-risk-high">
          Ask failed. {m.error instanceof ApiError ? m.error.message : "Please try again."}
        </div>
      )}

      {!m.isPending && !m.isError && !m.data && (
        <div className="rounded-card border border-border bg-surface px-5 py-12 text-center text-sm text-muted shadow-card">
          Ask a question to see a cited answer here.
        </div>
      )}

      {m.data && (
        <Card>
          <CardHeader
            title="Answer"
            action={<Badge tone={confidenceTone(m.data.confidence)}>{titleCase(m.data.confidence)} confidence</Badge>}
          />
          <CardBody className="space-y-4">
            <p className="whitespace-pre-wrap text-[15px] leading-relaxed text-ink">
              {m.data.answer}
            </p>

            {m.data.evidence_used.length > 0 && (
              <div>
                <p className="label mb-2">Evidence cited</p>
                <div className="flex flex-wrap gap-1.5">
                  {m.data.evidence_used.map((e) => (
                    <Badge key={e} className="font-mono">
                      {e}
                    </Badge>
                  ))}
                </div>
              </div>
            )}

            {m.data.limitations.length > 0 && (
              <div className="border-t border-border pt-3">
                <p className="label mb-2">Limitations</p>
                <ul className="space-y-1 text-sm text-muted">
                  {m.data.limitations.map((l, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-faint">•</span>
                      <span>{l}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}

            {m.data.unsupported_claims_refused.length > 0 && (
              <div className="border-t border-border pt-3">
                <p className="label mb-2">Unsupported claims refused</p>
                <ul className="space-y-1 text-sm text-risk-med">
                  {m.data.unsupported_claims_refused.map((c, i) => (
                    <li key={i} className="flex gap-2">
                      <span className="text-risk-med">•</span>
                      <span>{c}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardBody>
        </Card>
      )}
    </div>
  );
}
