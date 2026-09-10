# Professional Redesign — Phase B (Signature Components, part 3: ConfidenceRating rollout) Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Roll the existing part-1 `ConfidenceRating` gauge into its two remaining homes — the **Confidence tab** (replacing the flat on-track-% cluster) and the **portfolio** (a new "Featured asset" hero gauge for the primary project) — so the hero trust object reads consistently across the app, in both themes.

**Architecture:** Pure reuse. No new component, helper, or test — `ConfidenceRating` (`components/features/ConfidenceRating.tsx`, `<ConfidenceRating pct band size? />`) already exists, is theme-aware, and is reduced-motion-safe. This part only re-homes it: two page edits (`confidence/page.tsx`, `app/page.tsx`). The portfolio hero reads the primary project's dossier via the existing `useDossier` query (cached, non-blocking). Presentation-only; same data.

**Tech Stack:** Next.js 16, Tailwind v4 tokens, TypeScript, Vitest (jsdom), SVG (via the reused component).

## Global Constraints

- **No data/behavior/API/schema change.** Same `useProjects`/`useDossier` payloads. The portfolio hero uses one additional `useDossier(PRIMARY_PROJECT_ID)` call — the endpoint already exists; no new endpoint, no aggregation.
- **No new component, helper, or hook.** Reuse `ConfidenceRating` verbatim (do not modify it). If a change to `ConfidenceRating` seems necessary, STOP and report — it is out of scope for this part.
- **Light + dark parity, reduced-motion** are already handled inside `ConfidenceRating` (SVG stroke from `--color-risk-*` tokens; animation via a global CSS `transition-duration` that `prefers-reduced-motion` zeroes). Do not add motion/theme logic at the call sites.
- **`ConfidenceRating` props:** `pct: number | null`, `band: string | null`, `size?: number` (default 116). `pct` is the integer on-track percent (0–100), same value the `ProjectHeader` passes. `confidence.on_track_pct` is typed `number`; `confidence.risk_band` is `string | null`.
- **Graceful degradation:** the portfolio's featured hero renders **only** when the primary dossier has loaded (`primaryDossier?.confidence`); the KPI stats and the assets table must render regardless of the hero's load/error state. Never block the portfolio on the hero query.
- **Phase-C boundary:** leave `RiskBar`/`RiskScore` and the portfolio **table rows** (the `RiskScore` + `Band` columns) untouched — those are Phase C. This part only adds the gauge; it does not restyle the risk primitives.
- **Keep Geist** (the gauge's score uses `font-mono` = Geist Mono, tabular-nums — inherited from the component).
- **Commit hygiene (Canopy pre-commit gate):** code commits (`.tsx`) are blocked by `.claude/hooks/pre-commit-review.sh` until the staged snapshot is reviewed. Under subagent-driven execution the controller keeps all git: the SDD task-review is the review of record, then `git write-tree > .git/canopy-review-marker` (its own executed step) and `git commit` (separate step). The docs-only commit in Task 0 passes freely.

**Run** (from `frontend/`): `npx tsc --noEmit` · `npx eslint` · `npx vitest run` · `npx next build`. Dev server on `:3000`, backend `:8001`. Current baseline: **8 test files, 30 tests** passing (this part adds no tests, so the count is unchanged).

---

### Task 0: Commit this plan (docs-only)

**Files:**
- Create: `docs/specs/2026-07-20-professional-redesign-phase-b-part3-plan.md` (this file)

- [ ] **Step 1: Commit** (docs-only, passes the gate freely)

```bash
git add docs/specs/2026-07-20-professional-redesign-phase-b-part3-plan.md
git commit -m "docs: Phase B plan (part 3) — ConfidenceRating rollout"
```

---

### Task 1: Confidence tab — swap the flat on-track cluster for the gauge

**Files:**
- Modify: `frontend/src/app/projects/[id]/confidence/page.tsx`

**Interfaces:**
- Consumes: `ConfidenceRating` from `@/components/features/ConfidenceRating`.
- Removes usage of: `formatPercent` (was only used for the flat `on_track_pct`); the inline band `Badge` in the risk-score block (the gauge now shows the band).

**Context:** The first `Card` currently renders a flex row: left = a flat `text-5xl` `on_track_pct` (via `formatPercent`), right = `risk_score` (3xl) + band `Badge` + `RiskBar`. Replace the left block with the gauge and drop the now-duplicate band `Badge` from the right block. Keep the `risk_score` number + `RiskBar` (Phase C owns `RiskBar`), the rationale, and the entire Drivers card unchanged.

- [ ] **Step 1: Add the import**

At the top of `confidence/page.tsx`, add (keep the existing imports; `RiskBar`, `Badge`, `Card*`, `TraceChip`, `DossierUnavailable`, `useDossier`, `riskTone`, `RiskTone` all stay):

```tsx
import { ConfidenceRating } from "@/components/features/ConfidenceRating";
```

- [ ] **Step 2: Replace the first card's on-track row**

Find this block (the flex row inside the first `<CardBody className="space-y-5">`):

```tsx
          <div className="flex flex-wrap items-end justify-between gap-6">
            <div>
              <p className="label mb-1">On track</p>
              <p className="font-mono text-5xl font-semibold leading-none tabular-nums text-accent">
                {formatPercent(confidence.on_track_pct)}
              </p>
            </div>
            <div className="text-right">
              <p className="label mb-1">Risk score</p>
              <p className="font-mono text-3xl font-semibold leading-none tabular-nums text-ink">
                {confidence.risk_score ?? "—"}
              </p>
              <div className="mt-2 flex flex-col items-end gap-2">
                {confidence.risk_band && <Badge tone={band}>{confidence.risk_band}</Badge>}
                <RiskBar score={confidence.risk_score} tone={band} className="w-32" />
              </div>
            </div>
          </div>
```

Replace it with (gauge on the left; risk-score block keeps the number + `RiskBar` but loses the duplicate band `Badge`):

```tsx
          <div className="flex flex-wrap items-center justify-between gap-6">
            <ConfidenceRating pct={confidence.on_track_pct} band={confidence.risk_band} />
            <div className="text-right">
              <p className="label mb-1">Risk score</p>
              <p className="font-mono text-3xl font-semibold leading-none tabular-nums text-ink">
                {confidence.risk_score ?? "—"}
              </p>
              <RiskBar score={confidence.risk_score} tone={band} className="mt-2 w-32" />
            </div>
          </div>
```

- [ ] **Step 3: Remove the now-unused `formatPercent` import**

The `formatPercent` import is no longer used (it was only the flat on-track value). Change:

```tsx
import { formatPercent, riskTone, type RiskTone } from "@/lib/format";
```
to:
```tsx
import { riskTone, type RiskTone } from "@/lib/format";
```

(`Badge` is **still used** elsewhere? Check: after Step 2 the only `Badge` usage in this file was the one just removed. Grep `Badge` in the file — if no usages remain, also remove `import { Badge } from "@/components/ui/Badge";`. If any remain, keep it. As of the current file the risk-score block was the only `Badge`, so remove its import too.)

- [ ] **Step 4: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass; vitest unchanged at **8 files / 30 tests**. **No unused-import lint error** (`formatPercent`, and `Badge` if removed).

- [ ] **Step 5: Report** (controller handles git — do not commit)

Report DONE with the gate output. The controller stages, runs the SDD review, records the marker, and commits:
```
feat(ui): Confidence tab — gauge as the on-track hero (rollout)
```

---

### Task 2: Portfolio — featured-asset hero gauge for the primary project

**Files:**
- Modify: `frontend/src/app/page.tsx`

**Interfaces:**
- Consumes: `ConfidenceRating` from `@/components/features/ConfidenceRating`; `Card` from `@/components/ui/Card`; `useDossier` from `@/lib/queries`; `PRIMARY_PROJECT_ID` from `@/lib/config` (already imported); `titleCase` from `@/lib/format` (already imported).

**Context:** Add a "Featured asset" hero `Card` between the `PageHeader` and the KPI `Stat` grid, showing the primary project's `ConfidenceRating` (from its dossier's `confidence.on_track_pct` + `risk_band`) alongside its name / meta / link (from the already-fetched `useProjects()` list). Non-blocking: hidden until the dossier loads.

- [ ] **Step 1: Add the imports + the hero query + primary lookup**

Add these imports at the top (keep all existing imports):

```tsx
import { ConfidenceRating } from "@/components/features/ConfidenceRating";
import { Card } from "@/components/ui/Card";
```

`useDossier` — add it to the existing queries import:

```tsx
import { useProjects, useDossier } from "@/lib/queries";
```
(was `import { useProjects } from "@/lib/queries";`)

Inside `Home()`, after `const projects = data ?? [];`, add:

```tsx
  const { data: primaryDossier } = useDossier(PRIMARY_PROJECT_ID);
  const primary = projects.find((p) => p.id === PRIMARY_PROJECT_ID);
```

- [ ] **Step 2: Render the hero between `PageHeader` and the `Stat` grid**

Immediately after the closing `</PageHeader>`… (the `<PageHeader ... />` self-closing tag) and **before** the `<div className="grid grid-cols-2 gap-4 sm:grid-cols-4">` stat grid, insert:

```tsx
      {primaryDossier?.confidence && primary && (
        <Card className="flex flex-wrap items-center justify-between gap-6 px-5 py-5">
          <div className="min-w-0">
            <p className="label mb-1">Featured asset</p>
            <Link
              href={`/projects/${primary.id}`}
              className="text-xl font-semibold tracking-tight text-ink hover:text-accent"
            >
              {primary.name}
            </Link>
            <p className="mt-1 text-sm text-muted">
              {[titleCase(primary.asset_type), primary.country, titleCase(primary.financing_type)]
                .filter((x): x is string => Boolean(x) && x !== "—")
                .join("  ·  ")}
            </p>
          </div>
          <ConfidenceRating
            pct={primaryDossier.confidence.on_track_pct}
            band={primaryDossier.confidence.risk_band}
          />
        </Card>
      )}
```

(`Link` is already imported at the top of `app/page.tsx`. `titleCase` is already imported. The `Card` component composes `className` after its own base classes, so the flex utilities here lay out the card's direct children.)

- [ ] **Step 3: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass; vitest unchanged at **8 files / 30 tests**. No unused-import or type errors. Confirm the portfolio still renders its stats + table when `primaryDossier` is undefined (the hero is guarded by `primaryDossier?.confidence && primary`).

- [ ] **Step 4: Report** (controller handles git — do not commit)

Report DONE with the gate output. The controller stages, runs the SDD review, records the marker, and commits:
```
feat(ui): portfolio — featured-asset confidence gauge (rollout)
```

---

### Task 3: Verify both homes + both themes in the browser

- [ ] **Step 1:** Gates green (Task 2 Step 3 already ran them; re-confirm nothing regressed).
- [ ] **Step 2:** With dev (`:3000`) + backend (`:8001`) up, drive:
  - `/projects/nur_navoi_solar/confidence` and `/projects/mikoko_pamoja/confidence` — confirm the first card now shows the **gauge** (arc filled to the on-track %, band-colored, "On track" label, band Badge), the `risk_score` number + `RiskBar` still render beside it (no duplicate band Badge), and the rationale + Drivers card are intact.
  - `/` (portfolio) — confirm the **Featured asset** hero card renders the primary (`nur_navoi_solar`) gauge with name/meta/link, and the KPI stats + assets table still render below it.
  For each screen, screenshot **light**, then toggle **dark**. Confirm both themes look right, the gauge arc + band color are correct, layout doesn't break, and there are **zero console errors**.
- [ ] **Step 3:** Confirm the portfolio degrades gracefully — the stats + table are present and the page doesn't error even before/without the hero.
- [ ] **Step 4:** Fix any straggler (contrast, layout), re-verify. Note the outcome.

---

## Self-Review

**Spec coverage:** the ConfidenceRating gauge is rolled into the Confidence tab (Task 1) and the portfolio (Task 2, as a primary-asset featured hero — the honest treatment given the list payload lacks `on_track_pct`), verified in both homes/themes (Task 3). No new component/helper/test — pure reuse, matching the "no new component" constraint. `RiskBar`/`RiskScore` and the portfolio table rows are left for Phase C (stated in Global Constraints). The evidence-pipeline strip is **deferred to Phase D** (its prominent home is the landing "how it works"; the in-app narrative is already served by `SectionNav`).

**Placeholder scan:** clean — complete code in every step. The one conditional instruction (remove the `Badge` import only if no usages remain) is resolved explicitly: as of the current file, the removed risk-score block was the sole `Badge` usage, so its import is removed.

**Type consistency:** `ConfidenceRating` props (`pct: number | null`, `band: string | null`) match both call sites — Confidence tab passes `confidence.on_track_pct` (`number`) + `confidence.risk_band` (`string | null`); portfolio passes `primaryDossier.confidence.on_track_pct` + `.risk_band`. `useDossier(PRIMARY_PROJECT_ID)` returns the dossier whose `.confidence` shape is `{ on_track_pct: number; risk_band: string | null; ... }`. `primary` is a `ProjectSummary` (`id`, `name`, `asset_type`, `country`, `financing_type`), matching the hero's field reads.
