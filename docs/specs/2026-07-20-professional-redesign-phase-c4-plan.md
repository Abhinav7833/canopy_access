# Professional Redesign — Phase C4 (Product-Screen Overhaul: Ask + Memo) Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the LLM-output pair — add finance-legible lead-ins to Ask and Memo, and reframe their duplicated "LLM not configured" state from an amber alarm into a calm, honest, shared `LlmUnavailable` component (optional capability, not an error). Both themes, presentation-only.

**Architecture:** A small shared component `LlmUnavailable` (sibling to `DossierUnavailable`) renders the neutral state and replaces the two near-identical amber boxes duplicated in `AskPanel` and the Memo page (a known duplication). Each page gains a lead-in line. No data/API change; the answer card, `MemoView`, generate/ask flows, and the genuine-failure (red) + empty states are untouched.

**Tech Stack:** Next.js 16, Tailwind v4 tokens, TypeScript, Vitest + @testing-library/react + jest-dom.

## Global Constraints

- **No data/behavior/API/schema change.** Same `api.ask`/`api.createReport` mutations, same `isLlmUnavailable(m.error)` detection. Presentation + copy only.
- **The "LLM not configured" state is NOT an error — reframe it as calm/informational.** Neutral tokens only (`border-border`, `bg-surface-muted`, `text-ink`/`text-muted`); do NOT use `risk-med`/amber for this state. The genuine-failure path (`m.isError && !unavailable`) KEEPS its red (`risk-high`) styling — only the `unavailable` box changes.
- **DRY:** one shared `LlmUnavailable` component used by both Ask and Memo (removes the duplicated markup). Do not leave a second inline copy.
- **Honest copy only** — the reframed state says only what's true: the capability is optional/unconfigured in this environment, the evidence it draws on is already in place, only the model wiring is absent. Lead-ins describe what each screen does; no fabricated claims.
- **Leave untouched:** the Ask answer card (confidence `Badge`, Evidence cited, Limitations, Unsupported-claims-refused), `MemoView`, the generate/ask forms + buttons, the loading skeletons, the empty states, and the red genuine-failure boxes.
- **Light + dark parity**; reuse primitives + tokens; no motion added.
- **Commit hygiene (Canopy pre-commit gate):** code commits (`.tsx`) are blocked until the staged snapshot is reviewed. Under subagent-driven execution the controller keeps all git: the SDD task-review is the review of record, then `git write-tree > .git/canopy-review-marker` (its own executed step) and `git commit` (separate step). The docs-only Task 0 passes freely.

**Run** (from `frontend/`): `npx tsc --noEmit` · `npx eslint` · `npx vitest run` · `npx next build`. Dev `:3000`, backend `:8001`. Baseline: **9 files, 34 tests**; this part adds `LlmUnavailable.test.tsx` (3 tests) → **10 files, 37 tests**.

---

### Task 0: Commit this plan (docs-only)

**Files:**
- Create: `docs/specs/2026-07-20-professional-redesign-phase-c4-plan.md` (this file)

- [ ] **Step 1: Commit**

```bash
git add docs/specs/2026-07-20-professional-redesign-phase-c4-plan.md
git commit -m "docs: Phase C4 plan — ask + memo overhaul"
```

---

### Task 1: `LlmUnavailable` component + test

**Files:**
- Create: `frontend/src/components/features/LlmUnavailable.tsx`
- Test: `frontend/src/components/features/LlmUnavailable.test.tsx`

**Interfaces:**
- Produces: `<LlmUnavailable capability={string} message?={string} />` — a neutral informational box; heading `"{capability} needs a language model"`; body = `message` or a generic honest default.

- [ ] **Step 1: Write the failing test** — `frontend/src/components/features/LlmUnavailable.test.tsx`

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { LlmUnavailable } from "@/components/features/LlmUnavailable";

describe("LlmUnavailable", () => {
  it("renders the capability in the heading", () => {
    render(<LlmUnavailable capability="Q&A" />);
    expect(screen.getByText("Q&A needs a language model")).toBeInTheDocument();
  });

  it("shows a provided message", () => {
    render(<LlmUnavailable capability="Memo generation" message="Custom backend detail." />);
    expect(screen.getByText("Custom backend detail.")).toBeInTheDocument();
  });

  it("falls back to a default message when none is given", () => {
    render(<LlmUnavailable capability="Q&A" />);
    expect(screen.getByText(/optional and isn't wired up/i)).toBeInTheDocument();
  });
});
```

- [ ] **Step 2: Run it, expect FAIL** — `cd frontend && npx vitest run src/components/features/LlmUnavailable.test.tsx` (module not found).

- [ ] **Step 3: Implement** — `frontend/src/components/features/LlmUnavailable.tsx`

```tsx
/** Calm, informational state for an optional LLM-backed capability (Ask / Memo) that isn't
 * configured in the current environment. Deliberately NOT an error/alarm treatment — the
 * evidence the capability draws on is already in place; only the model wiring is absent. */
export function LlmUnavailable({
  capability,
  message,
}: {
  capability: string;
  message?: string;
}) {
  return (
    <div className="rounded-card border border-border bg-surface-muted px-5 py-4">
      <p className="text-sm font-semibold text-ink">{capability} needs a language model</p>
      <p className="mt-1 text-sm text-muted">
        {message ||
          "This capability is optional and isn't wired up on the backend in this environment — the evidence it draws on is already in place; only the model is missing."}
      </p>
    </div>
  );
}
```

- [ ] **Step 4: Run tests, expect PASS** — `npx vitest run src/components/features/LlmUnavailable.test.tsx` (3 pass). Then `npx tsc --noEmit` exit 0.

- [ ] **Step 5: Report** (controller handles git). Suggested commit message:
```
feat(ui): LlmUnavailable — calm shared state for optional LLM capabilities
```

---

### Task 2: Ask — lead-in + reframed unavailable state

**Files:**
- Modify: `frontend/src/components/features/AskPanel.tsx`

**Context:** Add a lead-in above the "Ask a question" card, and replace the inline amber `unavailable` box with `<LlmUnavailable capability="Q&A" …/>`. The answer card, the form, the red failure box, and the empty state are unchanged.

- [ ] **Step 1: Add the import**

Add (keep existing imports):
```tsx
import { LlmUnavailable } from "@/components/features/LlmUnavailable";
```

- [ ] **Step 2: Add the lead-in line**

Immediately after the opening `<div className="space-y-6">`, before the `<Card>` with "Ask a question", insert:

```tsx
      <p className="text-sm text-muted">
        Interrogate this asset&apos;s evidence directly — a bounded Q&amp;A that cites the evidence
        it uses and refuses claims the evidence doesn&apos;t support.
      </p>
```

- [ ] **Step 3: Replace the amber unavailable box**

Replace:
```tsx
      {m.isError && unavailable && (
        <div className="rounded-card border border-risk-med-border bg-risk-med-soft px-5 py-4">
          <p className="text-sm font-semibold text-risk-med">Ask Canopy is unavailable</p>
          <p className="mt-1 text-sm text-risk-med">
            {(m.error as ApiError).message ||
              "The language model isn't configured on the backend yet. Add LLM credentials to enable Q&A."}
          </p>
        </div>
      )}
```
with:
```tsx
      {m.isError && unavailable && (
        <LlmUnavailable capability="Q&A" message={(m.error as ApiError).message || undefined} />
      )}
```

(`ApiError` is still used here and in the red failure box, so its import stays.)

- [ ] **Step 4: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass; vitest **10 files / 37 tests**. No unused imports (`ApiError`/`api`/`isLlmUnavailable`/`Badge`/`confidenceTone`/`titleCase`/`Card*` all still used; `LlmUnavailable` now used).

- [ ] **Step 5: Report** (controller handles git). Suggested commit message:
```
feat(ui): Ask — IC lead-in + calm LLM-unavailable state
```

---

### Task 3: Memo — lead-in + reframed unavailable state

**Files:**
- Modify: `frontend/src/app/projects/[id]/memo/page.tsx`

**Context:** Add a lead-in above the "Monitoring memo" card, and replace the inline amber `unavailable` box with `<LlmUnavailable capability="Memo generation" …/>`. The generate button, the in-card helper, `MemoView`, the red failure box, and the empty/pending states are unchanged.

- [ ] **Step 1: Add the import**

Add (keep existing imports):
```tsx
import { LlmUnavailable } from "@/components/features/LlmUnavailable";
```

- [ ] **Step 2: Add the lead-in line**

Immediately after the opening `<div className="space-y-6">`, before the `<Card>` with "Monitoring memo", insert:

```tsx
      <p className="text-sm text-muted">
        A grounded monitoring memo drawn only from this asset&apos;s stored evidence — every claim
        it makes cites the evidence behind it.
      </p>
```

- [ ] **Step 3: Replace the amber unavailable box**

Replace:
```tsx
      {m.isError && unavailable && (
        <div className="rounded-card border border-risk-med-border bg-risk-med-soft px-5 py-4">
          <p className="text-sm font-semibold text-risk-med">Memo generation is unavailable</p>
          <p className="mt-1 text-sm text-risk-med">
            {(m.error as ApiError).message ||
              "The language model isn't configured on the backend yet. Add LLM credentials to enable memo generation."}
          </p>
        </div>
      )}
```
with:
```tsx
      {m.isError && unavailable && (
        <LlmUnavailable
          capability="Memo generation"
          message={(m.error as ApiError).message || undefined}
        />
      )}
```

(`ApiError` is still used here and in the red failure box, so its import stays.)

- [ ] **Step 4: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass; vitest unchanged at **10 files / 37 tests**. No unused imports (`ApiError`/`api`/`isLlmUnavailable`/`Badge`/`formatDate`/`titleCase`/`Card*`/`MemoView` all still used; `LlmUnavailable` now used).

- [ ] **Step 5: Report** (controller handles git). Suggested commit message:
```
feat(ui): Memo — IC lead-in + calm LLM-unavailable state
```

---

### Task 4: Verify both screens + both themes in the browser

- [ ] **Step 1:** Gates green (re-confirm).
- [ ] **Step 2:** With dev (`:3000`) + backend (`:8001`) up, drive `/projects/nur_navoi_solar/ask` and `/projects/nur_navoi_solar/memo`:
  - **Ask:** confirm the new lead-in renders above the "Ask a question" card; the form + in-card helper are intact. Submit a question. If the backend LLM is **not** configured, confirm the response is the **calm neutral `LlmUnavailable` box** ("Q&A needs a language model", neutral/muted styling — NOT amber). If the LLM **is** configured, confirm the answer card renders (confidence badge / evidence / limitations / refused) — and note that the unavailable state couldn't be triggered live (it's still covered by the Task 1 unit test).
  - **Memo:** confirm the new lead-in renders above the "Monitoring memo" card. Click Generate. Same branch: neutral `LlmUnavailable` box ("Memo generation needs a language model") if unconfigured, else the memo renders via `MemoView`.
  Screenshot **light**, toggle **dark**; confirm both themes look right (the neutral box recolors correctly — muted surface, legible text, no amber), layout doesn't break, and **zero console errors** (an expected 4xx/5xx network response for the unavailable capability is fine and is not a console error to fix).
- [ ] **Step 3:** Fix any straggler (contrast on the neutral box, spacing), re-verify. Note the outcome, and explicitly note whether the LLM was configured (answer/memo rendered) or not (neutral box shown).

---

## Self-Review

**Spec coverage:** shared `LlmUnavailable` (Task 1, tested) reframes the amber state to neutral/informational and DRYs the duplicate; Ask lead-in + swap (Task 2); Memo lead-in + swap (Task 3); verified both themes (Task 4). The answer card, `MemoView`, forms, red failure, and empty states are untouched (stated in Global Constraints). Honest copy; no data/API change.

**Placeholder scan:** clean — complete code in every step; both removed amber blocks are quoted verbatim for exact matching.

**Type consistency:** `LlmUnavailable` props (`capability: string`, `message?: string`) match both call sites (`capability="Q&A"` / `"Memo generation"`, `message={(m.error as ApiError).message || undefined}` — `string | undefined`, matching the optional prop). `ApiError` stays imported/used on both pages (the red failure box uses `m.error instanceof ApiError`). Test assertions match the component's heading (`"{capability} needs a language model"`) and default-message substring (`isn't wired up`).
