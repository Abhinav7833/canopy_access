# Professional Redesign — Phase B (Signature Components, part 1: Confidence Rating) Plan

> **For agentic workers:** REQUIRED SUB-SKILL: superpowers:subagent-driven-development. Steps use checkbox (`- [ ]`) syntax.

**Goal:** Build the hero trust object — a `ConfidenceRating` gauge badge (the BeZero-style "score as a rating") — and wire it into the persistent `ProjectHeader`, replacing the flat on-track-%/badge/bar cluster, in both themes.

**Architecture:** A tiny pure gauge-geometry helper (`lib/gauge.ts`, unit-tested) drives an SVG arc in a client component (`ConfidenceRating`) that animates on mount (reduced-motion aware), colored by the risk band via the existing `riskTone` + risk tokens. `ProjectHeader` renders it instead of the current inline cluster. Presentation-only; same data.

**Tech Stack:** Next.js 16, Tailwind v4 tokens, TypeScript, Vitest (jsdom), SVG.

## Global Constraints

- **No data/behavior/API change.** Same `useProject`/`useDossier` payloads; the header's graceful-degradation logic (dossier `on_track_pct`/`risk_band`, falling back to project `risk_score`/`risk_band`) is preserved.
- **Light + dark parity, AA-legible.** Colors come only from tokens (`--color-*`); the arc/track/band use the risk ramp + `border-strong`. No hard-coded hex.
- **Honor `prefers-reduced-motion`** — the arc animates on mount; under reduced-motion it renders at its final value with no transition.
- **Self-contained** (no external assets); **keep Geist** (the score uses `font-mono` = Geist Mono, tabular-nums).
- **`riskTone(band)` returns** `"low" | "medium" | "high" | "critical" | "neutral"`. Band→tone→color must reuse it (don't reinvent the mapping). Risk tokens: `--color-risk-low/-med/-high/-critical` (+ `-soft`/`-border`), and `Badge` already maps these tones.
- Leave `RiskBar`/`RiskScore` (used by the portfolio, Locate, and Confidence tabs) untouched — those are Phase C.

**Run** (from `frontend/`): `npx tsc --noEmit` · `npx eslint` · `npx vitest run` · `npx next build`. Dev server on `:3000`, backend `:8001`.

---

### Task 1: Gauge geometry helper + tests

**Files:**
- Create: `frontend/src/lib/gauge.ts`
- Test: `frontend/src/lib/gauge.test.ts`

**Interfaces:**
- Produces: `circumference(radius: number): number`; `arcOffset(pct: number | null, radius: number): number` — the `stroke-dashoffset` that fills a circle of `radius` to `pct`% (0 at 100%, full circumference at 0/null, clamped to [0,100]).

- [ ] **Step 1: Write the failing test** — `frontend/src/lib/gauge.test.ts`

```ts
import { describe, expect, it } from "vitest";
import { arcOffset, circumference } from "@/lib/gauge";

describe("gauge", () => {
  const r = 47;
  const circ = 2 * Math.PI * r;

  it("full circumference for a radius", () => {
    expect(circumference(r)).toBeCloseTo(circ, 6);
  });
  it("no offset at 100%", () => {
    expect(arcOffset(100, r)).toBeCloseTo(0, 6);
  });
  it("full offset at 0% and for null", () => {
    expect(arcOffset(0, r)).toBeCloseTo(circ, 6);
    expect(arcOffset(null, r)).toBeCloseTo(circ, 6);
  });
  it("half offset at 50%", () => {
    expect(arcOffset(50, r)).toBeCloseTo(circ / 2, 6);
  });
  it("clamps out-of-range input", () => {
    expect(arcOffset(150, r)).toBeCloseTo(0, 6);
    expect(arcOffset(-20, r)).toBeCloseTo(circ, 6);
  });
});
```

- [ ] **Step 2: Run it, expect FAIL** — `cd frontend && npx vitest run src/lib/gauge.test.ts` (module not found).

- [ ] **Step 3: Implement** — `frontend/src/lib/gauge.ts`

```ts
/** Circumference of a circle of the given radius. */
export function circumference(radius: number): number {
  return 2 * Math.PI * radius;
}

/** `stroke-dashoffset` to fill a circular gauge of `radius` to `pct`% (0-100).
 * 0 offset = full; full circumference = empty. Null/out-of-range clamp sensibly. */
export function arcOffset(pct: number | null, radius: number): number {
  const clamped = Math.max(0, Math.min(100, pct ?? 0));
  return circumference(radius) * (1 - clamped / 100);
}
```

- [ ] **Step 4: Run tests, expect PASS** — `npx vitest run src/lib/gauge.test.ts` (5 pass). Then `npx tsc --noEmit` exit 0.

- [ ] **Step 5: Commit** — `git add frontend/src/lib/gauge.ts frontend/src/lib/gauge.test.ts && git commit -m "feat(ui): gauge geometry helper for the confidence rating"`

---

### Task 2: `ConfidenceRating` component + `ProjectHeader` integration

**Files:**
- Create: `frontend/src/components/features/ConfidenceRating.tsx`
- Modify: `frontend/src/components/features/ProjectHeader.tsx`

**Interfaces:**
- Consumes: `circumference`, `arcOffset` (Task 1); `riskTone` from `@/lib/format`; `Badge` from `@/components/ui/Badge`.
- Produces: `<ConfidenceRating pct={number|null} band={string|null} size?={number} />` — an SVG gauge (track + band-colored arc animating to `pct` on mount, reduced-motion aware), the score in Geist Mono with an "On track" micro-label, and the band `Badge`.

- [ ] **Step 1: Create `ConfidenceRating.tsx`**

```tsx
"use client";
import { useEffect, useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { arcOffset, circumference } from "@/lib/gauge";
import { riskTone } from "@/lib/format";

const STROKE: Record<string, string> = {
  low: "var(--color-risk-low)",
  medium: "var(--color-risk-med)",
  high: "var(--color-risk-high)",
  critical: "var(--color-risk-critical)",
  neutral: "var(--color-faint)",
};

/** The dossier's on-track confidence, presented as a rating: a band-colored SVG gauge
 * with the score and risk band. The one number the committee acts on. */
export function ConfidenceRating({
  pct,
  band,
  size = 116,
}: {
  pct: number | null;
  band: string | null;
  size?: number;
}) {
  const stroke = 9;
  const r = size / 2 - stroke;
  const circ = circumference(r);
  const target = arcOffset(pct, r);
  const tone = riskTone(band);

  const reduce =
    typeof window !== "undefined" &&
    window.matchMedia("(prefers-reduced-motion: reduce)").matches;
  const [offset, setOffset] = useState(reduce ? target : circ);
  useEffect(() => {
    if (reduce) {
      setOffset(target);
      return;
    }
    const raf = requestAnimationFrame(() => requestAnimationFrame(() => setOffset(target)));
    return () => cancelAnimationFrame(raf);
  }, [target, reduce]);

  const c = size / 2;
  return (
    <div className="flex items-center gap-4">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          viewBox={`0 0 ${size} ${size}`}
          className="-rotate-90"
          role="img"
          aria-label={`On-track confidence ${pct ?? "unknown"} percent${band ? `, ${band} risk` : ""}`}
        >
          <circle cx={c} cy={c} r={r} fill="none" stroke="var(--color-border-strong)" strokeWidth={stroke} />
          <circle
            cx={c}
            cy={c}
            r={r}
            fill="none"
            stroke={STROKE[tone] ?? STROKE.neutral}
            strokeWidth={stroke}
            strokeLinecap="round"
            strokeDasharray={circ}
            strokeDashoffset={offset}
            style={reduce ? undefined : { transition: "stroke-dashoffset 1s cubic-bezier(.2,.7,.2,1)" }}
          />
        </svg>
        <div className="absolute inset-0 grid place-content-center text-center">
          <div className="font-mono text-3xl font-semibold leading-none tabular-nums text-ink">
            {pct ?? "—"}
            <span className="align-top text-sm font-normal text-muted">%</span>
          </div>
          <div className="label mt-1.5">On track</div>
        </div>
      </div>
      {band && (
        <div className="flex flex-col items-start gap-1.5">
          <span className="label">Risk band</span>
          <Badge tone={tone}>{band}</Badge>
        </div>
      )}
    </div>
  );
}
```

- [ ] **Step 2: Wire it into `ProjectHeader.tsx`**

Replace the `RiskBar` import and the `band && (...)` cluster with `ConfidenceRating`. New file:

```tsx
"use client";
import { ConfidenceRating } from "@/components/features/ConfidenceRating";
import { useDossier, useProject } from "@/lib/queries";
import { titleCase } from "@/lib/format";

/** Persistent per-project header. The headline is the dossier's on-track confidence,
 * shown as a rating gauge alongside the risk band (see
 * docs/specs/2026-07-13-canopy-disclosure-direction.md). Falls back to the project's own
 * risk_score/band if the dossier isn't available so the header degrades gracefully. */
export function ProjectHeader({ id }: { id: string }) {
  const { data: p, isError } = useProject(id);
  const { data: dossier } = useDossier(id);
  if (isError) return null;
  if (!p) {
    return <div className="h-10 w-72 animate-pulse rounded bg-surface-muted" />;
  }
  const meta = [titleCase(p.asset_type), p.country, titleCase(p.financing_type)].filter(
    (x): x is string => Boolean(x) && x !== "—",
  );
  const onTrackPct = dossier?.confidence?.on_track_pct ?? null;
  const band = dossier?.confidence?.risk_band ?? p.risk_band;
  return (
    <div className="flex flex-wrap items-start justify-between gap-4">
      <div className="min-w-0">
        <h1 className="text-2xl font-semibold tracking-tight text-ink">{p.name}</h1>
        <p className="mt-1 text-sm text-muted">{meta.join("  ·  ")}</p>
      </div>
      {band && <ConfidenceRating pct={onTrackPct} band={band} />}
    </div>
  );
}
```

(This drops the now-unused `Badge`, `RiskBar`, `riskTone`, `formatPercent` imports from `ProjectHeader` — remove them, keep only what the new file uses. The `barScore`/`tone` locals are gone.)

- [ ] **Step 3: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass (vitest now 17: the 16 prior + gauge; gauge test file adds 5 → but total = existing 16 + 5 = 21 tests across 7 files — confirm the numbers move up, nothing fails). No unused-import lint errors in `ProjectHeader`.

- [ ] **Step 4: Commit**

`git add frontend/src/components/features/ConfidenceRating.tsx frontend/src/components/features/ProjectHeader.tsx && git commit -m "feat(ui): confidence rating gauge as the project header hero"`

---

### Task 3: Verify both themes + both assets in the browser

- [ ] **Step 1:** Gates green (Task 2 Step 3 already ran them; re-confirm nothing regressed).
- [ ] **Step 2:** With dev (`:3000`) + backend (`:8001`) up, drive: `/projects/nur_navoi_solar` (85% / Low) and `/projects/mikoko_pamoja` (90% / Low). For each, screenshot **light** then toggle **dark**. Confirm: the gauge arc fills to the % and is band-colored (green for Low), the score is legible in Geist Mono, the band Badge renders, the layout doesn't break, both themes look right, zero console errors, and the arc respects `prefers-reduced-motion` (animation only when motion is allowed).
- [ ] **Step 3:** Fix any straggler (e.g. contrast, layout), re-verify. Note the outcome.

---

## Self-Review

**Spec coverage:** the ConfidenceRating gauge (hero trust object) is built (Task 2), driven by a tested pure helper (Task 1), band-colored via the existing `riskTone`/risk tokens (both themes), reduced-motion aware, and integrated into its most prominent home (Task 2 Step 2), verified in both themes/assets (Task 3). The remaining Phase-B signature components (`AoiEvidenceLayer` canvas, evidence-pipeline strip) and the portfolio/Confidence-tab rollout are **deferred to the next plan** — this plan is scoped to the single highest-impact rating component.

**Placeholder scan:** clean — complete code in every step.

**Type consistency:** `arcOffset`/`circumference` signatures match between Task 1 (definition + test) and Task 2 (consumption). `riskTone` return values (`low|medium|high|critical|neutral`) match the `STROKE` map keys and `Badge` tones. `ConfidenceRating` props (`pct`, `band`, `size?`) match the `ProjectHeader` call site.
