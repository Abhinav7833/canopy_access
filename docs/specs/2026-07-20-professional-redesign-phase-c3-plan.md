# Professional Redesign — Phase C3 (Product-Screen Overhaul: Cross-check + Confidence) Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Finish the analytical pair with finance-legible framing and one substantive honesty fix — remove the Confidence "Drivers" fabricated contribution bars (a magnitude invented from list position) and present drivers as an honest sentiment-dot list, plus lead-ins on both screens. Both themes, presentation-only.

**Architecture:** Two dossier tab pages. Confidence: add a lead-in; replace the fabricated `RiskBar score={100 - i*18}` per driver with a dot-led list (dot colored by the existing text-derived `driverSentiment`, sourced from the canonical `TONE_BG` map), and reword the overclaiming "Ranked by contribution" header. Cross-check: sharpen the existing lead-in copy. No new component, no data/API change; the `StatusPill` status column, the `ConfidenceRating` gauge, and the risk-score `RiskBar` are all untouched.

**Tech Stack:** Next.js 16, Tailwind v4 tokens, TypeScript.

## Global Constraints

- **No data/behavior/API/schema change.** Same `useDossier`/`useProject` payloads and the same error/loading branches. Presentation + copy only.
- **Honesty is the point of this part.** The driver bars encode no real data (width = `Math.max(30, 100 - i*18)`, i.e. list position) and the "Ranked by contribution" label claims a scored ranking that does not exist (`drivers` is a `string[]`, unscored — see the `driverSentiment` docstring). Both must go. Do not replace them with any other invented magnitude/score.
- **`driverSentiment` coloring is retained** — it is a display heuristic derived from the driver's *own text* (risk-language → `medium`, else `low`), not invented data. The dot color uses `TONE_BG[driverSentiment(d)]` (the single-source tone→bg map, as `StatusPill`/`RiskMeter` do). Do not hand-duplicate class names.
- **Leave `StatusPill`, `ConfidenceRating`, and the risk-score `RiskBar` (confidence first card) untouched.** Only the Drivers card body + header and the two lead-ins change.
- **Honest copy only** — lead-ins describe what each screen actually does; no fabricated claims. The new Drivers header must not imply a scored ranking.
- **Reuse primitives + tokens**; light + dark parity; no motion added.
- **Commit hygiene (Canopy pre-commit gate):** code commits (`.tsx`) are blocked until the staged snapshot is reviewed. Under subagent-driven execution the controller keeps all git: the SDD task-review is the review of record, then `git write-tree > .git/canopy-review-marker` (its own executed step) and `git commit` (separate step). The docs-only Task 0 passes freely.

**Run** (from `frontend/`): `npx tsc --noEmit` · `npx eslint` · `npx vitest run` · `npx next build`. Dev `:3000`, backend `:8001`. Baseline: **9 files, 34 tests** — unchanged (no tests added; presentation-only).

---

### Task 0: Commit this plan (docs-only)

**Files:**
- Create: `docs/specs/2026-07-20-professional-redesign-phase-c3-plan.md` (this file)

- [ ] **Step 1: Commit**

```bash
git add docs/specs/2026-07-20-professional-redesign-phase-c3-plan.md
git commit -m "docs: Phase C3 plan — cross-check + confidence overhaul"
```

---

### Task 1: Confidence — lead-in + honest drivers (remove fabricated bars)

**Files:**
- Modify: `frontend/src/app/projects/[id]/confidence/page.tsx`

**Context:** Add a finance-legible lead-in above the gauge card. In the "Drivers" card, remove the invented per-driver bar and the "Ranked by contribution" claim; render drivers as a dot-led list (sentiment dot + text). The first card (gauge + risk-score + RiskBar + rationale) is unchanged.

- [ ] **Step 1: Add `TONE_BG` to the format import**

Change:
```tsx
import { riskTone, type RiskTone } from "@/lib/format";
```
to:
```tsx
import { riskTone, TONE_BG, type RiskTone } from "@/lib/format";
```

- [ ] **Step 2: Add the lead-in line**

Immediately after the opening `<div className="space-y-6">` (before the first `<Card>`), insert:

```tsx
      <p className="text-sm text-muted">
        The one rating the review acts on — how on-track this asset is against its disclosed
        claims, the risk score beneath it, and the signals that produced it, each traceable to
        the evidence upstream.
      </p>
```

- [ ] **Step 3: Replace the Drivers card body + fix the header**

Replace the entire Drivers `<Card>` (from `<Card>` with `title="Drivers"` through its closing `</Card>`):

```tsx
      <Card>
        <CardHeader
          title="Drivers"
          action={<span className="text-xs text-muted">Ranked by contribution</span>}
        />
        <CardBody className="space-y-4">
          {confidence.drivers.map((d, i) => {
            const tone = driverSentiment(d);
            const width = Math.max(30, 100 - i * 18);
            return (
              <div key={i}>
                <p className="mb-1.5 text-sm text-ink">{d}</p>
                <RiskBar score={width} tone={tone} />
              </div>
            );
          })}
        </CardBody>
      </Card>
```

with:

```tsx
      <Card>
        <CardHeader
          title="Drivers"
          action={<span className="text-xs text-muted">Signals behind the rating</span>}
        />
        <CardBody>
          <ul className="space-y-3">
            {confidence.drivers.map((d, i) => (
              <li key={i} className="flex gap-3">
                <span
                  className={`mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full ${TONE_BG[driverSentiment(d)]}`}
                  aria-hidden
                />
                <p className="text-sm text-ink">{d}</p>
              </li>
            ))}
          </ul>
        </CardBody>
      </Card>
```

(This drops the fabricated `width`/`RiskBar` per driver and the "Ranked by contribution" claim. `RiskBar` is still imported and used in the first card's risk-score block, so its import stays. `driverSentiment` + `RiskTone` + `riskTone` all still used.)

- [ ] **Step 4: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass; vitest unchanged (9 files / 34 tests). No unused imports (`RiskBar` still used in the first card; `TONE_BG` now used; `driverSentiment`/`riskTone`/`RiskTone` still used). Confirm no `100 - i * 18` / `Math.max(30, ...)` remains in the file.

- [ ] **Step 5: Report** (controller handles git). Suggested commit message:
```
feat(ui): Confidence — IC lead-in + honest drivers (drop fabricated contribution bars)
```

---

### Task 2: Cross-check — sharpen the lead-in (light)

**Files:**
- Modify: `frontend/src/app/projects/[id]/crosscheck/page.tsx`

**Context:** Cross-check already has its `StatusPill` status column, a lead-in, and a clean promised-vs-observed table with real data. This is an intentionally light pass: sharpen the existing lead-in for the IC framing (the validation moment). No table/logic change.

- [ ] **Step 1: Sharpen the lead-in**

Replace:
```tsx
      <p className="text-sm text-muted">
        Promised vs observed — each row cross-checks a disclosed claim against the imagery
        evidence gathered so far.
      </p>
```
with:
```tsx
      <p className="text-sm text-muted">
        Each disclosed claim, promised versus what the satellite record actually shows — the
        moment a financed claim either holds up or doesn&apos;t. The variance and the evidence
        behind every row are shown.
      </p>
```

- [ ] **Step 2: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass; vitest unchanged (9 files / 34 tests). No import changes.

- [ ] **Step 3: Report** (controller handles git). Suggested commit message:
```
feat(ui): Cross-check — sharpen IC-legible lead-in
```

---

### Task 3: Verify both screens + both themes in the browser

- [ ] **Step 1:** Gates green (re-confirm).
- [ ] **Step 2:** With dev (`:3000`) + backend (`:8001`) up, drive:
  - `/projects/nur_navoi_solar/confidence` and `/projects/mikoko_pamoja/confidence` — confirm the new lead-in renders above the gauge card; the gauge + risk-score block + rationale are intact; the **Drivers card no longer shows per-driver bars** (no horizontal bars under each driver), instead a **dot-led list** (a small colored dot before each driver line — amber for risk-language drivers, green otherwise), and the card header reads **"Signals behind the rating"** (NOT "Ranked by contribution").
  - `/projects/nur_navoi_solar/crosscheck` and `/projects/mikoko_pamoja/crosscheck` — confirm the sharpened lead-in renders; the promised-vs-observed table + `StatusPill` status column are intact.
  Screenshot **light**, toggle **dark**; confirm both themes look right (driver dots recolor correctly), layout doesn't break, and **zero console errors**.
- [ ] **Step 3:** Fix any straggler (dot alignment, wrapping), re-verify. Note the outcome.

---

## Self-Review

**Spec coverage:** Confidence lead-in + honest drivers (Task 1 — removes the fabricated bar magnitude and the "Ranked by contribution" overclaim, the honesty centerpiece); Cross-check lead-in sharpen (Task 2). `StatusPill`/`ConfidenceRating`/risk-score `RiskBar` untouched (stated in Global Constraints). Both verified in both themes (Task 3). Presentation/copy only; no new component; honest copy; dot color reuses `TONE_BG` (single source).

**Placeholder scan:** clean — complete code in every step; the removed Drivers block and the Cross-check lead-in are quoted verbatim for exact matching.

**Type consistency:** `driverSentiment(d): RiskTone` (`"low" | "medium"`) indexes `TONE_BG: Record<RiskTone, string>` — valid keys, returns a `bg-*` class. `RiskBar` remains used in the first card (`score={confidence.risk_score}`), so its import is not orphaned. No signatures change; no imports removed (only `TONE_BG` added).
