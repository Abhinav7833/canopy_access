---
module: app
owns: [routes, components, styles, assets]
last_reviewed: b99d4eb970e2
---
# app

The Next.js App Router tree: the marketing landing, the validation-set portfolio, the per-project evidence screens, plus the root layout, global styles/design tokens, and favicon.

## Structure
- layout.tsx — root layout; loads Geist fonts, sets metadata, runs the inline no-flash `data-theme` bootstrap, and wraps children in `<Providers>` (from `providers.tsx`) with a persistent `<TopBar>`. Holds no width container — each surface sets its own `mx-auto max-w-* px-6`.
- page.tsx — `/` marketing landing (server component). Two-column hero with the live `HeroDossierPanel` (client island: the primary asset's real AOI + confidence rating), the `EvidencePipeline` "how it works" strip, `RatingExplainer`, `TrustBand`, a closing CTA, and a footer.
- portfolio/page.tsx — `/portfolio` the validation-set list: a guarded featured-asset hero (`ConfidenceRating` via `useDossier(PRIMARY_PROJECT_ID)`), KPI `Stat` tiles, and the assets table (Primary badge on `PRIMARY_PROJECT_ID`).
- globals.css — Tailwind import + the light/dark design system: runtime `--c-*` palette vars mapped to Tailwind `--color-*` utilities via `@theme` (so utilities flip with `data-theme`), the `.label`/`.tnum` helpers, and the global `prefers-reduced-motion` guard.
- favicon.ico — site icon
- projects/[id]/ — dynamic project route group sharing `layout.tsx` (a "← Portfolio" back link + `ProjectHeader` + `SectionNav` tabs with a persistent `EvidenceLauncher`). The tabs are the linear disclosure → confidence narrative:
  - page.tsx — `/projects/[id]` Disclosure (step 1): source document + extracted claims table
  - locate/page.tsx — Locate (step 2): claimed region → located AOI via the `AoiEvidenceLayer` canvas + candidates ruled out
  - timeline/page.tsx — Observe (step 3): `EvidenceMap` before/after swipe + a dated build-progress snapshot timeline
  - crosscheck/page.tsx — Cross-check (step 4): promised vs observed, one row per claim, status as a `StatusPill`
  - confidence/page.tsx — Confidence (step 5): the `ConfidenceRating` gauge + risk score + the honest signals behind it
  - ask/page.tsx — `AskPanel` for evidence-grounded Q&A
  - memo/page.tsx — triggers report generation and renders it via `MemoView`

  Dossier-driven tabs render `DossierUnavailable` when a project has no dossier fixture (404 → calm empty state); the Ask/Memo screens render the calm `LlmUnavailable` state when no language model is configured.

## Public interface
None — pages and layouts are resolved by Next.js file-system routing, not imported by other modules.

## Depends on
`components/features/*` (landing: HeroDossierPanel, EvidencePipeline, RatingExplainer, TrustBand; signature: ConfidenceRating, AoiEvidenceLayer; dossier: ProjectHeader, SectionNav, EvidenceLauncher, EvidenceDrawer, EvidenceCard, AskPanel, MemoView, TraceChip, DossierUnavailable, LlmUnavailable), `components/map/EvidenceMap`, `components/ui/*` (incl. StatusPill), `components/layout/*` (TopBar, ThemeToggle), `lib/*` (queries, api, dossier, format, config, gauge, aoiGeometry, geo, theme, types), and `providers.tsx`.
