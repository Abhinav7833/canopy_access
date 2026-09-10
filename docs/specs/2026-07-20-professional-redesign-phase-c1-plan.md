# Professional Redesign — Phase C1 (Product-Screen Overhaul: Portfolio + Disclosure) Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sharpen the two entry screens with the A+B system: merge the portfolio's Risk+Band columns into one **Rating** column, reframe its weakest KPI tile for a finance audience, backfill the deferred portfolio hero-present test, and tighten the Disclosure screen's framing — both themes, presentation-only.

**Architecture:** Repurpose the portfolio-only `RiskScore` primitive into a compact "score + band chip" rating (the same number+chip language the `ConfidenceRating` gauge uses), and drop the portfolio's separate Band column. Reframe one KPI `Stat`. Add a Vitest for the part-3 featured hero. Light copy/hierarchy pass on Disclosure. No new components; no data/API change.

**Tech Stack:** Next.js 16, Tailwind v4 tokens, TypeScript, Vitest + @testing-library/react + jest-dom.

## Global Constraints

- **No data/behavior/API/schema change.** Same `useProjects`/`useDossier` payloads. Presentation + copy only.
- **`RiskScore` is portfolio-only** (verified: sole caller is `app/page.tsx`) — safe to restyle. **Do NOT touch `RiskBar`** (used by `confidence` + `locate`) — leave its signature and rendering intact.
- **Reuse the shared tone vocabulary.** The rating's band chip uses `Badge tone={riskTone(band)}` (do not reinvent the mapping). Colors from tokens only (both themes).
- **Honest copy — no fabricated claims/metrics.** The reframed KPI tile and Disclosure copy must state only what is true (satellite + disclosure evidence, every figure cited/traced). No invented numbers, no fake customers/certifications.
- **Consistency with the gauge:** the rating shows the score in `text-ink` (mono, `tabular-nums`) + the band as a filled `Badge` — the same pattern `ConfidenceRating` uses (score neutral, band carries color). Do not band-color the number.
- **Light + dark parity** (inherited from tokens). No motion added.
- **Commit hygiene (Canopy pre-commit gate):** code commits (`.tsx`) are blocked until the staged snapshot is reviewed. Under subagent-driven execution the controller keeps all git: the SDD task-review is the review of record, then `git write-tree > .git/canopy-review-marker` (its own executed step) and `git commit` (separate step). The docs-only Task 0 passes freely.

**Run** (from `frontend/`): `npx tsc --noEmit` · `npx eslint` · `npx vitest run` · `npx next build`. Dev `:3000`, backend `:8001`. Baseline: **9 files, 33 tests**; this part adds 1 test (portfolio hero) → **9 files, 34 tests**.

---

### Task 0: Commit this plan (docs-only)

**Files:**
- Create: `docs/specs/2026-07-20-professional-redesign-phase-c1-plan.md` (this file)

- [ ] **Step 1: Commit**

```bash
git add docs/specs/2026-07-20-professional-redesign-phase-c1-plan.md
git commit -m "docs: Phase C1 plan — portfolio + disclosure overhaul"
```

---

### Task 1: Portfolio — Rating column + KPI reframe + hero test

**Files:**
- Modify: `frontend/src/components/ui/RiskMeter.tsx` (repurpose `RiskScore`)
- Modify: `frontend/src/app/page.tsx` (merge columns, reframe tile, drop unused import)
- Modify: `frontend/src/app/page.test.tsx` (add hero-present test)

**Interfaces:**
- `RiskScore({ score: number | null, band: string | null, className?: string })` — unchanged signature; new rendering (score + band `Badge`).

- [ ] **Step 1: Repurpose `RiskScore`** — `frontend/src/components/ui/RiskMeter.tsx`

Replace the whole `RiskScore` function (keep `RiskBar` above it exactly as-is) and add the `Badge` import. The full new file:

```tsx
import { Badge } from "@/components/ui/Badge";
import { riskTone, TONE_BG, type RiskTone } from "@/lib/format";

export function RiskBar({
  score,
  tone,
  className = "",
}: {
  score: number | null;
  tone: RiskTone;
  className?: string;
}) {
  const pct = Math.max(0, Math.min(100, score ?? 0));
  return (
    <div className={`h-1.5 overflow-hidden rounded-full bg-surface-muted ${className}`}>
      <div className={`h-full rounded-full ${TONE_BG[tone]}`} style={{ width: `${pct}%` }} />
    </div>
  );
}

/** Compact rating for table cells: the numeric score (neutral, tabular) paired with its risk
 * band as a filled chip — the same score+band language the ConfidenceRating gauge uses. */
export function RiskScore({
  score,
  band,
  className = "",
}: {
  score: number | null;
  band: string | null;
  className?: string;
}) {
  return (
    <div className={`flex items-center gap-2 ${className}`}>
      <span className="font-mono text-sm font-semibold tabular-nums text-ink">{score ?? "—"}</span>
      {band && <Badge tone={riskTone(band)}>{band}</Badge>}
    </div>
  );
}
```

- [ ] **Step 2: Run the existing portfolio tests, expect PASS** — `cd frontend && npx vitest run src/app/page.test.tsx`

The band-regression test (`getByText("medium")`) still passes: the band now renders inside `RiskScore`'s `Badge` (still exactly one "medium" in the DOM, since the separate Band column is removed in the next step). All good so far; the merge happens next.

- [ ] **Step 3: Merge Risk+Band → one Rating column + reframe the KPI tile** — `frontend/src/app/page.tsx`

(a) The table header — replace these two lines:
```tsx
              <Th align="right">Risk</Th>
              <Th align="center">Band</Th>
```
with a single column:
```tsx
              <Th align="right">Rating</Th>
```

(b) The row cells — replace this block:
```tsx
                <Td align="right">
                  <RiskScore score={p.risk_score} band={p.risk_band} className="justify-end" />
                </Td>
                <Td align="center">
                  {p.risk_band ? <Badge tone={riskTone(p.risk_band)}>{p.risk_band}</Badge> : "—"}
                </Td>
```
with the single merged cell:
```tsx
                <Td align="right">
                  <RiskScore score={p.risk_score} band={p.risk_band} className="justify-end" />
                </Td>
```

(c) Reframe the 4th KPI tile — replace:
```tsx
        <Stat label="Evidence" value="Live" sub="Precomputed store · seeded" tone="accent" />
```
with:
```tsx
        <Stat
          label="Evidence"
          value="Independent"
          sub="Satellite + disclosure, every figure cited"
          tone="accent"
        />
```

(d) Drop the now-unused `riskTone` import. Change:
```tsx
import { titleCase, riskTone } from "@/lib/format";
```
to:
```tsx
import { titleCase } from "@/lib/format";
```
(`Badge` import STAYS — the "Primary" chip at the asset cell still uses it. `RiskScore` import stays.)

- [ ] **Step 4: Add the featured-hero test** — `frontend/src/app/page.test.tsx`

Replace the whole file with (converts the `useDossier` mock to a per-test mutable value, keeps both existing assertions, adds the hero-present test):

```tsx
import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import type { ProjectSummary } from "@/lib/types";
import Home from "./page";

vi.mock("next/navigation", () => ({
  useRouter: () => ({ push: vi.fn() }),
}));

const project: ProjectSummary = {
  id: "nur_navoi_solar",
  name: "Navoi Solar",
  asset_type: "solar",
  country: "Uzbekistan",
  financing_type: "green_bond",
  status: "active",
  risk_score: 42,
  risk_band: "medium",
};

// Per-test dossier for the featured-asset hero. Read lazily inside the mocked hook (invoked
// during render), so tests set it before rendering; undefined => hero hidden.
let heroDossier: { confidence: { on_track_pct: number; risk_band: string | null } } | undefined;

vi.mock("@/lib/queries", () => ({
  useProjects: () => ({ data: [project], isLoading: false, isError: false }),
  useDossier: () => ({ data: heroDossier }),
}));

afterEach(() => {
  heroDossier = undefined;
});

describe("Home (portfolio)", () => {
  it("renders a link to the project's detail page with the project name", () => {
    render(<Home />);
    const link = screen.getByRole("link", { name: "Navoi Solar" });
    expect(link).toHaveAttribute("href", `/projects/${project.id}`);
  });

  it("renders the risk band for each asset", () => {
    render(<Home />);
    // Regression guard: the portfolio must surface the risk band (Badge) per row — now inside
    // the merged Rating column's RiskScore rather than a separate Band column.
    expect(screen.getByText(project.risk_band!)).toBeInTheDocument();
  });

  it("shows the featured-asset hero gauge when the primary dossier is present", () => {
    heroDossier = { confidence: { on_track_pct: 85, risk_band: "low" } };
    render(<Home />);
    expect(screen.getByText("Featured asset")).toBeInTheDocument();
    // Both the hero link and the table-row link target the primary project, so its name
    // appears twice — assert both rather than the singular getByRole (which would throw).
    expect(screen.getAllByRole("link", { name: "Navoi Solar" })).toHaveLength(2);
  });
});
```

- [ ] **Step 5: Run tests, expect PASS** — `npx vitest run src/app/page.test.tsx` (3 pass). Then `npx tsc --noEmit` exit 0.

- [ ] **Step 6: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass. Vitest **9 files / 34 tests**. No unused-import lint errors in `app/page.tsx` (`riskTone` removed; `Badge`/`RiskScore`/`Stat` still used) or `RiskMeter.tsx`.

- [ ] **Step 7: Report** (controller handles git). Suggested commit message:
```
feat(ui): portfolio — merged Rating column + finance-framed KPI tile + hero test
```

---

### Task 2: Disclosure — tighten framing (light)

**Files:**
- Modify: `frontend/src/app/projects/[id]/page.tsx`

**Context:** The Disclosure screen is already clean (tokenized card + claims table). This is an intentionally light pass: sharpen the two pieces of framing copy for an investment-committee reader, and give the "Claims extracted" section a clearer heading. No structural/data change.

- [ ] **Step 1: Sharpen the PageHeader description**

Replace:
```tsx
        description="Every number on this asset starts here — the financed claim, before any satellite evidence is checked against it."
```
with:
```tsx
        description="The financed claims, exactly as disclosed — the baseline every downstream figure is checked against. Nothing here is verified yet; that starts at Locate."
```

- [ ] **Step 2: Elevate the "Claims extracted" section header**

Replace this block:
```tsx
      <div className="flex items-center justify-between">
        <p className="label">Claims extracted</p>
        <span className="text-xs text-muted">{claims.length} from this document</span>
      </div>
```
with a clearer heading + supporting line:
```tsx
      <div className="flex items-end justify-between">
        <div>
          <h2 className="text-sm font-semibold text-ink">Claims extracted</h2>
          <p className="mt-0.5 text-xs text-muted">Each is the promise a downstream screen must corroborate.</p>
        </div>
        <span className="text-xs text-muted">{claims.length} from this document</span>
      </div>
```

- [ ] **Step 3: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass; vitest unchanged at **9 files / 34 tests**. No unused imports introduced/removed.

- [ ] **Step 4: Report** (controller handles git). Suggested commit message:
```
feat(ui): Disclosure — IC-legible framing + clearer claims section header
```

---

### Task 3: Verify both screens + both themes in the browser

- [ ] **Step 1:** Gates green (re-confirm).
- [ ] **Step 2:** With dev (`:3000`) + backend (`:8001`) up, drive:
  - `/` (portfolio) — confirm the table now has a single **Rating** column showing `score + band Badge` per row (no separate Band column), the featured-asset hero still renders, and the KPI row's 4th tile reads **Evidence / Independent / "Satellite + disclosure, every figure cited"** (no "Precomputed store · seeded"). Table still scans cleanly; row click/hover intact.
  - `/projects/nur_navoi_solar` (Disclosure) — confirm the sharpened PageHeader description and the new "Claims extracted" heading + supporting line render; source-document card + claims table intact.
  Screenshot **light**, toggle **dark**; confirm both themes look right, the band Badge colors are correct, and there are **zero console errors**.
- [ ] **Step 3:** Fix any straggler (alignment, wrapping, contrast), re-verify. Note the outcome.

---

## Self-Review

**Spec coverage:** portfolio Rating-column merge (Task 1 Steps 1,3 — the deferred RiskScore restyle), KPI finance-reframe (Task 1 Step 3c), deferred hero-present test (Task 1 Step 4), Disclosure framing (Task 2) — all present, verified both themes (Task 3). No new component; `RiskScore` repurposed in place; `RiskBar` untouched. Honest copy only (Evidence tile + Disclosure text state only what's true).

**Placeholder scan:** clean — complete code in every step.

**Type consistency:** `RiskScore` keeps its `{ score: number|null, band: string|null, className? }` signature, so the portfolio call site is unchanged (only the surrounding columns change). The test's `heroDossier` shape (`{ confidence: { on_track_pct: number, risk_band: string|null } }`) matches what `app/page.tsx` reads (`primaryDossier.confidence.on_track_pct` / `.risk_band`). `riskTone(band)` returns `RiskTone`, valid for `Badge`'s `tone`. Removing `riskTone` from `app/page.tsx` imports is safe — its only use was the deleted Band cell.
