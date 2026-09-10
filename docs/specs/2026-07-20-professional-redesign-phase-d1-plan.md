# Professional Redesign — Phase D1 (Landing IA + Shell) Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Establish the landing-first information architecture — move the portfolio from `/` to `/portfolio`, put a presentable landing hero shell at `/`, refactor the page container out of the root layout so the landing can go full-bleed (D2/D3), and rewire the nav — with every existing product screen looking identical, both themes.

**Architecture:** The root layout stops wrapping children in `max-w-6xl`; each surface owns its container (dossier layout + the moved portfolio page add `mx-auto max-w-6xl px-6 py-8`; the landing controls its own). `app/page.tsx` (portfolio) moves to `app/portfolio/page.tsx` (route `/portfolio`) with its test; a new `app/page.tsx` is a minimal-but-real landing hero linking to `/portfolio`. Nav: the dossier back-link and a new TopBar link point at `/portfolio`; the brand stays at `/` (the landing). No data/API change.

**Tech Stack:** Next.js 16 (App Router), Tailwind v4 tokens, TypeScript, Vitest.

## Global Constraints

- **No data/behavior/API/schema change.** Routing + presentation only. Same `useProjects`/`useDossier` etc.
- **Existing product screens must look identical.** After moving the `max-w-6xl px-6 py-8` container out of the root layout, the dossier layout and the portfolio page MUST each re-add it, so `/portfolio` and every `/projects/[id]/*` page render byte-for-byte the same as before.
- **Route move, not copy:** `/` (portfolio) becomes `/portfolio`; the old `app/page.test.tsx` moves to `app/portfolio/page.test.tsx` (it tests the portfolio — it must NOT remain at `app/page.test.tsx` testing the new landing).
- **Nav correctness:** the dossier "← Portfolio" back-link → `/portfolio`; the TopBar brand link stays `/` (→ landing, conventional); add one TopBar "Portfolio" link → `/portfolio`. These are the ONLY two `href="/"` in the app today (verified: `projects/[id]/layout.tsx`, `TopBar.tsx`).
- **Honest copy** on the landing shell — describe what Canopy actually does; no fabricated customers/metrics/claims.
- **Landing CTA uses the theme-correct accent ink** (`text-accent-ink`, not `text-white`) so it reads in both themes.
- **Light + dark parity**; reuse primitives + tokens; no motion added.
- **Commit hygiene (Canopy pre-commit gate):** code commits are blocked until the staged snapshot is reviewed. Under subagent-driven execution the controller keeps all git: the SDD task-review is the review of record, then `git write-tree > .git/canopy-review-marker` (its own executed step) and `git commit` (separate step). The docs-only Task 0 passes freely. (File create/overwrite/`rm` are filesystem ops the implementer may do; only git is controller-owned.)

**Run** (from `frontend/`): `npx tsc --noEmit` · `npx eslint` · `npx vitest run` · `npx next build`. Dev `:3000`, backend `:8001`. Baseline: **10 files, 37 tests** — unchanged (the portfolio test moves, it isn't added/removed). `next build` must list routes `/`, `/portfolio`, and `/projects/[id]/*`.

---

### Task 0: Commit this plan (docs-only)

**Files:**
- Create: `docs/specs/2026-07-20-professional-redesign-phase-d1-plan.md` (this file)

- [ ] **Step 1: Commit**

```bash
git add docs/specs/2026-07-20-professional-redesign-phase-d1-plan.md
git commit -m "docs: Phase D1 plan — landing IA + shell"
```

---

### Task 1: IA move + layout refactor + nav rewire + landing hero shell

**Files:**
- Modify: `frontend/src/app/layout.tsx` (remove the shared container)
- Create: `frontend/src/app/portfolio/page.tsx` (moved portfolio + its own container)
- Create: `frontend/src/app/portfolio/page.test.tsx` (moved portfolio test)
- Delete: `frontend/src/app/page.test.tsx` (moved to `portfolio/`)
- Overwrite: `frontend/src/app/page.tsx` (portfolio → landing hero shell)
- Modify: `frontend/src/app/projects/[id]/layout.tsx` (add container; back-link → `/portfolio`)
- Modify: `frontend/src/components/layout/TopBar.tsx` (add "Portfolio" link)

- [ ] **Step 1: Remove the shared container from the root layout** — `frontend/src/app/layout.tsx`

Replace:
```tsx
        <Providers>
          <TopBar />
          <div className="mx-auto max-w-6xl px-6 py-8">{children}</div>
        </Providers>
```
with:
```tsx
        <Providers>
          <TopBar />
          {children}
        </Providers>
```

- [ ] **Step 2: Create the moved portfolio page** — `frontend/src/app/portfolio/page.tsx`

Copy the CURRENT `frontend/src/app/page.tsx` verbatim, with ONE change: the top-level `<div className="space-y-6">` becomes `<div className="mx-auto max-w-6xl px-6 py-8 space-y-6">` (re-adds the container the root layout no longer provides). Everything else — all imports (`@/…` absolute, unaffected by the move), the `Home` function, the `TableSkeleton`, the KPI tiles, the merged Rating column — is unchanged. (Read the current `app/page.tsx` and reproduce it exactly except for that one className.)

- [ ] **Step 3: Move the portfolio test** — create `frontend/src/app/portfolio/page.test.tsx` as a verbatim copy of the current `frontend/src/app/page.test.tsx` (its `import Home from "./page"` now resolves to `portfolio/page`; all assertions unchanged). Then **delete** `frontend/src/app/page.test.tsx` (e.g. `rm frontend/src/app/page.test.tsx`).

- [ ] **Step 4: Overwrite `app/page.tsx` with the landing hero shell** — `frontend/src/app/page.tsx`

Replace the ENTIRE file with:
```tsx
import Link from "next/link";

/** Marketing landing (the front door). Phase D1 ships a presentable hero shell; the
 * evidence-pipeline strip (D2) and the remaining sections (D3) fill in below it. */
export default function Landing() {
  return (
    <main>
      <section className="mx-auto max-w-4xl px-6 py-24 text-center sm:py-32">
        <p className="label">Green-finance evidence</p>
        <h1 className="mt-4 text-4xl font-semibold tracking-tight text-ink sm:text-5xl">
          Every financed claim, checked against the satellite record.
        </h1>
        <p className="mx-auto mt-5 max-w-2xl text-lg leading-relaxed text-muted">
          Canopy turns a green-bond disclosure into a located asset, tracked over time and
          cross-checked against what was promised — resolved to one explained confidence rating,
          with every figure traced to its evidence.
        </p>
        <div className="mt-8 flex items-center justify-center gap-3">
          <Link
            href="/portfolio"
            className="rounded-md bg-accent px-5 py-2.5 text-sm font-medium text-accent-ink transition-colors hover:bg-accent-hover"
          >
            View the validation set
          </Link>
        </div>
      </section>
    </main>
  );
}
```

- [ ] **Step 5: Add the container + fix the back-link in the dossier layout** — `frontend/src/app/projects/[id]/layout.tsx`

Change the root `<div className="space-y-6">` to `<div className="mx-auto max-w-6xl px-6 py-8 space-y-6">`, and change the back-link `href="/"` to `href="/portfolio"`. The full new return:
```tsx
  return (
    <div className="mx-auto max-w-6xl px-6 py-8 space-y-6">
      <Link
        href="/portfolio"
        className="inline-flex items-center gap-1.5 text-sm text-muted transition-colors hover:text-ink"
      >
        <span aria-hidden>←</span> Portfolio
      </Link>
      <ProjectHeader id={id} />
      <SectionNav id={id} />
      <div className="pt-1">{children}</div>
    </div>
  );
```

- [ ] **Step 6: Add the "Portfolio" link to the TopBar** — `frontend/src/components/layout/TopBar.tsx`

In the right cluster, add a "Portfolio" link before the "Demo environment" chip. Replace:
```tsx
        <div className="ml-auto flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1 text-xs text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            Demo environment
          </span>
          <ThemeToggle />
        </div>
```
with:
```tsx
        <div className="ml-auto flex items-center gap-2">
          <Link
            href="/portfolio"
            className="rounded-md px-2.5 py-1 text-sm text-muted transition-colors hover:text-ink"
          >
            Portfolio
          </Link>
          <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1 text-xs text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            Demo environment
          </span>
          <ThemeToggle />
        </div>
```
(The brand `<Link href="/">` stays as-is — it points at the landing. `Link` is already imported.)

- [ ] **Step 7: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass. Vitest **10 files / 37 tests** (the portfolio test moved, count unchanged). `next build` route list shows `○ /`, `○ /portfolio` (or `ƒ`), and the `/projects/[id]/*` routes — confirm `/portfolio` exists and there is no leftover portfolio at `/`. No unused imports. No stray `app/page.test.tsx`.

- [ ] **Step 8: Report** (controller handles git; it will `git add -A` so the rename + deletion are staged). Suggested commit message:
```
feat(ui): landing IA — portfolio → /portfolio, hero shell at /, container refactor
```

---

### Task 2: Verify the IA move + shell + both themes in the browser

- [ ] **Step 1:** Gates green (re-confirm).
- [ ] **Step 2:** With dev (`:3000`) + backend (`:8001`) up, drive:
  - `/` — confirm the **landing hero shell** renders (eyebrow, headline "Every financed claim, checked against the satellite record.", subhead, a **"View the validation set"** button). Click it → lands on `/portfolio`.
  - `/portfolio` — confirm the **portfolio** renders exactly as it used to (featured-asset hero gauge, KPI tiles, the single "Rating" column table) — same width/padding as before (the `max-w-6xl` container is preserved), nothing full-bleed or misaligned.
  - `/projects/nur_navoi_solar` — confirm the dossier renders normally (ProjectHeader, SectionNav, content) at the same width as before; the **"← Portfolio"** back-link goes to `/portfolio`.
  - **TopBar** — the "Portfolio" link goes to `/portfolio`; the brand goes to `/` (landing).
  For the landing and the portfolio, screenshot **light**, toggle **dark**; confirm both themes look right, the CTA button is legible in both (accent-ink), layout isn't broken, and **zero console errors**.
- [ ] **Step 3:** Fix any straggler (container padding drift on portfolio/dossier, CTA contrast), re-verify. Note the outcome.

---

## Self-Review

**Spec coverage:** portfolio moved to `/portfolio` with its test (Task 1 Steps 2–3), container refactored out of the root layout with each surface re-adding it so existing screens are unchanged (Steps 1, 2, 5), landing hero shell at `/` (Step 4), nav rewired — dossier back-link + new TopBar link → `/portfolio`, brand → `/` (Steps 5–6), verified both themes + that existing screens look identical (Task 2). Honest copy; theme-correct CTA; no data/API change. Pipeline strip (D2) and full landing sections (D3) are explicitly deferred.

**Placeholder scan:** clean — complete code in every step. The one "copy the current file verbatim except one className" step (portfolio move) is explicit about the single change and that imports are unaffected by the move.

**Type consistency:** no signatures change. The moved `app/portfolio/page.tsx` keeps the exact component/imports of the current `app/page.tsx` (only its root `className` gains the container utilities). The moved test's `import Home from "./page"` resolves within `app/portfolio/`. The landing is a self-contained server component using only `next/link`. `app/projects/[id]/layout.tsx` and `TopBar.tsx` already import `Link`, so no new imports.

**Deferred/batched note:** the existing Ask/Memo generate/ask buttons use `text-white` on `bg-accent` (a latent dark-mode contrast nit vs the theme-correct `text-accent-ink` the landing CTA uses) — out of scope for D1; log for a later polish pass. `app/_folder_context.md` describes the old route layout and will be stale after the move — flag for an arch-tidy/folder-doc follow-up.
