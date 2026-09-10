# Professional Redesign — Phase D2 — Evidence-pipeline strip + "how it works"

Parent design: `docs/specs/2026-07-20-professional-redesign-design.md` (signature component #3, lines 69–74; Phase D landing, line 84).
Branch: `canopy-mvp`. Base: tip of D1 (`d7b1b19`). Presentation-only — no backend/API/data change.

## Goal

Fill the space the D1 hero shell reserved below it (`frontend/src/app/page.tsx:3-4`) with the
**evidence-pipeline strip**: the `disclosure → locate → observe → cross-check → confidence`
sequence as a **numbered, connected 5-node strip, one line each, final node accented**, inside a
landing **"how it works"** section. The remaining landing sections (explainer, trust band, CTA,
footer) stay in D3.

## Decisions (locked)

- **Static explainer** (user-chosen): nodes are non-interactive. The existing hero CTA
  ("View the validation set" → `/portfolio`) remains the single conversion path. This keeps the
  strip a **pure server component** with no coupling to `PRIMARY_PROJECT_ID`, and leaves it reusable
  as an optional in-app rail later.
- **Component boundary:** the reusable strip is `EvidencePipeline`; the landing-specific section
  wrapper (eyebrow + h2 + intro) lives in `page.tsx`.
- **In-app rail use is deferred** — `SectionNav` already serves the in-app narrative; D2 ships the
  landing use only.

## Task 1 — `EvidencePipeline` component + tests

New file `frontend/src/components/features/EvidencePipeline.tsx`:
- Named `export function EvidencePipeline({ className = "" }: { className?: string })` — matches the
  house convention (inline anonymous props type, named export, `className` passthrough). No
  `"use client"` (no hooks, no motion → reduced-motion is trivially satisfied; the "one orchestrated
  moment" the spec reserves is the confidence arc, not this strip).
- Local `STAGES` const (5 entries, order is the story) with `label` + one-line `detail`, honest copy
  mirroring each dossier page's real intro:
  1. Disclosure — "The financed claims, exactly as disclosed."
  2. Locate — "The claimed region, resolved to one asset."
  3. Observe — "Sentinel snapshots tracking build progress over time."
  4. Cross-check — "Promised versus what the satellite record shows."
  5. Confidence — "One explained rating, every figure traced to its evidence."
- Markup: `<ol>` (sequence is semantic), one `<li>` per stage = numbered badge (`font-mono`,
  Geist Mono numerals per spec) + `<h3>` label + `<p>` detail. Final node badge accented
  (`bg-accent text-accent-ink border-accent-border`); others `bg-surface text-ink border-border`.
- Connected rail: a single `aria-hidden` hairline (`bg-border`) behind the badges, `hidden md:block`,
  `inset-x-[10%]` so it spans exactly badge-1-centre → badge-5-centre (5 equal 20%-wide columns,
  `md:gap-0` + `md:px-3` keeps centres at 10/30/50/70/90%). Badges paint over it (`relative z-10` +
  solid bg) so it reads as connecting them.
- Responsive: mobile = vertical stack (badge left, text right); `md+` = 5 centred columns.
- Tokens only (never hex); uses `text-accent-ink` on accent (not `text-white` — avoids the D1-flagged
  dark-contrast nit). Status not by colour alone: the accented node also carries the text label
  "Confidence" and the number 5.

New file `frontend/src/components/features/EvidencePipeline.test.tsx` (RTL, 3 `it`s per house pattern):
1. renders the five stage labels in narrative order,
2. numbers the stages 1–5,
3. accents only the final (Confidence) node.

## Task 2 — wire into the landing

Edit `frontend/src/app/page.tsx`:
- Import `EvidencePipeline`.
- Below the hero `<section>`, add a `<section className="border-t border-border">` (hairline divide
  per the elevation system) with `mx-auto max-w-6xl px-6 py-20 sm:py-24`, containing a left-aligned
  header (`.label` "How it works" + `<h2>` + one intro `<p>`) and `<EvidencePipeline className="mt-14" />`.
- Refresh the top-of-file doc comment to note D2 shipped, D3 remains.
- If `components/**/_folder_context.md` enumerates the public component set, add `EvidencePipeline`.

## Verification

- Gates from `frontend/`: `npx tsc --noEmit && npx eslint && npx vitest run && npx next build`
  (expect vitest 37 → 40: +3 new tests; `next build` still lists `/`, `/portfolio`, `/projects/[id]/*`).
- Playwright drive `/` in **both** themes: header + 5 numbered nodes render, rail connects them,
  Confidence node accented, copy legible (AA), light↔dark repaint clean, 0 console errors. Confirm the
  hero above is untouched and the portfolio route still loads.

## Out of scope (D3)

Landing hero live-dossier visual (ConfidenceRating + AoiEvidenceLayer), the "what the rating means"
explainer, methodology/trust band, closing CTA, footer. Batched nits to fold into D3: the two
Ask/Memo `text-white` on `bg-accent` buttons; `app/_folder_context.md` route description stale after
the portfolio move.
