---
module: lib
owns: [routes, utils, tests]
last_reviewed: b99d4eb970e2
---
# lib

The backend API client, TanStack Query hooks, display formatting + tone maps, theming, gauge/AOI geometry, shared types, and small config — with colocated Vitest tests.

## Structure
- api.ts — the API client: `get`/`post` fetch helpers hitting the same-origin `/api/*` proxy, exported as the `api` object (`listProjects`, `getProject`, `getBoundary`, `getImagery`, `getEvidence`, `getDossier`, `ask`, `createReport`, `getReport`), plus `ApiError` — a typed error carrying the HTTP `status` and backend `code`/`message` from the `{error:{…}}` envelope (used to surface the LLM-unavailable notice). Note: labeled kind "route" by the analyzer because the filename contains "api", but it is a client, not a route handler.
- format.ts — display formatting (`titleCase`, `formatNumber`, `formatPercent`, `formatDate`) and the semantic tone system: `RiskTone`, the mappers `riskTone`/`confidenceTone`/`confidenceValueTone`/`crossCheckTone`, and the canonical class maps `TONE_BG`/`TONE_TEXT` (single source for risk/confidence coloring). Keeps raw snake_case and ratios out of the UI.
- queries.ts — TanStack Query hooks wrapping `api` (`useProjects`, `useProject`, `useBoundary`, `useImagery`, `useEvidence`, `useDossier`)
- theme.ts — light/dark theme: resolve/persist/toggle helpers over `localStorage` key `canopy-theme` and the `data-theme` attribute on `<html>` (drives the `globals.css` token flip; used by `ThemeToggle` + the no-flash layout script)
- gauge.ts — SVG gauge math (`circumference`, `arcOffset`) for `ConfidenceRating`
- aoiGeometry.ts — seeded procedural terrain + polygon projection helpers (`terrainAt`, `fitTransform`, `projectRing`, `gridLines`, `perimeter`, `toPx`, …) for the `AoiEvidenceLayer` canvas
- geo.ts — map geometry helpers: `bbox()` (bounding box from a boundary ring), `imageCoords()` (orders corners TL, TR, BR, BL for MapLibre image sources)
- config.ts — `PRIMARY_PROJECT_ID`, the lead validation asset (single source of truth for the "Primary"/featured asset)
- types.ts — shared TS interfaces for backend payloads (ProjectSummary, ProjectDetail, Imagery, ImageLayer, Evidence, AskResponse, Report, Boundary, and the Dossier tree: Dossier/Disclosure/Claim/Localization/ObservationSeriesPoint/CrossCheckItem/Confidence)
- dossier.ts, assetType.ts — dossier presentation: `claimLabel(kind, assetType?)`/`formatClaimValue` (dossier.ts) and the per-`asset_type` config map `ASSET_TYPES`/`assetTypeConfig()` (assetType.ts) giving solar vs mangrove their own claim labels, Observe title, and footprint label
- *.test.ts — colocated Vitest tests: api, geo, dossier, smoke, gauge, aoiGeometry, theme

## Public interface
`api` + `ApiError` (api.ts), the formatting + tone helpers (format.ts), the `use*` hooks (queries.ts), theme helpers (theme.ts), gauge/AOI/geo math (gauge.ts/aoiGeometry.ts/geo.ts), `PRIMARY_PROJECT_ID` (config.ts), dossier helpers (dossier.ts/assetType.ts), and all exported types (types.ts) — imported throughout `app/` and `components/`.

## Depends on
`@tanstack/react-query`, the FastAPI backend via same-origin `/api/*`, and `vitest`/`@testing-library` (test files only).
