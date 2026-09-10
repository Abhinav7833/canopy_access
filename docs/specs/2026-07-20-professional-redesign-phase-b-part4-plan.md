# Professional Redesign — Phase B (Signature Components, part 4: StatusPill) Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a `StatusPill` primitive — a semantic colored **dot + label** — and use it for the cross-check status column, distinguishing *status* (dot-led pill) from *risk band* (filled `Badge`), in both themes.

**Architecture:** A tiny presentational component (`components/ui/StatusPill.tsx`) colors a small dot from the shared risk tokens via the existing `RiskTone` vocabulary; the text label carries the meaning (the dot is `aria-hidden`). It replaces the `Badge` in the cross-check page's status column only. Unit-tested for the tone→dot-color contract. Presentation-only; same data.

**Tech Stack:** Next.js 16, Tailwind v4 tokens, TypeScript, Vitest (jsdom) + @testing-library/react + jest-dom.

## Global Constraints

- **No data/behavior/API/schema change.** Same `useDossier`/`useProject` payloads. Pure presentation.
- **Reuse the shared tone vocabulary.** `StatusPill` takes `tone?: RiskTone | "accent"` (`RiskTone` = `"low" | "medium" | "high" | "critical" | "neutral"`, from `@/lib/format`). The cross-check call site keeps `crossCheckTone(r.status)` (met/on_track → `low`, behind/variance → `medium`, else `neutral`) — do not reinvent the mapping.
- **Dot colors from tokens only** (so they flip light/dark): `bg-risk-low`/`-med`/`-high`/`-critical` (solid, not the `-soft` Badge variants), `bg-faint` (neutral), `bg-accent`. All verified present in `globals.css` (`--color-risk-*`, `--color-faint`, `--color-accent`).
- **Accessibility:** the dot is decorative (`aria-hidden`); the visible text label is the accessible name. Label text is `text-ink` (meets AA). No color-only meaning.
- **Do not restyle `Badge`, `Stat`, `Table`, or `TraceChip`** — those are already tokenized and out of scope for this part (the design doc's other "refined primitives" were assessed as already-done / YAGNI). Only add `StatusPill` and wire the one call site.
- **`Badge` stays imported in the cross-check page** — the evidence-id chips still use it. Only the status column swaps to `StatusPill`.
- **Commit hygiene (Canopy pre-commit gate):** code commits (`.tsx`) are blocked by `.claude/hooks/pre-commit-review.sh` until the staged snapshot is reviewed. Under subagent-driven execution the controller keeps all git: the SDD task-review is the review of record, then `git write-tree > .git/canopy-review-marker` (its own executed step) and `git commit` (separate step). The docs-only commit in Task 0 passes freely.

**Run** (from `frontend/`): `npx tsc --noEmit` · `npx eslint` · `npx vitest run` · `npx next build`. Dev server on `:3000`, backend `:8001`. Current baseline: **8 test files, 30 tests**; this part adds `StatusPill.test.tsx` (3 tests) → **9 files, 33 tests**.

---

### Task 0: Commit this plan (docs-only)

**Files:**
- Create: `docs/specs/2026-07-20-professional-redesign-phase-b-part4-plan.md` (this file)

- [ ] **Step 1: Commit** (docs-only, passes the gate freely)

```bash
git add docs/specs/2026-07-20-professional-redesign-phase-b-part4-plan.md
git commit -m "docs: Phase B plan (part 4) — StatusPill primitive"
```

---

### Task 1: `StatusPill` component + test + cross-check wiring

**Files:**
- Create: `frontend/src/components/ui/StatusPill.tsx`
- Test: `frontend/src/components/ui/StatusPill.test.tsx`
- Modify: `frontend/src/app/projects/[id]/crosscheck/page.tsx`

**Interfaces:**
- Consumes: `RiskTone` from `@/lib/format`; `crossCheckTone`, `titleCase` from `@/lib/format` (at the call site, already imported there).
- Produces: `<StatusPill tone?={RiskTone | "accent"}>{label}</StatusPill>` — an inline dot + label span.

- [ ] **Step 1: Write the failing test** — `frontend/src/components/ui/StatusPill.test.tsx`

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { StatusPill } from "@/components/ui/StatusPill";

describe("StatusPill", () => {
  it("renders its label", () => {
    render(<StatusPill tone="low">On track</StatusPill>);
    expect(screen.getByText("On track")).toBeInTheDocument();
  });

  it("colors the dot by tone", () => {
    const { container } = render(<StatusPill tone="medium">Behind</StatusPill>);
    const dot = container.querySelector("[aria-hidden]");
    expect(dot).not.toBeNull();
    expect(dot?.className).toContain("bg-risk-med");
  });

  it("defaults to a neutral dot", () => {
    const { container } = render(<StatusPill>Unknown</StatusPill>);
    const dot = container.querySelector("[aria-hidden]");
    expect(dot?.className).toContain("bg-faint");
  });
});
```

- [ ] **Step 2: Run it, expect FAIL** — `cd frontend && npx vitest run src/components/ui/StatusPill.test.tsx` (module not found).

- [ ] **Step 3: Implement** — `frontend/src/components/ui/StatusPill.tsx`

```tsx
import type { ReactNode } from "react";
import type { RiskTone } from "@/lib/format";

const DOT: Record<string, string> = {
  neutral: "bg-faint",
  low: "bg-risk-low",
  medium: "bg-risk-med",
  high: "bg-risk-high",
  critical: "bg-risk-critical",
  accent: "bg-accent",
};

/** A status as a semantic dot + label — the quiet counterpart to the filled `Badge` (which we
 * reserve for risk bands). The dot carries the color; the text carries the meaning, so the dot
 * is aria-hidden. Used for cross-check outcomes (met / on-track / behind / variance). */
export function StatusPill({
  tone = "neutral",
  children,
  className = "",
}: {
  tone?: RiskTone | "accent";
  children: ReactNode;
  className?: string;
}) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 whitespace-nowrap text-xs font-medium text-ink ${className}`}
    >
      <span
        aria-hidden
        className={`h-1.5 w-1.5 shrink-0 rounded-full ${DOT[tone] ?? DOT.neutral}`}
      />
      {children}
    </span>
  );
}
```

- [ ] **Step 4: Run tests, expect PASS** — `npx vitest run src/components/ui/StatusPill.test.tsx` (3 pass). Then `npx tsc --noEmit` exit 0.

- [ ] **Step 5: Wire into the cross-check status column** — `frontend/src/app/projects/[id]/crosscheck/page.tsx`

Add the import (keep all existing imports — `Badge` stays, the evidence chips use it):
```tsx
import { StatusPill } from "@/components/ui/StatusPill";
```

Find the status cell:
```tsx
                  <Td align="center">
                    <Badge tone={crossCheckTone(r.status)}>{titleCase(r.status)}</Badge>
                  </Td>
```
Replace the `Badge` with `StatusPill` (same tone + label):
```tsx
                  <Td align="center">
                    <StatusPill tone={crossCheckTone(r.status)}>{titleCase(r.status)}</StatusPill>
                  </Td>
```
Leave the rest of the file unchanged — in particular the evidence-id `<Badge key={e} className="font-mono">{e}</Badge>` cell keeps using `Badge`, so the `Badge` import stays. `crossCheckTone` and `titleCase` remain used.

- [ ] **Step 6: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass. Vitest is now **9 files / 33 tests** (30 prior + 3 StatusPill). No unused-import lint errors in `crosscheck/page.tsx` (`Badge`, `crossCheckTone`, `titleCase`, `StatusPill` all used).

- [ ] **Step 7: Report** (controller handles git — do not commit)

Report DONE with the TDD evidence (RED then GREEN for the StatusPill test) and the gate output. The controller stages, runs the SDD review, records the marker, and commits:
```
feat(ui): StatusPill (semantic dot) for cross-check status
```

---

### Task 2: Verify the cross-check status column + both themes in the browser

- [ ] **Step 1:** Gates green (Task 1 Step 6 already ran them; re-confirm nothing regressed).
- [ ] **Step 2:** With dev (`:3000`) + backend (`:8001`) up, drive `/projects/nur_navoi_solar/crosscheck` and `/projects/mikoko_pamoja/crosscheck`. Confirm the **Status** column now renders each status as a **dot + label** (a small colored dot before "Met" / "On Track" / "Behind" / "Variance"), where Met/On-track dots are the green (low) tone and Behind/Variance dots are the amber (medium) tone. Confirm the **Evidence** column chips still render as filled `Badge`s (unchanged), the rest of the table is intact, and the layout doesn't break. Screenshot **light**, then toggle **dark**; confirm the dot colors flip correctly with the theme and the labels stay legible, with **zero console errors**.
- [ ] **Step 3:** Fix any straggler (contrast, alignment), re-verify. Note the outcome.

---

## Self-Review

**Spec coverage:** `StatusPill` (semantic dot + label) is built and unit-tested (Task 1 Steps 1–4), and wired into its one home — the cross-check status column (Task 1 Step 5) — verified in both themes (Task 2). The dot/label split (dot = color via risk tokens, aria-hidden; text = meaning) satisfies the a11y + token constraints. `Badge`/`Stat`/`Table`/`TraceChip` are deliberately untouched (stated in Global Constraints — assessed already-refined). The evidence-id `Badge` usage is preserved, so the `Badge` import legitimately stays.

**Placeholder scan:** clean — complete code in every step.

**Type consistency:** `StatusPill`'s `tone?: RiskTone | "accent"` matches the `DOT` map keys (`neutral | low | medium | high | critical | accent`) and the `crossCheckTone` return type (`RiskTone`) at the call site. `crossCheckTone(r.status)` → `RiskTone`, assignable to `StatusPill`'s `tone`. The test's expected classes (`bg-risk-med`, `bg-faint`) match the `DOT` map values for `medium` / default-`neutral`.
