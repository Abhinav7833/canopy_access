---
module: components
owns: [components]
last_reviewed: b99d4eb970e2
---
# components

Reusable UI split by role: the app-chrome layout, page-level feature widgets, the MapLibre evidence map, and the low-level presentational primitives that carry the green light+dark design system.

## Structure
- layout/ — TopBar (sticky app header: brand mark + context + "Demo environment" chip + the theme toggle) and ThemeToggle (light/dark switch, persists via `lib/theme`), rendered by the root layout
- features/ — page-level widgets:
  - Signature: ConfidenceRating (SVG confidence gauge), AoiEvidenceLayer (Canvas AOI evidence layer, asset-type-aware terrain), EvidencePipeline (numbered, connected 5-node disclosure→confidence "how it works" strip)
  - Landing: HeroDossierPanel (client island — the featured asset's live AOI + rating, with a graceful loading/unavailable frame), RatingExplainer (what the rating means), TrustBand (three honest method pillars)
  - Dossier: ProjectHeader (per-project title + rating header), SectionNav (per-project tab navigation), EvidenceLauncher + EvidenceDrawer + EvidenceCard (the evidence sheet), TraceChip (quiet "← source" provenance chip), AskPanel (grounded Q&A), MemoView (renders generated memo markdown)
  - Calm states: DossierUnavailable (no dossier), LlmUnavailable (no language model configured)
- map/ — EvidenceMap: MapLibre GL map that draws a project boundary and reconciles before/after/overlay image layers in place (exports the `MapImage` type)
- ui/ — design-system primitives: Badge, Card (+ `CardHeader`/`CardBody`/`CardSkeleton`/`EmptyState`), StatusPill (semantic dot + label), Stat (labeled metric tile), RiskMeter (`RiskBar`/`RiskScore`), Table (`Table`/`Thead`/`Th`/`Tbody`/`Td`), PageHeader

## Public interface
Named exports imported by `app/` route pages and by each other: `TopBar`, `ThemeToggle` (layout/); the feature widgets above (features/); `EvidenceMap` + `MapImage` (map/); `Badge`, `Card`/`CardHeader`/`CardBody`/`CardSkeleton`/`EmptyState`, `StatusPill`, `Stat`, `RiskBar`/`RiskScore`, `Table`/`Thead`/`Th`/`Tbody`/`Td`, `PageHeader` (ui/).

## Depends on
`lib/types.ts`, `lib/api.ts` + `ApiError` (AskPanel/MemoView), `lib/queries.ts` (`useProject`/`useDossier`/`useBoundary`/`useEvidence`/…), `lib/format.ts` (formatting + tone maps `riskTone`/`TONE_BG`/`TONE_TEXT`), `lib/gauge.ts` (ConfidenceRating), `lib/aoiGeometry.ts` + `lib/geo.ts` (AoiEvidenceLayer/EvidenceMap), `lib/theme.ts` (ThemeToggle), `lib/config.ts` (PRIMARY_PROJECT_ID), `maplibre-gl`, `next/link`, `next/navigation`.
