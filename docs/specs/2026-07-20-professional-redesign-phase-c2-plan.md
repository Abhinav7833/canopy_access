# Professional Redesign — Phase C2 (Product-Screen Overhaul: Locate + Observe) Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Sharpen the geospatial evidence pair with finance-legible framing + stronger hierarchy — elevate Locate's "what we ruled out" trust signal into its own card, and re-treat Observe's dated snapshots as a proper build-progress timeline — keeping the existing `AoiEvidenceLayer` (Locate) and `EvidenceMap` swipe (Observe) intact. Both themes, presentation-only.

**Architecture:** Pure JSX/copy changes on two dossier tab pages. Locate: add a lead-in line and move `alternatives_rejected` out of the Localization card into a dedicated "Candidates ruled out" card. Observe: add a lead-in line and render `observation_series` as a connected vertical timeline (dot-and-line gutter + content) instead of flat divided rows. No new component, no data/API change; the Observe map (`EvidenceMap` + swipe) is untouched.

**Tech Stack:** Next.js 16, Tailwind v4 tokens, TypeScript.

## Global Constraints

- **No data/behavior/API/schema change.** Same `useBoundary`/`useDossier`/`useImagery`/`useProject` payloads and the same error/loading branches. Presentation + copy only.
- **Keep the Observe map + swipe exactly as-is.** `EvidenceMap`, the `images`/`resolve`/`swipe` logic, and the range input are NOT modified (they remain ready for the real Sentinel raster data track). Only the surrounding framing + the "Dated snapshots" list treatment change.
- **Keep `AoiEvidenceLayer` on Locate as-is.** Only the non-map content (lead-in, Localization card, alternatives) changes.
- **Honest copy only** — no fabricated claims/metrics. Lead-ins describe what the screen actually does; nothing over-promises the imagery.
- **Reuse primitives + tokens.** `Card`/`CardHeader`/`CardBody`, `TraceChip`, `formatDate`/`formatNumber`, `typeConfig` are already imported on their pages. Colors from tokens (both themes). The timeline dot reuses the accent/faint tokens (same dot language as `StatusPill`).
- **Light + dark parity.** No hard-coded colors; no motion added.
- **Commit hygiene (Canopy pre-commit gate):** code commits (`.tsx`) are blocked until the staged snapshot is reviewed. Under subagent-driven execution the controller keeps all git: the SDD task-review is the review of record, then `git write-tree > .git/canopy-review-marker` (its own executed step) and `git commit` (separate step). The docs-only Task 0 passes freely.

**Run** (from `frontend/`): `npx tsc --noEmit` · `npx eslint` · `npx vitest run` · `npx next build`. Dev `:3000`, backend `:8001`. Baseline: **9 files, 34 tests** — unchanged (no tests added; presentation-only).

---

### Task 0: Commit this plan (docs-only)

**Files:**
- Create: `docs/specs/2026-07-20-professional-redesign-phase-c2-plan.md` (this file)

- [ ] **Step 1: Commit**

```bash
git add docs/specs/2026-07-20-professional-redesign-phase-c2-plan.md
git commit -m "docs: Phase C2 plan — locate + observe overhaul"
```

---

### Task 1: Locate — lead-in + elevate "Candidates ruled out"

**Files:**
- Modify: `frontend/src/app/projects/[id]/locate/page.tsx`

**Context:** Add a finance-legible lead-in line, and move the `alternatives_rejected` block out of the Localization `CardBody` into its own prominent card after it (a stronger "what we ruled out and why" trust signal). The `AoiEvidenceLayer` card and the rest of the Localization card are unchanged.

- [ ] **Step 1: Add the lead-in line**

Immediately after the opening `<div className="space-y-6">` (before the `<Card>` with "Located asset"), insert:

```tsx
      <p className="text-sm text-muted">
        The claimed region, resolved to one located asset. Nothing downstream — the imagery, the
        cross-checks, the confidence rating — holds if this match is wrong, so the candidates
        ruled out are shown alongside it.
      </p>
```

- [ ] **Step 2: Remove the alternatives block from the Localization card**

Delete this block (the last child inside the Localization `<CardBody className="space-y-4">`, i.e. everything from the `{localization.alternatives_rejected.length > 0 && (` line through its closing `)}`):

```tsx
          {localization.alternatives_rejected.length > 0 && (
            <div className="border-t border-border pt-3">
              <p className="label mb-2">Alternatives rejected</p>
              <ul className="space-y-1.5 text-xs text-muted">
                {localization.alternatives_rejected.map((a, i) => (
                  <li key={i} className="flex gap-1.5">
                    <span className="text-faint">—</span>
                    <span>
                      <span className="font-medium text-ink">{a.name}</span>: {a.reason}
                    </span>
                  </li>
                ))}
              </ul>
            </div>
          )}
```

The Localization `CardBody` now ends with the `{localization.method}` paragraph.

- [ ] **Step 3: Add the "Candidates ruled out" card**

After the closing `</Card>` of the Localization card and before the final `</div>`, insert:

```tsx
      {localization.alternatives_rejected.length > 0 && (
        <Card>
          <CardHeader
            title="Candidates ruled out"
            action={<span className="text-xs text-muted">Why this AOI, and not the alternatives</span>}
          />
          <CardBody>
            <ul className="space-y-3">
              {localization.alternatives_rejected.map((a, i) => (
                <li key={i} className="flex gap-3">
                  <span className="mt-1.5 h-1.5 w-1.5 shrink-0 rounded-full bg-faint" aria-hidden />
                  <p className="text-sm text-muted">
                    <span className="font-medium text-ink">{a.name}</span> — {a.reason}
                  </p>
                </li>
              ))}
            </ul>
          </CardBody>
        </Card>
      )}
```

(`Card`, `CardHeader`, `CardBody` are already imported. No import changes.)

- [ ] **Step 4: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass; vitest unchanged (9 files / 34 tests). No unused imports (all of `Badge`, `RiskBar`, `TraceChip`, `Card*`, `confidenceValueTone`, `formatPercent` still used).

- [ ] **Step 5: Report** (controller handles git). Suggested commit message:
```
feat(ui): Locate — IC lead-in + elevate "candidates ruled out" to its own card
```

---

### Task 2: Observe — lead-in + build-progress timeline

**Files:**
- Modify: `frontend/src/app/projects/[id]/timeline/page.tsx`

**Context:** Add a finance-legible lead-in line and re-treat the "Dated snapshots" list as a connected vertical timeline (a dot-and-line gutter beside each snapshot's content), making the real build-progress evidence the star. The map card + swipe are untouched.

- [ ] **Step 1: Add the lead-in line**

Immediately after the opening `<div className="space-y-6">` (before the first `<Card>`), insert:

```tsx
      <p className="text-sm text-muted">
        Sentinel snapshots tracking the asset&apos;s build progress over time — each dated
        observation and its measured footprint, checked against the disclosed timeline.
      </p>
```

- [ ] **Step 2: Re-treat "Dated snapshots" as a vertical timeline**

Replace this block (the `series.length > 0 ? (...) : (...)` inside the second `<Card>`):

```tsx
        {series.length > 0 ? (
          <div className="divide-y divide-border">
            {series.map((s, i) => (
              <div key={i} className="px-5 py-4">
                <div className="flex items-start justify-between gap-3">
                  <p className="font-mono text-xs tabular-nums text-faint">{formatDate(s.date)}</p>
                  <TraceChip traces_to={s.trace?.traces_to} />
                </div>
                <p className="mt-2 text-sm leading-relaxed text-ink">{s.note}</p>
                <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted">
                  <span>
                    {typeConfig.footprintLabel}:{" "}
                    <span className="font-mono tabular-nums text-ink">
                      {formatNumber(s.footprint_ha, { unit: "ha" })}
                    </span>
                  </span>
                  {s.ndvi != null && (
                    <span>
                      NDVI: <span className="font-mono tabular-nums text-ink">{s.ndvi.toFixed(2)}</span>
                    </span>
                  )}
                  {s.trace?.source && <span className="text-faint">{s.trace.source}</span>}
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div className="px-5 py-12 text-center text-sm text-muted">
            No dated snapshots recorded yet.
          </div>
        )}
```

with:

```tsx
        {series.length > 0 ? (
          <ol className="px-5 py-4">
            {series.map((s, i) => (
              <li key={i} className="flex gap-4">
                <div className="flex flex-col items-center" aria-hidden>
                  <span className="mt-1.5 h-2.5 w-2.5 shrink-0 rounded-full border-2 border-surface bg-accent" />
                  {i < series.length - 1 && <span className="w-px flex-1 bg-border" />}
                </div>
                <div className="flex-1 pb-6 last:pb-0">
                  <div className="flex items-start justify-between gap-3">
                    <p className="font-mono text-xs tabular-nums text-faint">{formatDate(s.date)}</p>
                    <TraceChip traces_to={s.trace?.traces_to} />
                  </div>
                  <p className="mt-1.5 text-sm leading-relaxed text-ink">{s.note}</p>
                  <div className="mt-2 flex flex-wrap gap-4 text-xs text-muted">
                    <span>
                      {typeConfig.footprintLabel}:{" "}
                      <span className="font-mono tabular-nums text-ink">
                        {formatNumber(s.footprint_ha, { unit: "ha" })}
                      </span>
                    </span>
                    {s.ndvi != null && (
                      <span>
                        NDVI: <span className="font-mono tabular-nums text-ink">{s.ndvi.toFixed(2)}</span>
                      </span>
                    )}
                    {s.trace?.source && <span className="text-faint">{s.trace.source}</span>}
                  </div>
                </div>
              </li>
            ))}
          </ol>
        ) : (
          <div className="px-5 py-12 text-center text-sm text-muted">
            No dated snapshots recorded yet.
          </div>
        )}
```

The gutter renders an accent dot per snapshot and a hairline connector to the next (skipped on the last), producing a vertical build-progress timeline. Same data/fields as before; no logic change.

- [ ] **Step 3: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass; vitest unchanged (9 files / 34 tests). No import changes (`formatDate`, `formatNumber`, `TraceChip`, `typeConfig` still used; the map imports untouched).

- [ ] **Step 4: Report** (controller handles git). Suggested commit message:
```
feat(ui): Observe — IC lead-in + build-progress snapshot timeline
```

---

### Task 3: Verify both screens + both themes in the browser

- [ ] **Step 1:** Gates green (re-confirm).
- [ ] **Step 2:** With dev (`:3000`) + backend (`:8001`) up, drive:
  - `/projects/nur_navoi_solar/locate` and `/projects/mikoko_pamoja/locate` — confirm the new lead-in line renders above the AOI canvas card; the Localization card no longer contains the alternatives list; a separate **"Candidates ruled out"** card renders below it with dot-led `name — reason` rows (when the asset has rejected alternatives). AOI canvas + Localization confidence/method intact.
  - `/projects/nur_navoi_solar/timeline` and `/projects/mikoko_pamoja/timeline` — confirm the new lead-in line renders; the **map + swipe are unchanged and still work**; the "Dated snapshots" section now renders as a **vertical timeline** (accent dots connected by a hairline down the left, each node showing date · note · footprint · NDVI · trace).
  Screenshot **light**, toggle **dark**; confirm both themes look right (dots/connectors/borders recolor correctly), layout doesn't break, and **zero console errors**.
- [ ] **Step 3:** Fix any straggler (dot alignment on the timeline gutter, spacing, wrapping), re-verify. Note the outcome.

---

## Self-Review

**Spec coverage:** Locate lead-in + elevated "Candidates ruled out" card (Task 1); Observe lead-in + build-progress vertical timeline (Task 2); map/swipe + `AoiEvidenceLayer` untouched (stated in Global Constraints, guarded in Task 3). Both verified in both themes (Task 3). Presentation/copy only — no new component, no data change, honest copy.

**Placeholder scan:** clean — complete code in every step; the removed Locate block and both Observe blocks are quoted verbatim for exact matching.

**Type consistency:** no signatures change. `alternatives_rejected` items expose `{ name, reason }` (already used by the pre-move code). `observation_series` items expose `date`, `note`, `footprint_ha`, `ndvi`, `trace` (unchanged fields, same accessors). `typeConfig.footprintLabel`, `formatNumber(s.footprint_ha, { unit: "ha" })`, `formatDate(s.date)` all identical to the pre-change usage. No imports added or removed on either page.
