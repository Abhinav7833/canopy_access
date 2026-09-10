---
module: src
owns: [modules, components]
last_reviewed: b99d4eb970e2
---
# src

The Next.js app source root: route tree, UI components, the backend client + query hooks + theming, and the client-provider wrapper.

## Structure
- app/ — Next.js App Router routes: the root layout, the `/` marketing landing, the `/portfolio` validation-set list, and the `projects/[id]/` dossier screens (disclosure → locate → observe → cross-check → confidence, plus ask and memo); also `globals.css` (the light/dark design tokens)
- components/ — reusable UI, split into `layout/` (TopBar, ThemeToggle), `features/` (page-level + signature widgets), `map/` (EvidenceMap), and `ui/` (Badge, Card, StatusPill, Stat, RiskMeter, Table, PageHeader primitives)
- lib/ — backend API client (`api.ts`), TanStack Query hooks (`queries.ts`), formatting + tone maps (`format.ts`), theming (`theme.ts`), gauge/AOI/geo math (`gauge.ts`/`aoiGeometry.ts`/`geo.ts`), shared types (`types.ts`), config (`config.ts`), and colocated Vitest tests
- providers.tsx — client-side `Providers` wrapper that mounts a `QueryClientProvider`, used once by `app/layout.tsx`

## Public interface
Not imported as a module itself — `app/layout.tsx` imports `Providers` from `providers.tsx`; everything else here is consumed via the subdir paths (`@/components/...`, `@/lib/...`).

## Depends on
`@tanstack/react-query`, `maplibre-gl`, `next`, and the FastAPI backend reached through `lib/api.ts` (proxied at `/api/*`). State is local/react-query — there is no global store.
