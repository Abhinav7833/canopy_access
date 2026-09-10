# Canopy Frontend — Implementation Plan (Plan 3 of 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build the Next.js + MapLibre frontend — the 7 spec screens that turn the backend's stored evidence into a finance-grade experience: select a project, inspect its boundary + before/after imagery, review metrics with auditable evidence, ask bounded questions, and generate a memo.

**Architecture:** A Next.js (App Router, TypeScript) app talks to the backend only through a same-origin Next proxy (`/api/*` → backend), so there is no CORS and no remote host in the browser. TanStack Query owns server state; Zustand owns light UI state. MapLibre GL renders the AOI **without any base tiles** — the RGB/overlay PNGs are georeferenced to the boundary's bounding box and the boundary is drawn as a vector layer. All libraries are bundled via npm (no CDN `<script>`/`<link>`).

**Tech Stack:** Next.js 15 (App Router) + React 19 + TypeScript (strict), Tailwind CSS, MapLibre GL JS, TanStack Query, Zustand, Vitest + React Testing Library.

## Global Constraints

- **No CDN assets — ever.** This user's browser blocks CDN libraries and public map-tile hosts. Every dependency is installed via npm and bundled; no `<script src="https://...">`, no CDN fonts, no remote tiles. (The app's own API and `localhost` are fine.) MapLibre CSS is imported from the `maplibre-gl` package.
- **Mapping = MapLibre GL, no base tiles.** Empty style (solid background); add each imagery PNG as a georeferenced `image` source pinned to the AOI bounding box (derived from the boundary GeoJSON); draw the boundary as a `line` layer. Before/after = two image layers with an opacity swipe.
- **Backend access via Next proxy.** `next.config.ts` rewrites `/api/:path*` **and** `/static/:path*` → the backend (default `http://localhost:8001`), so both the API and the imagery assets are same-origin. The browser never calls a remote host. Backend must be running + seeded (`docker compose up -d` → `uv run alembic upgrade head` → `uv run python ../scripts/seed.py` → `uv run uvicorn app.main:app --port 8001`).
- **State:** TanStack Query for all server data; Zustand only for ephemeral UI (selected overlay, swipe position, drawer open). No optimistic updates (reads are cheap; the two writes — ask/memo — are pessimistic).
- **Evidence is the product.** Every screen surfaces provenance — source, method, confidence, limitations — never a bare number. Conservative language throughout (monitoring / screening / evidence / proxy / limitations).
- **Theme:** dark "green-finance" palette defined once as Tailwind tokens; consistent Card/Badge/Button primitives.
- **Quality gate:** the pre-commit hook runs `eslint .` + `tsc --noEmit` for `frontend/` once `package.json` exists; Vitest covers the API client and pure logic. Visual screens are verified by running the dev server and checking in the browser. Commits: `git add` then `git commit` as separate steps; record the review marker first.
- **Port:** Next dev on `3000`; backend on `8001`.

---

## File Structure

```
frontend/
  package.json  tsconfig.json  next.config.ts  vitest.config.ts  eslint config
  postcss.config.mjs
  src/
    app/
      layout.tsx                  # root: providers + app chrome
      globals.css                 # tailwind + theme tokens
      page.tsx                    # (1) Portfolio / Project Selector
      projects/[id]/
        layout.tsx                # project shell: header + section nav
        page.tsx                  # (2) Project Overview (map + metadata)
        timeline/page.tsx         # (3) Evidence Timeline
        metrics/page.tsx          # (4) Metrics Dashboard + (5) Evidence Drawer
        ask/page.tsx              # (6) Ask Canopy
        memo/page.tsx             # (7) Generate Memo
    lib/
      types.ts                    # TS types mirroring backend schemas
      api.ts                      # typed fetch client (same-origin /api)
      queries.ts                  # TanStack Query hooks
      geo.ts                      # bbox + image-corner helpers
    providers.tsx                 # QueryClientProvider
    stores/ui.ts                  # Zustand UI store
    components/
      ui/{Card,Badge,Button,Stat,Spinner}.tsx
      map/EvidenceMap.tsx         # MapLibre, no tiles
      features/{ProjectCard,SectionNav,MetricTile,EvidenceCard,EvidenceDrawer,AskPanel,MemoView}.tsx
  src/lib/*.test.ts  src/components/**/*.test.tsx
```

---

### Task 1: Scaffold Next.js + Tailwind + proxy + theme

**Files:** create the `frontend/` project, `next.config.ts`, `globals.css`, `vitest.config.ts`, a smoke test.

- [ ] **Step 1: Create the app**

```bash
cd /Users/cemkilinc/Desktop/Canopy
npx create-next-app@latest frontend --ts --tailwind --eslint --app --src-dir --import-alias "@/*" --use-npm --yes
```
`--yes` accepts defaults non-interactively. (If the installed create-next-app rejects a flag, drop it and re-run; the only requirements are TS + Tailwind + App Router + `src/` + the `@/*` alias.)

- [ ] **Step 2: Add runtime + dev deps**

```bash
cd frontend
npm install maplibre-gl @tanstack/react-query zustand
npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom @vitejs/plugin-react
```

- [ ] **Step 3: Proxy the backend in `next.config.ts`**

```ts
import type { NextConfig } from "next";

const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8001";

const nextConfig: NextConfig = {
  async rewrites() {
    return [
      { source: "/api/:path*", destination: `${BACKEND_URL}/:path*` },
      { source: "/static/:path*", destination: `${BACKEND_URL}/static/:path*` },
    ];
  },
};

export default nextConfig;
```

- [ ] **Step 4: Theme tokens in `src/app/globals.css`**

Replace the file body (keep the Tailwind import line create-next-app added) and append:
```css
:root {
  --bg: #0b1512;
  --panel: #10201a;
  --border: #1e3a2e;
  --text: #e7f0eb;
  --muted: #8fae9f;
  --accent: #34d399;
  --danger: #f87171;
  --warn: #fbbf24;
}
body { background: var(--bg); color: var(--text); }
```

- [ ] **Step 5: Vitest config `frontend/vitest.config.ts`**

```ts
import react from "@vitejs/plugin-react";
import { defineConfig } from "vitest/config";

export default defineConfig({
  plugins: [react()],
  test: { environment: "jsdom", globals: true, setupFiles: ["./vitest.setup.ts"] },
  resolve: { alias: { "@": new URL("./src", import.meta.url).pathname } },
});
```
And `frontend/vitest.setup.ts`:
```ts
import "@testing-library/jest-dom/vitest";
```
Add to `package.json` scripts: `"test": "vitest run"`.

- [ ] **Step 6: Smoke test `src/lib/smoke.test.ts`**

```ts
import { describe, expect, it } from "vitest";

describe("smoke", () => {
  it("runs", () => {
    expect(1 + 1).toBe(2);
  });
});
```

- [ ] **Step 7: Verify build + test + typecheck**

```bash
cd frontend
npm run test
npx tsc --noEmit
npx next build
```
Expected: test passes, tsc clean, build succeeds.

- [ ] **Step 8: Review + commit**

```bash
git add frontend/ .gitignore
git write-tree > .git/canopy-review-marker
git commit -m "feat(frontend): scaffold next.js + tailwind + backend proxy + vitest"
```
(create-next-app writes `frontend/.gitignore` for `node_modules`/`.next`; confirm they are ignored.)

---

### Task 2: Types + API client + query hooks

**Files:** create `src/lib/types.ts`, `src/lib/api.ts`, `src/lib/queries.ts`, `src/providers.tsx`; modify `src/app/layout.tsx`. Test: `src/lib/api.test.ts`.

**Interfaces:**
- Produces types mirroring the backend: `ProjectSummary`, `ProjectDetail`, `Imagery`/`ImageLayer`, `Observation`, `Metric`, `Risk`, `Evidence`, `AskResponse`, `Report`.
- Produces `api` object: `listProjects()`, `getProject(id)`, `getBoundary(id)`, `getImagery(id)`, `getObservations(id)`, `getMetrics(id)`, `getRisk(id)`, `getEvidence(id)`, `ask(id, body)`, `createReport(id, body)`, `getReport(id)`.
- Produces query hooks: `useProjects()`, `useProject(id)`, `useBoundary(id)`, `useImagery(id)`, `useMetrics(id)`, `useRisk(id)`, `useEvidence(id)`, `useObservations(id)`.

- [ ] **Step 1: `src/lib/types.ts`**

```ts
export interface ProjectSummary {
  id: string; name: string; asset_type: string;
  country: string | null; financing_type: string | null;
  status: string; risk_score: number | null; risk_band: string | null;
}
export interface ProjectDetail extends ProjectSummary {
  monitoring_objective: string | null; screening_status: string | null;
  confidence: number | null; main_finding: string | null;
}
export interface ImageLayer { key: string; label: string; url: string; kind: "rgb" | "overlay"; date: string | null; }
export interface Imagery { project_id: string; layers: ImageLayer[]; }
export interface Metric { id: string; metric_name: string; value: number | null; unit: string | null; baseline_value: number | null; comparison_value: number | null; method_id: string | null; }
export interface Observation { id: string; observation_type: string; period_start: string | null; period_end: string | null; summary: string; severity: string | null; confidence: number | null; metrics: Metric[]; }
export interface Risk { score_type: string; score_value: number | null; score_band: string | null; drivers_json: Record<string, number | null>; }
export interface Evidence { id: string; observation_id: string; source_name: string; source_date: string | null; method_id: string | null; confidence: string | null; limitations: string[]; financial_relevance: string | null; supporting_assets: string[]; }
export interface AskResponse { answer: string; evidence_used: string[]; confidence: string; limitations: string[]; unsupported_claims_refused: string[]; }
export interface Report { id: string; project_id: string; report_type: string; content: string | null; evidence_ids: string[]; generated_at: string; }
export type Boundary = { type: "Feature"; geometry: { type: string; coordinates: number[][][] }; properties: { project_id: string; area_hectares: number | null } };
```

- [ ] **Step 2: `src/lib/api.ts`**

```ts
import type {
  AskResponse, Boundary, Evidence, Imagery, Metric, Observation,
  ProjectDetail, ProjectSummary, Report, Risk,
} from "@/lib/types";

async function get<T>(path: string): Promise<T> {
  const res = await fetch(`/api${path}`);
  if (!res.ok) throw new Error(`GET ${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}
async function post<T>(path: string, body: unknown): Promise<T> {
  const res = await fetch(`/api${path}`, {
    method: "POST",
    headers: { "content-type": "application/json" },
    body: JSON.stringify(body),
  });
  if (!res.ok) throw new Error(`POST ${path} -> ${res.status}`);
  return res.json() as Promise<T>;
}

export const api = {
  listProjects: () => get<ProjectSummary[]>("/projects"),
  getProject: (id: string) => get<ProjectDetail>(`/projects/${id}`),
  getBoundary: (id: string) => get<Boundary>(`/projects/${id}/boundary`),
  getImagery: (id: string) => get<Imagery>(`/projects/${id}/imagery`),
  getObservations: (id: string) => get<Observation[]>(`/projects/${id}/observations`),
  getMetrics: (id: string) => get<Metric[]>(`/projects/${id}/metrics`),
  getRisk: (id: string) => get<Risk>(`/projects/${id}/risk`),
  getEvidence: (id: string) => get<Evidence[]>(`/projects/${id}/evidence`),
  ask: (id: string, body: { question: string; allowed_evidence_ids?: string[] }) =>
    post<AskResponse>(`/projects/${id}/ask`, body),
  createReport: (id: string, body: { report_type?: string }) =>
    post<Report>(`/projects/${id}/reports`, body),
  getReport: (reportId: string) => get<Report>(`/reports/${reportId}`),
};
```

- [ ] **Step 3: Write the failing test `src/lib/api.test.ts`**

```ts
import { afterEach, describe, expect, it, vi } from "vitest";
import { api } from "@/lib/api";

afterEach(() => vi.restoreAllMocks());

describe("api client", () => {
  it("GET /projects hits the same-origin proxy and returns JSON", async () => {
    const fetchMock = vi.fn().mockResolvedValue(
      new Response(JSON.stringify([{ id: "p1" }]), { status: 200 }),
    );
    vi.stubGlobal("fetch", fetchMock);
    const out = await api.listProjects();
    expect(fetchMock).toHaveBeenCalledWith("/api/projects");
    expect(out[0].id).toBe("p1");
  });

  it("throws on non-ok responses", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response("nope", { status: 500 })));
    await expect(api.listProjects()).rejects.toThrow("500");
  });

  it("POST /ask sends a JSON body", async () => {
    const fetchMock = vi.fn().mockResolvedValue(new Response(JSON.stringify({ answer: "x" }), { status: 200 }));
    vi.stubGlobal("fetch", fetchMock);
    await api.ask("p1", { question: "q" });
    const [, init] = fetchMock.mock.calls[0];
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body).question).toBe("q");
  });
});
```

- [ ] **Step 4: Run it and confirm it fails, then passes** (the client already exists from Step 2, so it should pass immediately)

Run: `cd frontend && npm run test -- api`
Expected: 3 pass.

- [ ] **Step 5: `src/providers.tsx`**

```tsx
"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  const [client] = useState(() => new QueryClient());
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>;
}
```

- [ ] **Step 6: `src/lib/queries.ts`**

```ts
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";

export const useProjects = () => useQuery({ queryKey: ["projects"], queryFn: api.listProjects });
export const useProject = (id: string) => useQuery({ queryKey: ["project", id], queryFn: () => api.getProject(id) });
export const useBoundary = (id: string) => useQuery({ queryKey: ["boundary", id], queryFn: () => api.getBoundary(id) });
export const useImagery = (id: string) => useQuery({ queryKey: ["imagery", id], queryFn: () => api.getImagery(id) });
export const useObservations = (id: string) => useQuery({ queryKey: ["observations", id], queryFn: () => api.getObservations(id) });
export const useMetrics = (id: string) => useQuery({ queryKey: ["metrics", id], queryFn: () => api.getMetrics(id) });
export const useRisk = (id: string) => useQuery({ queryKey: ["risk", id], queryFn: () => api.getRisk(id) });
export const useEvidence = (id: string) => useQuery({ queryKey: ["evidence", id], queryFn: () => api.getEvidence(id) });
```

- [ ] **Step 7: Wrap the app in providers (`src/app/layout.tsx`)**

Wrap `{children}` in `<Providers>` (import from `@/providers`). Keep the existing `<html>`/`<body>` structure.

- [ ] **Step 8: Commit**

```bash
git add frontend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(frontend): typed api client, types, and query hooks"
```

---

### Task 3: Portfolio / Project Selector (screen 1)

**Files:** create `src/components/ui/{Card,Badge}.tsx`, `src/components/features/ProjectCard.tsx`; replace `src/app/page.tsx`. Test: `src/components/features/ProjectCard.test.tsx`.

**Interfaces:**
- Produces: `Badge({ tone, children })` (tones: `neutral | low | medium | high`); `Card`; `ProjectCard({ project })` linking to `/projects/{id}`; the home page renders `useProjects()` as a grid.

- [ ] **Step 1: `src/components/ui/Badge.tsx`**

```tsx
const TONES: Record<string, string> = {
  neutral: "bg-emerald-900/40 text-emerald-200",
  low: "bg-emerald-800/50 text-emerald-100",
  medium: "bg-amber-800/50 text-amber-100",
  high: "bg-red-900/50 text-red-100",
};
export function Badge({ tone = "neutral", children }: { tone?: string; children: React.ReactNode }) {
  return <span className={`rounded px-2 py-0.5 text-xs font-medium ${TONES[tone] ?? TONES.neutral}`}>{children}</span>;
}
export const bandTone = (band: string | null) =>
  band === "High" || band === "Critical" ? "high" : band === "Medium" ? "medium" : "low";
```

- [ ] **Step 2: `src/components/ui/Card.tsx`**

```tsx
export function Card({ children, className = "" }: { children: React.ReactNode; className?: string }) {
  return <div className={`rounded-lg border border-[var(--border)] bg-[var(--panel)] p-4 ${className}`}>{children}</div>;
}
```

- [ ] **Step 3: `src/components/features/ProjectCard.tsx`**

```tsx
import Link from "next/link";
import { Badge, bandTone } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import type { ProjectSummary } from "@/lib/types";

export function ProjectCard({ project }: { project: ProjectSummary }) {
  return (
    <Link href={`/projects/${project.id}`}>
      <Card className="transition hover:border-[var(--accent)]">
        <div className="flex items-start justify-between gap-2">
          <h3 className="font-semibold">{project.name}</h3>
          {project.risk_band && <Badge tone={bandTone(project.risk_band)}>{project.risk_band}</Badge>}
        </div>
        <p className="mt-1 text-sm text-[var(--muted)]">
          {project.asset_type}{project.country ? ` · ${project.country}` : ""}
        </p>
        <div className="mt-3 flex items-center justify-between text-xs text-[var(--muted)]">
          <span>{project.financing_type ?? "—"}</span>
          <span>risk {project.risk_score ?? "—"}</span>
        </div>
      </Card>
    </Link>
  );
}
```

- [ ] **Step 4: Write the failing test `src/components/features/ProjectCard.test.tsx`**

```tsx
import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";
import { ProjectCard } from "@/components/features/ProjectCard";

describe("ProjectCard", () => {
  it("renders name, type, risk band and links to the project", () => {
    render(
      <ProjectCard project={{
        id: "solar1", name: "Nur Navoi Solar", asset_type: "solar", country: "Uzbekistan",
        financing_type: "development_finance", status: "monitored", risk_score: 61, risk_band: "High",
      }} />,
    );
    expect(screen.getByText("Nur Navoi Solar")).toBeInTheDocument();
    expect(screen.getByText("High")).toBeInTheDocument();
    expect(screen.getByRole("link")).toHaveAttribute("href", "/projects/solar1");
  });
});
```

- [ ] **Step 5: Run test → pass**

Run: `cd frontend && npm run test -- ProjectCard`
Expected: PASS.

- [ ] **Step 6: Replace `src/app/page.tsx`**

```tsx
"use client";
import { ProjectCard } from "@/components/features/ProjectCard";
import { useProjects } from "@/lib/queries";

export default function Home() {
  const { data, isLoading, isError } = useProjects();
  return (
    <main className="mx-auto max-w-5xl p-8">
      <h1 className="text-2xl font-bold">Canopy — Monitored Projects</h1>
      <p className="mt-1 text-sm text-[var(--muted)]">Green-finance evidence for tracked assets.</p>
      {isLoading && <p className="mt-8 text-[var(--muted)]">Loading…</p>}
      {isError && <p className="mt-8 text-[var(--danger)]">Could not reach the API. Is the backend running on :8001?</p>}
      <div className="mt-6 grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {data?.map((p) => <ProjectCard key={p.id} project={p} />)}
      </div>
    </main>
  );
}
```

- [ ] **Step 7: Verify in the browser** (backend must be up + seeded)

```bash
cd frontend && npm run dev   # http://localhost:3000
```
Confirm the project grid renders `Nur Navoi Solar` with a `High` badge; clicking navigates to `/projects/nur_navoi_solar` (404 page for now — next tasks fill it).

- [ ] **Step 8: Commit**

```bash
git add frontend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(frontend): portfolio/project selector screen"
```

---

### Task 4: Project shell + Overview metadata (screen 2, no map yet)

**Files:** create `src/components/features/SectionNav.tsx`, `src/app/projects/[id]/layout.tsx`, `src/app/projects/[id]/page.tsx`.

**Interfaces:**
- Produces: `SectionNav({ id })` linking to Overview / Timeline / Metrics / Ask / Memo; project `layout` renders a header (name, status, risk badge) + `SectionNav`; Overview `page` shows metadata, financing/monitoring context, `main_finding`, and a data-source summary.

- [ ] **Step 1: `src/components/features/SectionNav.tsx`**

```tsx
"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";

const SECTIONS = [
  { slug: "", label: "Overview" },
  { slug: "timeline", label: "Evidence Timeline" },
  { slug: "metrics", label: "Metrics" },
  { slug: "ask", label: "Ask Canopy" },
  { slug: "memo", label: "Memo" },
];

export function SectionNav({ id }: { id: string }) {
  const path = usePathname();
  return (
    <nav className="flex gap-1 border-b border-[var(--border)]">
      {SECTIONS.map((s) => {
        const href = `/projects/${id}${s.slug ? `/${s.slug}` : ""}`;
        const active = path === href;
        return (
          <Link key={s.slug} href={href}
            className={`px-3 py-2 text-sm ${active ? "border-b-2 border-[var(--accent)] text-[var(--text)]" : "text-[var(--muted)]"}`}>
            {s.label}
          </Link>
        );
      })}
    </nav>
  );
}
```

- [ ] **Step 2: `src/app/projects/[id]/layout.tsx`**

```tsx
import { SectionNav } from "@/components/features/SectionNav";
import Link from "next/link";

export default async function ProjectLayout({
  children, params,
}: { children: React.ReactNode; params: Promise<{ id: string }> }) {
  const { id } = await params;
  return (
    <div className="mx-auto max-w-5xl p-8">
      <Link href="/" className="text-sm text-[var(--muted)]">← All projects</Link>
      <div className="mt-2"><SectionNav id={id} /></div>
      <div className="mt-6">{children}</div>
    </div>
  );
}
```

- [ ] **Step 3: `src/app/projects/[id]/page.tsx`** (Overview)

```tsx
"use client";
import { use } from "react";
import { Badge, bandTone } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { useProject } from "@/lib/queries";

export default function Overview({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: p, isLoading } = useProject(id);
  if (isLoading || !p) return <p className="text-[var(--muted)]">Loading…</p>;
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-bold">{p.name}</h1>
          <p className="text-sm text-[var(--muted)]">{p.asset_type} · {p.country ?? "—"} · {p.financing_type ?? "—"}</p>
        </div>
        {p.risk_band && <Badge tone={bandTone(p.risk_band)}>Risk {p.risk_score} · {p.risk_band}</Badge>}
      </div>
      <Card>
        <h2 className="text-sm font-semibold text-[var(--muted)]">Main finding</h2>
        <p className="mt-1">{p.main_finding ?? "—"}</p>
      </Card>
      <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        <Card>
          <h2 className="text-sm font-semibold text-[var(--muted)]">Monitoring objective</h2>
          <p className="mt-1 text-sm">{p.monitoring_objective ?? "—"}</p>
        </Card>
        <Card>
          <h2 className="text-sm font-semibold text-[var(--muted)]">Screening</h2>
          <p className="mt-1 text-sm">{p.screening_status ?? "—"} (confidence {p.confidence ?? "—"})</p>
          <p className="mt-2 text-xs text-[var(--muted)]">Sources: Sentinel-2, Sentinel-1 · monitoring, not certification.</p>
        </Card>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: Verify** — `/projects/nur_navoi_solar` shows the header, risk badge, main finding, monitoring objective, and screening card. `tsc --noEmit` clean.

- [ ] **Step 5: Commit**

```bash
git add frontend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(frontend): project shell + overview metadata"
```

---

### Task 5: EvidenceMap (MapLibre, no tiles) + boundary on Overview

**Files:** create `src/lib/geo.ts`, `src/components/map/EvidenceMap.tsx`; modify Overview to render the boundary map. Test: `src/lib/geo.test.ts`.

**Interfaces:**
- Produces: `bbox(coords: number[][][]) -> [minLng, minLat, maxLng, maxLat]`; `imageCoords(bbox) -> [[lng,lat]×4]` (TL,TR,BR,BL for a MapLibre image source); `EvidenceMap({ boundary, images })` where `images: MapImage[]` (`{ id, url, opacity }`) are drawn georeferenced to the boundary bbox — layers reconciled in place (opacity via `setPaintProperty` for a smooth swipe), boundary outline on top, **no base tiles**.

- [ ] **Step 1: `src/lib/geo.ts`**

```ts
export type BBox = [number, number, number, number];

export function bbox(coords: number[][][]): BBox {
  const ring = coords[0];
  let minLng = Infinity, minLat = Infinity, maxLng = -Infinity, maxLat = -Infinity;
  for (const [lng, lat] of ring) {
    minLng = Math.min(minLng, lng); maxLng = Math.max(maxLng, lng);
    minLat = Math.min(minLat, lat); maxLat = Math.max(maxLat, lat);
  }
  return [minLng, minLat, maxLng, maxLat];
}

export function imageCoords([minLng, minLat, maxLng, maxLat]: BBox): [number, number][] {
  // MapLibre image source order: top-left, top-right, bottom-right, bottom-left
  return [[minLng, maxLat], [maxLng, maxLat], [maxLng, minLat], [minLng, minLat]];
}
```

- [ ] **Step 2: `src/lib/geo.test.ts`**

```ts
import { describe, expect, it } from "vitest";
import { bbox, imageCoords } from "@/lib/geo";

describe("geo", () => {
  it("computes bbox from a ring", () => {
    expect(bbox([[[0, 0], [2, 0], [2, 3], [0, 3], [0, 0]]])).toEqual([0, 0, 2, 3]);
  });
  it("orders image corners TL,TR,BR,BL", () => {
    expect(imageCoords([0, 0, 2, 3])).toEqual([[0, 3], [2, 3], [2, 0], [0, 0]]);
  });
});
```

- [ ] **Step 3: Run → pass.** `cd frontend && npm run test -- geo`

- [ ] **Step 4: `src/components/map/EvidenceMap.tsx`**

```tsx
"use client";
import "maplibre-gl/dist/maplibre-gl.css";
import maplibregl, { type Map as MlMap, type StyleSpecification } from "maplibre-gl";
import { useEffect, useRef } from "react";
import { bbox, imageCoords } from "@/lib/geo";
import type { Boundary } from "@/lib/types";

export interface MapImage { id: string; url: string; opacity: number; }

const EMPTY_STYLE: StyleSpecification = {
  version: 8,
  sources: {},
  layers: [{ id: "bg", type: "background", paint: { "background-color": "#0b1512" } }],
};

// Reconcile image layers in place: update opacity for existing ones (smooth swipe),
// add/remove only when the set changes. Never recreates the map.
function sync(map: MlMap, boundary: Boundary, images: MapImage[], active: Set<string>) {
  const corners = imageCoords(bbox(boundary.geometry.coordinates as number[][][]));
  const wanted = new Set(images.map((i) => i.id));
  for (const id of Array.from(active)) {
    if (!wanted.has(id)) {
      if (map.getLayer(id)) map.removeLayer(id);
      if (map.getSource(id)) map.removeSource(id);
      active.delete(id);
    }
  }
  for (const img of images) {
    if (active.has(img.id)) {
      map.setPaintProperty(img.id, "raster-opacity", img.opacity);
    } else {
      map.addSource(img.id, { type: "image", url: img.url, coordinates: corners });
      map.addLayer(
        { id: img.id, type: "raster", source: img.id, paint: { "raster-opacity": img.opacity } },
        "boundary-line",
      );
      active.add(img.id);
    }
  }
}

export function EvidenceMap({ boundary, images = [] }: { boundary: Boundary; images?: MapImage[] }) {
  const ref = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MlMap | null>(null);
  const loadedRef = useRef(false);
  const imagesRef = useRef<MapImage[]>(images);
  const activeRef = useRef<Set<string>>(new Set());

  // Create the map once per boundary; draw the outline.
  useEffect(() => {
    if (!ref.current) return;
    const box = bbox(boundary.geometry.coordinates as number[][][]);
    const map = new maplibregl.Map({
      container: ref.current, style: EMPTY_STYLE,
      bounds: [box[0], box[1], box[2], box[3]], fitBoundsOptions: { padding: 40 },
    });
    mapRef.current = map;
    loadedRef.current = false;
    activeRef.current = new Set();
    map.on("load", () => {
      map.addSource("boundary", { type: "geojson", data: boundary });
      map.addLayer({ id: "boundary-line", type: "line", source: "boundary",
        paint: { "line-color": "#34d399", "line-width": 2 } });
      loadedRef.current = true;
      sync(map, boundary, imagesRef.current, activeRef.current);
    });
    return () => { map.remove(); mapRef.current = null; loadedRef.current = false; };
  }, [boundary]);

  // Reconcile whenever images change (opacity updates in place -> smooth swipe).
  useEffect(() => {
    imagesRef.current = images;
    if (mapRef.current && loadedRef.current) sync(mapRef.current, boundary, images, activeRef.current);
  }, [images, boundary]);

  return <div ref={ref} className="h-80 w-full rounded-lg border border-[var(--border)]" />;
}
```

- [ ] **Step 5: Render the map on Overview**

In `src/app/projects/[id]/page.tsx`, add `useBoundary`/`useImagery`, pick the RGB layer, and render:
```tsx
// imports
import { EvidenceMap } from "@/components/map/EvidenceMap";
import { useBoundary, useImagery } from "@/lib/queries";
// inside component, after useProject:
const { data: boundary } = useBoundary(id);
const { data: imagery } = useImagery(id);
const rgb = imagery?.layers.find((l) => l.kind === "rgb");
// in JSX, above the Main finding card:
{boundary && (
  <EvidenceMap boundary={boundary} images={rgb ? [{ id: "rgb", url: rgb.url, opacity: 1 }] : []} />
)}
```

- [ ] **Step 6: Verify in browser** — Overview shows the map: the AOI RGB placeholder filling the boundary box with a green outline, no base tiles, no network calls to any tile host (check the Network tab: only `/api/*` and `/static/*` on localhost).

- [ ] **Step 7: Commit**

```bash
git add frontend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(frontend): maplibre evidence map (no tiles) + boundary on overview"
```

---

### Task 6: Evidence Timeline (screen 3)

**Files:** create `src/stores/ui.ts`, `src/app/projects/[id]/timeline/page.tsx`.

**Interfaces:**
- Consumes: `EvidenceMap`, `useBoundary`, `useImagery`, `useObservations`.
- Produces: a page with a before/after opacity slider (Zustand `swipe`), overlay toggles, observation summaries as markers/labels, and source labels.

- [ ] **Step 1: `src/stores/ui.ts`**

```ts
import { create } from "zustand";

interface UiState {
  swipe: number; setSwipe: (v: number) => void;
  overlays: Record<string, boolean>; toggleOverlay: (key: string) => void;
}
export const useUi = create<UiState>((set) => ({
  swipe: 0.5,
  setSwipe: (v) => set({ swipe: v }),
  overlays: {},
  toggleOverlay: (key) => set((s) => ({ overlays: { ...s.overlays, [key]: !s.overlays[key] } })),
}));
```

- [ ] **Step 2: `src/app/projects/[id]/timeline/page.tsx`**

```tsx
"use client";
import { use, useMemo } from "react";
import { EvidenceMap, type MapImage } from "@/components/map/EvidenceMap";
import { Card } from "@/components/ui/Card";
import { useBoundary, useImagery, useObservations } from "@/lib/queries";
import { useUi } from "@/stores/ui";

export default function Timeline({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: boundary } = useBoundary(id);
  const { data: imagery } = useImagery(id);
  const { data: observations } = useObservations(id);
  const { swipe, setSwipe, overlays, toggleOverlay } = useUi();

  if (!boundary || !imagery) return <p className="text-[var(--muted)]">Loading…</p>;
  const before = imagery.layers.find((l) => l.key.includes("before"));
  const after = imagery.layers.find((l) => l.key.includes("after"));
  const overlayLayers = imagery.layers.filter((l) => l.kind === "overlay");

  const images = useMemo<MapImage[]>(() => [
    ...(before ? [{ id: "before", url: before.url, opacity: 1 - swipe }] : []),
    ...(after ? [{ id: "after", url: after.url, opacity: swipe }] : []),
    ...overlayLayers.filter((l) => overlays[l.key]).map((l) => ({ id: l.key, url: l.url, opacity: 0.7 })),
  ], [before, after, overlayLayers, overlays, swipe]);

  return (
    <div className="space-y-4">
      <EvidenceMap boundary={boundary} images={images} />
      <div className="flex items-center gap-3">
        <span className="text-xs text-[var(--muted)]">Before</span>
        <input type="range" min={0} max={1} step={0.01} value={swipe}
          onChange={(e) => setSwipe(Number(e.target.value))} className="flex-1" />
        <span className="text-xs text-[var(--muted)]">After</span>
      </div>
      <div className="flex flex-wrap gap-2">
        {overlayLayers.map((l) => (
          <button key={l.key} onClick={() => toggleOverlay(l.key)}
            className={`rounded border px-2 py-1 text-xs ${overlays[l.key] ? "border-[var(--accent)] text-[var(--text)]" : "border-[var(--border)] text-[var(--muted)]"}`}>
            {l.label}
          </button>
        ))}
      </div>
      <div className="space-y-2">
        {observations?.map((o) => (
          <Card key={o.id}>
            <p className="text-sm">{o.summary}</p>
            <p className="mt-1 text-xs text-[var(--muted)]">
              {o.observation_type} · {o.period_start} → {o.period_end}
            </p>
          </Card>
        ))}
      </div>
    </div>
  );
}
```

- [ ] **Step 3: Verify in browser** — the slider cross-fades before/after; overlay toggles add/remove the change layer; observation summaries list below with periods.

- [ ] **Step 4: Commit**

```bash
git add frontend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(frontend): evidence timeline with before/after swipe + overlays"
```

---

### Task 7: Metrics Dashboard (screen 4) + Evidence Drawer (screen 5)

**Files:** create `src/components/ui/Stat.tsx`, `src/components/features/EvidenceCard.tsx`, `src/components/features/EvidenceDrawer.tsx`, `src/app/projects/[id]/metrics/page.tsx`.

**Interfaces:**
- Produces: `Stat({ label, value, sub })`; `EvidenceCard({ evidence })` showing source/method/date/confidence/limitations; `EvidenceDrawer({ id, open, onClose })` (slide-over listing `useEvidence`); metrics page with `useMetrics` + `useRisk` tiles and a button opening the drawer.

- [ ] **Step 1: `src/components/ui/Stat.tsx`**

```tsx
import { Card } from "@/components/ui/Card";
export function Stat({ label, value, sub }: { label: string; value: React.ReactNode; sub?: string }) {
  return (
    <Card>
      <p className="text-xs text-[var(--muted)]">{label}</p>
      <p className="mt-1 text-2xl font-semibold">{value}</p>
      {sub && <p className="mt-1 text-xs text-[var(--muted)]">{sub}</p>}
    </Card>
  );
}
```

- [ ] **Step 2: `src/components/features/EvidenceCard.tsx`**

```tsx
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import type { Evidence } from "@/lib/types";

const confTone = (c: string | null) => (c === "high" ? "low" : c === "low" ? "high" : "medium");

export function EvidenceCard({ evidence }: { evidence: Evidence }) {
  return (
    <Card>
      <div className="flex items-center justify-between">
        <span className="font-mono text-xs text-[var(--muted)]">{evidence.id}</span>
        {evidence.confidence && <Badge tone={confTone(evidence.confidence)}>{evidence.confidence}</Badge>}
      </div>
      <p className="mt-2 text-sm">Source: {evidence.source_name} · Method: {evidence.method_id ?? "—"}</p>
      {evidence.financial_relevance && (
        <p className="mt-1 text-sm text-[var(--muted)]">{evidence.financial_relevance}</p>
      )}
      {evidence.limitations.length > 0 && (
        <ul className="mt-2 list-disc pl-4 text-xs text-[var(--muted)]">
          {evidence.limitations.map((l, i) => <li key={i}>{l}</li>)}
        </ul>
      )}
    </Card>
  );
}
```

- [ ] **Step 3: `src/components/features/EvidenceDrawer.tsx`**

```tsx
"use client";
import { EvidenceCard } from "@/components/features/EvidenceCard";
import { useEvidence } from "@/lib/queries";

export function EvidenceDrawer({ id, open, onClose }: { id: string; open: boolean; onClose: () => void }) {
  const { data } = useEvidence(id);
  if (!open) return null;
  return (
    <div className="fixed inset-0 z-20 flex justify-end bg-black/50" onClick={onClose}>
      <div className="h-full w-full max-w-md overflow-y-auto bg-[var(--bg)] p-4" onClick={(e) => e.stopPropagation()}>
        <div className="flex items-center justify-between">
          <h2 className="font-semibold">Evidence</h2>
          <button onClick={onClose} className="text-[var(--muted)]">✕</button>
        </div>
        <div className="mt-4 space-y-3">
          {data?.map((e) => <EvidenceCard key={e.id} evidence={e} />)}
        </div>
      </div>
    </div>
  );
}
```

- [ ] **Step 4: `src/app/projects/[id]/metrics/page.tsx`**

```tsx
"use client";
import { use, useState } from "react";
import { EvidenceDrawer } from "@/components/features/EvidenceDrawer";
import { Stat } from "@/components/ui/Stat";
import { useMetrics, useRisk } from "@/lib/queries";

export default function Metrics({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const { data: metrics } = useMetrics(id);
  const { data: risk } = useRisk(id);
  const [open, setOpen] = useState(false);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Metrics</h1>
        <button onClick={() => setOpen(true)}
          className="rounded border border-[var(--accent)] px-3 py-1 text-sm text-[var(--accent)]">
          View evidence
        </button>
      </div>
      <div className="grid grid-cols-2 gap-4 md:grid-cols-4">
        {risk && <Stat label="Risk score" value={risk.score_value ?? "—"} sub={risk.score_band ?? undefined} />}
        {risk && <Stat label="Flood driver" value={risk.drivers_json.flood ?? "—"} />}
        {risk && <Stat label="Fire driver" value={risk.drivers_json.fire ?? "—"} />}
        {metrics?.map((m) => (
          <Stat key={m.id} label={m.metric_name} value={m.value ?? "—"} sub={m.method_id ?? undefined} />
        ))}
      </div>
      <p className="text-xs text-[var(--muted)]">
        Explanatory monitoring metrics — proxies, not certification. Open evidence for source, method, and limitations.
      </p>
      <EvidenceDrawer id={id} open={open} onClose={() => setOpen(false)} />
    </div>
  );
}
```

- [ ] **Step 5: Verify** — tiles show risk 61/High, flood 61, fire 22, vegetation_change_percent 34.1; "View evidence" opens the drawer with the land-cover evidence card (source, method `build_v1`, 3 limitations).

- [ ] **Step 6: Commit**

```bash
git add frontend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(frontend): metrics dashboard + evidence drawer"
```

---

### Task 8: Ask Canopy (screen 6) + Generate Memo (screen 7)

**Files:** create `src/components/features/AskPanel.tsx`, `src/components/features/MemoView.tsx`, `src/app/projects/[id]/ask/page.tsx`, `src/app/projects/[id]/memo/page.tsx`.

**Interfaces:**
- Produces: `AskPanel({ id })` using a `useMutation` over `api.ask`, rendering the answer, cited evidence IDs, confidence, limitations, and any refusals; `MemoView({ content })` rendering the memo text; memo page uses `useMutation` over `api.createReport`.

- [ ] **Step 1: `src/components/features/AskPanel.tsx`**

```tsx
"use client";
import { useMutation } from "@tanstack/react-query";
import { useState } from "react";
import { Badge } from "@/components/ui/Badge";
import { Card } from "@/components/ui/Card";
import { api } from "@/lib/api";

export function AskPanel({ id }: { id: string }) {
  const [q, setQ] = useState("");
  const m = useMutation({ mutationFn: (question: string) => api.ask(id, { question }) });
  return (
    <div className="space-y-4">
      <form onSubmit={(e) => { e.preventDefault(); if (q.trim()) m.mutate(q); }} className="flex gap-2">
        <input value={q} onChange={(e) => setQ(e.target.value)} placeholder="Ask about this project's evidence…"
          className="flex-1 rounded border border-[var(--border)] bg-[var(--panel)] px-3 py-2 text-sm" />
        <button className="rounded bg-[var(--accent)] px-4 py-2 text-sm font-medium text-black" disabled={m.isPending}>
          {m.isPending ? "…" : "Ask"}
        </button>
      </form>
      {m.isError && <p className="text-sm text-[var(--danger)]">Ask failed. Is an LLM key configured on the backend?</p>}
      {m.data && (
        <Card>
          <p className="whitespace-pre-wrap">{m.data.answer}</p>
          <div className="mt-3 flex flex-wrap items-center gap-2">
            <Badge>confidence: {m.data.confidence}</Badge>
            {m.data.evidence_used.map((e) => <span key={e} className="font-mono text-xs text-[var(--muted)]">[{e}]</span>)}
          </div>
          {m.data.limitations.length > 0 && (
            <ul className="mt-2 list-disc pl-4 text-xs text-[var(--muted)]">
              {m.data.limitations.map((l, i) => <li key={i}>{l}</li>)}
            </ul>
          )}
          {m.data.unsupported_claims_refused.length > 0 && (
            <p className="mt-2 text-xs text-[var(--warn)]">Refused (unsupported): {m.data.unsupported_claims_refused.join("; ")}</p>
          )}
        </Card>
      )}
    </div>
  );
}
```

- [ ] **Step 2: `src/app/projects/[id]/ask/page.tsx`**

```tsx
"use client";
import { use } from "react";
import { AskPanel } from "@/components/features/AskPanel";

export default function Ask({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  return (
    <div className="space-y-3">
      <h1 className="text-xl font-bold">Ask Canopy</h1>
      <p className="text-sm text-[var(--muted)]">Answers are bounded to this project's stored evidence and cite the evidence used.</p>
      <AskPanel id={id} />
    </div>
  );
}
```

- [ ] **Step 3: `src/components/features/MemoView.tsx`**

```tsx
export function MemoView({ content }: { content: string }) {
  return (
    <pre className="whitespace-pre-wrap rounded-lg border border-[var(--border)] bg-[var(--panel)] p-4 text-sm">
      {content}
    </pre>
  );
}
```

- [ ] **Step 4: `src/app/projects/[id]/memo/page.tsx`**

```tsx
"use client";
import { useMutation } from "@tanstack/react-query";
import { use } from "react";
import { MemoView } from "@/components/features/MemoView";
import { api } from "@/lib/api";

export default function Memo({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  const m = useMutation({ mutationFn: () => api.createReport(id, {}) });
  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <h1 className="text-xl font-bold">Monitoring Memo</h1>
        <button onClick={() => m.mutate()} disabled={m.isPending}
          className="rounded bg-[var(--accent)] px-4 py-2 text-sm font-medium text-black">
          {m.isPending ? "Generating…" : "Generate memo"}
        </button>
      </div>
      {m.isError && <p className="text-sm text-[var(--danger)]">Memo generation failed. Is an LLM key configured on the backend?</p>}
      {m.data?.content && <MemoView content={m.data.content} />}
      {m.data && <p className="text-xs text-[var(--muted)]">Report {m.data.id} · evidence: {m.data.evidence_ids.join(", ") || "—"}</p>}
    </div>
  );
}
```

- [ ] **Step 5: Verify** — requires an LLM key in `backend/.env`. With a key: Ask returns a cited answer; Generate memo renders the Appendix-B memo. Without a key: the buttons show the friendly "Is an LLM key configured?" error (graceful — the rest of the app is unaffected).

- [ ] **Step 6: Commit**

```bash
git add frontend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(frontend): ask canopy chat + generate memo screens"
```

---

### Task 9: Polish, states, and end-to-end walkthrough

**Files:** modify `src/app/layout.tsx` (metadata/title), add shared `Loading`/`Error` treatment, and a not-found for unknown projects.

- [ ] **Step 1: App title + shell** — set `metadata.title = "Canopy"` in `layout.tsx`; ensure the body uses the theme background.
- [ ] **Step 2: Loading + error consistency** — confirm each screen shows a muted "Loading…" and, on API failure, a readable message (not a blank page). Add a `src/app/projects/[id]/not-found.tsx` for unknown ids.
- [ ] **Step 3: Full walkthrough (backend up + seeded)** — with `npm run dev`, click through: selector → overview (map) → timeline (swipe) → metrics (evidence drawer) → ask → memo. Confirm the **Network tab shows only same-origin `/api/*` and `/static/*`** — no CDN or tile hosts.
- [ ] **Step 4: Gate** — `cd frontend && npx eslint . && npx tsc --noEmit && npm run test`; all clean/green.
- [ ] **Step 5: Commit**

```bash
git add frontend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(frontend): polish, loading/error states, and not-found"
```

---

## Self-Review

**Spec coverage (spec §9 — 7 screens + mapping):**
- (1) Portfolio/Project Selector → Task 3. ✅
- (2) Project Overview (boundary map + metadata + data-source summary) → Tasks 4–5. ✅
- (3) Evidence Timeline (before/after swipe, overlay toggles, observation markers, source labels) → Task 6. ✅
- (4) Metrics Dashboard → Task 7. ✅
- (5) Evidence Drawer (source/method/date/confidence/limitations) → Task 7. ✅
- (6) Ask Canopy (cited answers, refusals) → Task 8. ✅
- (7) Generate Memo → Task 8. ✅
- Mapping = MapLibre, **no base tiles**, georeferenced images + GeoJSON boundary → Task 5, constraint honored across 5/6. ✅
- No CDN assets; same-origin proxy; React Query + Zustand → Global Constraints + Tasks 1–2. ✅

**Placeholder scan:** no TBD/TODO; every step has complete code. Frontend visual screens use explicit browser-verification steps (unavoidable for UI); pure logic (api client, geo) is unit-tested. ✅

**Type consistency:** `api.*` return types match `types.ts`; query hooks wrap the same `api` calls; `EvidenceMap({ boundary, images })`, `Stat`, `Badge(tone)`, `bandTone`, `bbox`/`imageCoords` signatures are used consistently across tasks. `params: Promise<{id}>` (Next 15 async params) unwrapped with `use()` in client pages / `await` in server layout. ✅

**Notes / dependencies:** the Ask + Memo screens need an LLM key in `backend/.env` to return live content; without one they degrade to a clear error and the other five screens work fully. The imagery is placeholder solid-colour PNGs georeferenced to the AOI bbox until real pipeline rasters are dropped into `seed_data/assets/` (same filenames → no code change).
