# Professional Redesign — Phase D3 — Landing content (hero visual · explainer · trust · CTA · footer)

Parent design: `docs/specs/2026-07-20-professional-redesign-design.md` (Phase D landing, line 84).
Branch: `canopy-mvp`. Base: tip of D2 (`4095737`). Presentation-only — no backend/API/data change.

## Goal

Complete the marketing landing (`app/page.tsx`). D1 shipped the hero shell; D2 shipped the "how it
works" pipeline strip. D3 adds the remaining sections so the page reads as a finished, finance-credible
front door. **Final page order:** Hero (copy + CTA + **live product panel** + trust microline) →
How it works (D2) → What the rating means → Methodology / trust band → Closing CTA → Footer.

**Hard rule (from the design spec, non-negotiable): NO fabricated trust signals** — no fake customer
logos, testimonials, SOC-2/compliance badges, or invented metrics. Every number/claim on the page is
either the real featured dossier's live value or an honest description of the method. Light+dark parity,
WCAG-AA, status-never-by-color-alone, honor `prefers-reduced-motion`, tokens-only (no hex).

## Decision (locked with user)

Hero visual = **live product panel**: the featured (PRIMARY) asset's real located-AOI canvas
(`AoiEvidenceLayer`) + confidence rating gauge (`ConfidenceRating`), pulled live from its dossier —
the same live-data path the portfolio's featured hero already proves works. Client island with graceful
fallback (loading → skeleton; error/absent → a quiet neutral placeholder that keeps the hero balanced,
never an alarming error on the front door).

## Task 1 — Hero live product panel + hero restructure

New `frontend/src/components/features/HeroDossierPanel.tsx` (**client**):
- Fetches the featured asset via `useDossier(PRIMARY_PROJECT_ID)`, `useBoundary(PRIMARY_PROJECT_ID)`,
  `useProject(PRIMARY_PROJECT_ID)` (all from `@/lib/queries`; `PRIMARY_PROJECT_ID` from `@/lib/config`).
- Renders a `Card` "product panel": `AoiEvidenceLayer` (boundary + `localization.located_centroid` +
  `project.asset_type` + `boundary.properties.area_hectares`, at a shorter hero height e.g. `h-64`)
  above a footer row = featured-asset name (links to `/projects/{PRIMARY}`) + `ConfidenceRating`
  (`pct=confidence.on_track_pct`, `band=confidence.risk_band`, smaller `size`). Clearly labeled as the
  real featured asset (honest, not a generic mock).
- **Graceful states:** loading (any query pending) → a `CardSkeleton`-style shimmer of the same footprint;
  success (boundary + `dossier.confidence` + project all present) → the live panel; error/absent → a
  quiet static neutral card of the same size (no error text on the marketing hero). Mirror the portfolio's
  guard idiom (`primaryDossier?.confidence && primary`). Never leave the hero's second column empty.
- Reuses existing signature components unchanged; no new data hooks.

Edit `frontend/src/app/page.tsx` hero `<section>`:
- Restructure the centered hero into a **two-column** layout on `lg+` (copy/CTA/trust-microline left,
  `<HeroDossierPanel />` right), **stacked** on mobile (copy first, panel below). Keep the D1 headline,
  subcopy, and primary CTA verbatim (left-aligned in the two-col layout).
- Add a one-line honest **trust microline** under the CTA: "Independent satellite evidence · every figure
  cited · one explained rating."
- Refresh the top-of-file doc comment (D3 shipped).

Tests `HeroDossierPanel.test.tsx` (RTL, mock `@/lib/queries` like `portfolio/page.test.tsx` does):
loading → skeleton present; success (mock dossier/boundary/project) → featured-asset name + rating
aria-label render; error/absent → neutral fallback, no crash, no error copy.

## Task 2 — Explainer · trust band · closing CTA · footer

New `frontend/src/components/features/RatingExplainer.tsx` (**server**) — "What the rating means":
honest explanation of the on-track confidence rating + the Low/Med/High **risk bands** (reuse `Badge`
with `riskTone`; real semantics, NO invented magnitudes — this is the same honesty fix applied on the
Confidence screen in C3). Three band rows, each a one-line meaning.

New `frontend/src/components/features/TrustBand.tsx` (**server**) — three methodology pillars, each a
short honest description (no logos/testimonials/badges):
- **Independent evidence** — Sentinel satellite + the disclosure document, not the issuer's word.
- **Everything cited** — every figure traces back to its source (the real `TraceChip` provenance system).
- **One explained rating** — a single confidence rating with the signals behind it shown, not a black box.

Edit `frontend/src/app/page.tsx` — append, after the D2 "how it works" section:
- `<RatingExplainer />` section (eyebrow + h2 + the band rows).
- `<TrustBand />` section (eyebrow + h2 + 3 pillars, hairline-separated per the elevation system).
- Closing **CTA** section: short line + repeat the primary CTA ("View the validation set" → `/portfolio`,
  `text-accent-ink` not `text-white`).
- **Footer** (`<footer>`): minimal + honest — `BrandMark`/brand name + one honest line ("Disclosure-anchored
  evidence for green-finance claims.") + a muted "Demo · validation set" note (matches the TopBar "Demo
  environment" pill). No fake legal/social/company links.

Tests: light RTL for `RatingExplainer` + `TrustBand` (band labels / pillar headings present) — presentational,
mirror the 3-`it` house pattern.

## Verification

- Gates from `frontend/`: `npx tsc --noEmit && npx eslint && npx vitest run && npx next build`
  (vitest count rises with the new tests; `next build` still lists `/`, `/portfolio`, `/projects/[id]/*`).
  Note: `/` may shift from static (○) to server-rendered because the hero panel island fetches — acceptable
  (the panel is a client island; the surrounding page content stays server-rendered).
- Playwright drive `/` in **both** themes at desktop + mobile: hero two-col (copy + live panel showing the
  real Nur Navoi AOI + 85%/Low gauge) → stacks cleanly on mobile; explainer, trust band, CTA, footer all
  render; every section legible (AA), light↔dark repaint clean incl. the AOI canvas; **0 console errors**;
  no clipped text (re-run the D2 detector); no horizontal overflow. Confirm graceful fallback by observing
  the loading skeleton. Confirm the D2 pipeline strip + hero copy/CTA still intact.

## Out of scope / batched for a later docs pass

- Ask/Memo `text-white`→`text-accent-ink` buttons (D1/D2 batched nit) — fold in opportunistically if touched,
  else defer.
- `app/_folder_context.md` (stale route description) + `components/_folder_context.md` (predates Phase B/C)
  full refresh — a dedicated docs-cleanup pass (arch-tidy), not D3.
