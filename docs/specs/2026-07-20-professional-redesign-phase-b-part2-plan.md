# Professional Redesign — Phase B (Signature Components, part 2: AoiEvidenceLayer) Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build `AoiEvidenceLayer` — a Canvas-rendered "designed evidence layer" for the AOI (procedural asset-type terrain, measurement grid + corner ticks, the located boundary polygon, centroid marker, and an honest caption strip) — and swap it in for `EvidenceMap` on the **Locate** screen, in both themes.

**Architecture:** A tiny pure geometry/noise helper (`lib/aoiGeometry.ts`, unit-tested) provides the lon/lat→canvas projection, grid positions, path perimeter, and a deterministic value-noise function. A client component (`AoiEvidenceLayer`) draws the layers onto a single HiDPI `<canvas>`, animates the boundary draw-in on mount (reduced-motion aware), repaints on theme flip via a `data-theme` `MutationObserver` (the same token-resolve pattern `EvidenceMap` already uses), and renders the caption as an HTML overlay for crisp text + a11y. `EvidenceMap` is untouched and stays on the Timeline (Observe) screen, which does the real before/after raster swipe. Presentation-only; same data.

**Tech Stack:** Next.js 16, Tailwind v4 tokens, TypeScript, Vitest (jsdom), HTML5 Canvas 2D.

## Global Constraints

- **No data/behavior/API change.** Same `useProject`/`useBoundary`/`useDossier` payloads. The Locate screen's graceful-degradation (error → `DossierUnavailable`, loading → `CardSkeleton`) is preserved.
- **Locate only.** `AoiEvidenceLayer` replaces `EvidenceMap` on `/projects/[id]/locate` **only**. `EvidenceMap`, the Timeline (Observe) swipe, and the MapLibre dependency are **left untouched** — removing them is a deliberate Phase C call, not this plan.
- **Light + dark parity, AA-legible.** All canvas colors are resolved from tokens (`--c-map-bg`, `--c-accent`, `--color-border`, `--color-muted`) at draw time and repainted on every `data-theme` flip. Caption uses token utility classes only. The only hard-coded hex are module-level SSR/first-paint fallbacks (mirrors `EvidenceMap`'s `MAP_BG_FALLBACK`/`ACCENT_FALLBACK`).
- **Honor `prefers-reduced-motion`** — the boundary strokes in and the terrain/marker fade in on mount; under reduced-motion the final frame paints immediately with no animation.
- **Deterministic texture.** The terrain uses a seeded value-noise function — **no `Math.random`, no `Date.now`** — so output is stable across redraws, resizes, and SSR/hydration.
- **Asset-type aware.** `assetType === "mangrove"` → mottled canopy texture; anything else (`"solar"`) → regular panel-field banding. Seed values `mangrove: 71`, else `23`. (Seed assets: `nur_navoi_solar` → `"solar"`, `mikoko_pamoja` → `"mangrove"`.)
- **Honest caption.** Only fields that exist: AOI area (`boundary.properties.area_hectares`, omitted when null), centroid (`lat, lon` in Geist Mono), asset type label. **No fabricated source/date.**
- **Keep Geist** (numeric caption fields use `font-mono` = Geist Mono, `tabular-nums`).
- **Commit hygiene (Canopy pre-commit gate):** code commits (`.ts`/`.tsx`) are blocked by `.claude/hooks/pre-commit-review.sh` until the staged snapshot is reviewed. For each code task: run `/simplify` on the staged diff and apply cleanups, run `/code-review` and fix real findings, then `git write-tree > .git/canopy-review-marker`, then commit. **Always run `git add` and `git commit` as separate steps** (the compound `add && commit` slips past the gate). The docs-only commit in Task 0 passes freely.

**Run** (from `frontend/`): `npx tsc --noEmit` · `npx eslint` · `npx vitest run` · `npx next build`. Dev server on `:3000`, backend `:8001`. Current baseline: **7 test files, 21 tests** passing.

---

### Task 0: Commit this plan (docs-only)

**Files:**
- Create: `docs/specs/2026-07-20-professional-redesign-phase-b-part2-plan.md` (this file)

- [ ] **Step 1: Commit** (docs-only, passes the gate freely)

```bash
git add docs/specs/2026-07-20-professional-redesign-phase-b-part2-plan.md
git commit -m "docs: Phase B plan (part 2) — AoiEvidenceLayer"
```

---

### Task 1: AOI geometry + noise helper + tests

**Files:**
- Create: `frontend/src/lib/aoiGeometry.ts`
- Test: `frontend/src/lib/aoiGeometry.test.ts`

**Interfaces:**
- Consumes: `BBox` from `@/lib/geo`.
- Produces:
  - `Size = { w: number; h: number }`
  - `Point = [number, number]` (canvas px)
  - `Transform = { scale: number; ox: number; oy: number; box: BBox }`
  - `fitTransform(box: BBox, size: Size, pad: number): Transform` — uniform aspect-preserving fit of a lon/lat bbox into `(w,h)` with `pad` px inset, centered.
  - `toPx(lon: number, lat: number, t: Transform): Point` — project one lon/lat pair; latitude flipped (north = small y).
  - `projectRing(ring: number[][], t: Transform): Point[]` — project a GeoJSON `[lng,lat][]` ring.
  - `perimeter(points: Point[]): number` — total pixel path length (drives the stroke draw-in).
  - `gridLines(size: Size, step: number, pad: number): { xs: number[]; ys: number[] }` — interior grid line positions.
  - `terrainAt(x: number, y: number, seed: number): number` — deterministic value noise in `[0,1]`.

- [ ] **Step 1: Write the failing test** — `frontend/src/lib/aoiGeometry.test.ts`

```ts
import { describe, expect, it } from "vitest";
import {
  fitTransform,
  gridLines,
  perimeter,
  projectRing,
  terrainAt,
  toPx,
} from "@/lib/aoiGeometry";
import type { BBox } from "@/lib/geo";

const box: BBox = [10, 20, 12, 22]; // a 2×2 lon/lat square
const size = { w: 100, h: 100 };
const pad = 10;

describe("fitTransform", () => {
  it("fits a square box into a square canvas with a uniform, centered scale", () => {
    const t = fitTransform(box, size, pad);
    // avail = 80, span = 2 -> scale 40; square-in-square, so no extra centering offset
    expect(t.scale).toBeCloseTo(40, 6);
    expect(t.ox).toBeCloseTo(10, 6);
    expect(t.oy).toBeCloseTo(10, 6);
  });
});

describe("toPx", () => {
  const t = fitTransform(box, size, pad);
  it("maps the north-west corner to the padded top-left", () => {
    const [x, y] = toPx(10, 22, t);
    expect(x).toBeCloseTo(10, 6);
    expect(y).toBeCloseTo(10, 6);
  });
  it("flips latitude (north is up = smaller y)", () => {
    const [, yNorth] = toPx(11, 22, t);
    const [, ySouth] = toPx(11, 20, t);
    expect(yNorth).toBeLessThan(ySouth);
  });
});

describe("projectRing + perimeter", () => {
  const t = fitTransform(box, size, pad);
  const ring = [
    [10, 22],
    [12, 22],
    [12, 20],
    [10, 20],
    [10, 22],
  ];
  it("projects every vertex and preserves the point count", () => {
    const pts = projectRing(ring, t);
    expect(pts).toHaveLength(5);
    expect(pts[0][0]).toBeCloseTo(10, 6);
    expect(pts[0][1]).toBeCloseTo(10, 6);
  });
  it("measures the projected square's perimeter as 4 × 80px", () => {
    expect(perimeter(projectRing(ring, t))).toBeCloseTo(320, 6);
  });
});

describe("gridLines", () => {
  it("returns evenly spaced interior lines inside the padded area", () => {
    const { xs, ys } = gridLines(size, 20, pad);
    expect(xs).toEqual([30, 50, 70]);
    expect(ys).toEqual([30, 50, 70]);
  });
});

describe("terrainAt", () => {
  it("is deterministic for the same input", () => {
    expect(terrainAt(3, 7, 42)).toBe(terrainAt(3, 7, 42));
  });
  it("stays within [0,1]", () => {
    for (let i = 0; i < 50; i++) {
      const v = terrainAt(i, i * 2, 1);
      expect(v).toBeGreaterThanOrEqual(0);
      expect(v).toBeLessThanOrEqual(1);
    }
  });
  it("varies with the seed", () => {
    expect(terrainAt(3, 7, 1)).not.toBe(terrainAt(3, 7, 2));
  });
});
```

- [ ] **Step 2: Run it, expect FAIL** — `cd frontend && npx vitest run src/lib/aoiGeometry.test.ts` (module not found).

- [ ] **Step 3: Implement** — `frontend/src/lib/aoiGeometry.ts`

```ts
import type { BBox } from "@/lib/geo";

export interface Size {
  w: number;
  h: number;
}

/** A canvas pixel coordinate. */
export type Point = [number, number];

/** Uniform fit of a lon/lat bbox into a canvas: `scale` px per lon/lat unit, `(ox,oy)` the
 * top-left px of the fitted box. `box` is retained so `toPx` can resolve absolute positions. */
export interface Transform {
  scale: number;
  ox: number;
  oy: number;
  box: BBox;
}

/** Compute the aspect-preserving, centered transform that fits `box` into `size` with a `pad`
 * px inset on all sides. */
export function fitTransform(box: BBox, size: Size, pad: number): Transform {
  const [minLng, minLat, maxLng, maxLat] = box;
  const spanX = maxLng - minLng || 1e-9;
  const spanY = maxLat - minLat || 1e-9;
  const availW = size.w - pad * 2;
  const availH = size.h - pad * 2;
  const scale = Math.min(availW / spanX, availH / spanY);
  const ox = pad + (availW - spanX * scale) / 2;
  const oy = pad + (availH - spanY * scale) / 2;
  return { scale, ox, oy, box };
}

/** Project a lon/lat pair to canvas px. Latitude is flipped so north renders up (smaller y). */
export function toPx(lon: number, lat: number, t: Transform): Point {
  const [minLng, , , maxLat] = t.box;
  return [t.ox + (lon - minLng) * t.scale, t.oy + (maxLat - lat) * t.scale];
}

/** Project a GeoJSON ring (`[lng,lat][]`) to canvas px points. */
export function projectRing(ring: number[][], t: Transform): Point[] {
  return ring.map(([lng, lat]) => toPx(lng, lat, t));
}

/** Total pixel length of a point path — used to animate the boundary stroke draw-in. */
export function perimeter(points: Point[]): number {
  let sum = 0;
  for (let i = 1; i < points.length; i++) {
    const [x0, y0] = points[i - 1];
    const [x1, y1] = points[i];
    sum += Math.hypot(x1 - x0, y1 - y0);
  }
  return sum;
}

/** Evenly spaced interior grid line positions (vertical `xs`, horizontal `ys`) within the
 * padded area. `step` is the target px spacing. */
export function gridLines(size: Size, step: number, pad: number): { xs: number[]; ys: number[] } {
  const xs: number[] = [];
  const ys: number[] = [];
  for (let x = pad + step; x < size.w - pad; x += step) xs.push(x);
  for (let y = pad + step; y < size.h - pad; y += step) ys.push(y);
  return { xs, ys };
}

/** Deterministic value noise in `[0,1]` for integer cell `(x,y)` and `seed`. Uses `Math.imul`
 * for 32-bit-stable hashing — no `Math.random`/`Date.now`, so the texture is identical across
 * redraws, resizes, and SSR/hydration. */
export function terrainAt(x: number, y: number, seed: number): number {
  let h = Math.imul(x | 0, 374761393) ^ Math.imul(y | 0, 668265263) ^ Math.imul(seed | 0, 40503);
  h = Math.imul(h ^ (h >>> 13), 1274126177);
  h ^= h >>> 16;
  return (h >>> 0) / 4294967295;
}
```

- [ ] **Step 4: Run tests, expect PASS** — `npx vitest run src/lib/aoiGeometry.test.ts` (9 pass). Then `npx tsc --noEmit` exit 0.

- [ ] **Step 5: Review + commit** (code files — clear the gate)

```bash
git add frontend/src/lib/aoiGeometry.ts frontend/src/lib/aoiGeometry.test.ts
```
Run `/simplify` on the staged diff (apply cleanups), then `/code-review` (fix real findings), then:
```bash
git write-tree > .git/canopy-review-marker
git commit -m "feat(ui): AOI geometry + deterministic terrain-noise helper"
```

---

### Task 2: `AoiEvidenceLayer` component + Locate integration

**Files:**
- Create: `frontend/src/components/features/AoiEvidenceLayer.tsx`
- Modify: `frontend/src/app/projects/[id]/locate/page.tsx`

**Interfaces:**
- Consumes: `bbox` from `@/lib/geo`; `fitTransform`, `projectRing`, `perimeter`, `gridLines`, `terrainAt`, `toPx`, `Point` from `@/lib/aoiGeometry` (Task 1); `titleCase` from `@/lib/format`; `Boundary` from `@/lib/types`; `useProject` from `@/lib/queries`.
- Produces: `<AoiEvidenceLayer boundary={Boundary} centroid={[lon,lat]} assetType={string} areaHectares={number|null} className?={string} />`.

- [ ] **Step 1: Create `AoiEvidenceLayer.tsx`**

```tsx
"use client";
import { useEffect, useRef } from "react";
import { bbox } from "@/lib/geo";
import {
  fitTransform,
  gridLines,
  perimeter,
  projectRing,
  terrainAt,
  toPx,
  type Point,
} from "@/lib/aoiGeometry";
import { titleCase } from "@/lib/format";
import type { Boundary } from "@/lib/types";

const MAP_BG_FALLBACK = "#eef1f5";
const ACCENT_FALLBACK = "#0a7c4c";
const GRID_FALLBACK = "#d5dbe2";
const MUTED_FALLBACK = "#5b6670";

/** Read a CSS custom property's live value (theme-dependent). Canvas fill/stroke are plain
 * strings, not CSS, so we resolve tokens ourselves at draw time and repaint on theme flip. */
function token(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}

const PAD = 28;

/** The AOI rendered as a designed evidence layer: procedural terrain (asset-type aware), a
 * measurement grid + corner ticks, the located boundary polygon, and the centroid marker —
 * on a HiDPI Canvas that repaints on theme change. Removes the live-tile dependency for the
 * localization screen (see docs/specs/2026-07-20-professional-redesign-design.md). */
export function AoiEvidenceLayer({
  boundary,
  centroid,
  assetType,
  areaHectares,
  className = "relative h-96 w-full overflow-hidden rounded-card border border-border",
}: {
  boundary: Boundary;
  centroid: [number, number];
  assetType: string;
  areaHectares: number | null;
  className?: string;
}) {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [lon, lat] = centroid;

  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;
    const reduce = window.matchMedia("(prefers-reduced-motion: reduce)").matches;
    const seed = assetType === "mangrove" ? 71 : 23;
    let raf = 0;
    let startTs = 0;
    let animating = false;

    // `progress` ∈ [0,1] drives the mount animation: terrain/marker fade in, boundary strokes in.
    const draw = (progress: number) => {
      const ctx = canvas.getContext("2d");
      if (!ctx) return;
      const rect = canvas.getBoundingClientRect();
      const w = rect.width;
      const h = rect.height;
      if (w === 0 || h === 0) return;
      const dpr = window.devicePixelRatio || 1;
      canvas.width = Math.round(w * dpr);
      canvas.height = Math.round(h * dpr);
      ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
      ctx.clearRect(0, 0, w, h);

      const bg = token("--c-map-bg", MAP_BG_FALLBACK);
      const accent = token("--c-accent", ACCENT_FALLBACK);
      const grid = token("--color-border", GRID_FALLBACK);
      const muted = token("--color-muted", MUTED_FALLBACK);

      // 1. Background
      ctx.fillStyle = bg;
      ctx.fillRect(0, 0, w, h);

      // 2. Procedural terrain — coarse cells, asset-type-distinct, fading in with progress.
      const cell = 14;
      ctx.save();
      for (let gy = 0; gy < Math.ceil(h / cell); gy++) {
        for (let gx = 0; gx < Math.ceil(w / cell); gx++) {
          const n = terrainAt(gx, gy, seed);
          ctx.fillStyle = accent;
          if (assetType === "solar") {
            // Regular panel-field banding: darker alternating rows + slight noise jitter.
            const band = gy % 2 === 0 ? 0.1 : 0.02;
            ctx.globalAlpha = (band + n * 0.05) * progress;
            ctx.fillRect(gx * cell, gy * cell, cell - 1, cell - 1);
          } else {
            // Mangrove canopy: irregular mottled blobs keyed off the noise value.
            ctx.globalAlpha = (0.04 + n * 0.16) * progress;
            ctx.beginPath();
            ctx.arc(gx * cell + cell / 2, gy * cell + cell / 2, 2 + n * 4, 0, Math.PI * 2);
            ctx.fill();
          }
        }
      }
      ctx.restore();

      // 3. Measurement grid + corner ticks
      const { xs, ys } = gridLines({ w, h }, 48, PAD);
      ctx.save();
      ctx.strokeStyle = grid;
      ctx.globalAlpha = 0.6;
      ctx.lineWidth = 1;
      ctx.beginPath();
      for (const x of xs) {
        ctx.moveTo(x, PAD);
        ctx.lineTo(x, h - PAD);
      }
      for (const y of ys) {
        ctx.moveTo(PAD, y);
        ctx.lineTo(w - PAD, y);
      }
      ctx.stroke();
      ctx.restore();

      const tick = 10;
      const corners: Point[] = [
        [PAD, PAD],
        [w - PAD, PAD],
        [w - PAD, h - PAD],
        [PAD, h - PAD],
      ];
      ctx.save();
      ctx.strokeStyle = muted;
      ctx.lineWidth = 1.5;
      ctx.beginPath();
      for (const [cx, cy] of corners) {
        const sx = cx === PAD ? 1 : -1;
        const sy = cy === PAD ? 1 : -1;
        ctx.moveTo(cx, cy + sy * tick);
        ctx.lineTo(cx, cy);
        ctx.lineTo(cx + sx * tick, cy);
      }
      ctx.stroke();
      ctx.restore();

      // 4. Boundary polygon — soft fill + accent stroke that draws in via line dash.
      const tf = fitTransform(bbox(boundary.geometry.coordinates), { w, h }, PAD);
      const ring = projectRing(boundary.geometry.coordinates[0] ?? [], tf);
      if (ring.length > 1) {
        ctx.save();
        ctx.beginPath();
        ctx.moveTo(ring[0][0], ring[0][1]);
        for (let i = 1; i < ring.length; i++) ctx.lineTo(ring[i][0], ring[i][1]);
        ctx.closePath();
        ctx.fillStyle = accent;
        ctx.globalAlpha = 0.08 * progress;
        ctx.fill();
        ctx.globalAlpha = 1;
        ctx.strokeStyle = accent;
        ctx.lineWidth = 2;
        ctx.lineJoin = "round";
        const per = perimeter(ring);
        ctx.setLineDash([per]);
        ctx.lineDashOffset = per * (1 - progress);
        ctx.stroke();
        ctx.restore();

        // 5. Centroid marker
        const [mx, my] = toPx(lon, lat, tf);
        ctx.save();
        ctx.globalAlpha = progress;
        ctx.fillStyle = accent;
        ctx.beginPath();
        ctx.arc(mx, my, 5, 0, Math.PI * 2);
        ctx.fill();
        ctx.lineWidth = 2;
        ctx.strokeStyle = bg;
        ctx.stroke();
        ctx.restore();
      }
    };

    const frame = (ts: number) => {
      if (!startTs) startTs = ts;
      const p = Math.min(1, (ts - startTs) / 750);
      const eased = 1 - Math.pow(1 - p, 3); // easeOutCubic
      draw(eased);
      if (p < 1) {
        raf = requestAnimationFrame(frame);
      } else {
        animating = false;
      }
    };

    if (reduce) {
      draw(1);
    } else {
      animating = true;
      raf = requestAnimationFrame(frame);
    }

    // Repaint the final frame on resize / theme flip — but not mid-animation (the running
    // rAF loop already owns the canvas then, so a stray full-frame paint would flicker).
    const repaint = () => {
      if (!animating) draw(1);
    };
    const ro = new ResizeObserver(repaint);
    ro.observe(canvas);
    const themeObserver = new MutationObserver(repaint);
    themeObserver.observe(document.documentElement, {
      attributes: true,
      attributeFilter: ["data-theme"],
    });

    return () => {
      cancelAnimationFrame(raf);
      ro.disconnect();
      themeObserver.disconnect();
    };
  }, [boundary, lon, lat, assetType]);

  return (
    <div className={className}>
      <canvas ref={canvasRef} className="block h-full w-full" />
      <div className="pointer-events-none absolute inset-x-0 bottom-0 flex flex-wrap items-center gap-x-4 gap-y-1 border-t border-border bg-surface/85 px-4 py-2 text-xs backdrop-blur">
        <span className="label">AOI</span>
        {areaHectares != null && (
          <span className="text-muted">
            <span className="font-mono tabular-nums text-ink">
              {Math.round(areaHectares).toLocaleString()}
            </span>{" "}
            ha
          </span>
        )}
        <span className="font-mono tabular-nums text-muted">
          {lat.toFixed(4)}, {lon.toFixed(4)}
        </span>
        <span className="ml-auto text-faint">{titleCase(assetType)}</span>
      </div>
    </div>
  );
}
```

- [ ] **Step 2: Wire it into `locate/page.tsx`**

Replace the `EvidenceMap` import with `AoiEvidenceLayer`, add `useProject` to the `queries` import, read the project for `asset_type`, and swap the render. The `className` override keeps `relative` (the caption is absolutely positioned) but drops the border/rounding since the enclosing `Card` supplies the frame.

Import line changes (top of file):
```tsx
import { AoiEvidenceLayer } from "@/components/features/AoiEvidenceLayer";
```
(remove `import { EvidenceMap } from "@/components/map/EvidenceMap";`)

```tsx
import { useBoundary, useDossier, useProject } from "@/lib/queries";
```
(was `import { useBoundary, useDossier } from "@/lib/queries";`)

Inside the component, after the existing `useDossier` line, add:
```tsx
  const { data: project } = useProject(id);
```

Replace the map block:
```tsx
        <EvidenceMap
          boundary={boundary}
          marker={{ lon, lat, label: "Located centroid" }}
          className="h-96 w-full"
        />
```
with:
```tsx
        <AoiEvidenceLayer
          boundary={boundary}
          centroid={localization.located_centroid}
          assetType={project?.asset_type ?? "solar"}
          areaHectares={boundary.properties.area_hectares}
          className="relative h-96 w-full"
        />
```

(The `const [lon, lat] = localization.located_centroid;` line stays — `tone` and the Localization card below still use it. No other change to the file.)

- [ ] **Step 3: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All pass. Vitest is now **8 files, 30 tests** (21 prior + 9 new aoiGeometry). No unused-import lint error in `locate/page.tsx` (confirm `EvidenceMap` import is gone and `useProject` is used).

- [ ] **Step 4: Review + commit** (code files — clear the gate)

```bash
git add frontend/src/components/features/AoiEvidenceLayer.tsx "frontend/src/app/projects/[id]/locate/page.tsx"
```
Run `/simplify` (apply cleanups), `/code-review` (fix real findings), then:
```bash
git write-tree > .git/canopy-review-marker
git commit -m "feat(ui): AoiEvidenceLayer canvas — designed AOI evidence on Locate"
```

---

### Task 3: Verify both assets + both themes in the browser

- [ ] **Step 1:** Gates green (Task 2 Step 3 already ran them; re-confirm nothing regressed).
- [ ] **Step 2:** With dev (`:3000`) + backend (`:8001`) up, drive `/projects/nur_navoi_solar/locate` and `/projects/mikoko_pamoja/locate`. For each, screenshot **light**, then toggle **dark**. Confirm for each:
  - The boundary polygon renders in accent with a soft fill; the centroid marker sits inside it.
  - The terrain texture is **visibly asset-distinct** (solar = regular banded field; mangrove = irregular mottled canopy).
  - The measurement grid + corner ticks render; the caption strip shows area (ha) + `lat, lon` in Geist Mono + the asset label, all legible.
  - Toggling the theme **repaints** the canvas cleanly (background + accent + grid recolor; no stale colors, no flicker).
  - Layout doesn't break; **zero console errors**.
  - The boundary animates in on load when motion is allowed, and paints immediately under `prefers-reduced-motion`.
- [ ] **Step 3:** Confirm **Timeline (Observe) is unchanged** — `/projects/nur_navoi_solar/timeline` still shows `EvidenceMap` with the working before/after swipe slider.
- [ ] **Step 4:** Fix any straggler (contrast, layout, texture legibility), re-verify. Note the outcome.

---

## Self-Review

**Spec coverage:** `AoiEvidenceLayer` (Canvas evidence layer with procedural asset-type terrain, boundary polygon in accent, measurement grid, corner ticks, caption strip) is built (Task 2), driven by tested pure helpers (Task 1), theme-repainting + reduced-motion aware, and swapped in on its most prominent home — Locate (Task 2 Step 2) — verified in both themes/assets (Task 3). The spec's caption "source/date" is intentionally reduced to **honest fields only** (area + coordinates + asset label) per the design's no-fabricated-trust-signals rule; this is called out in Global Constraints. The remaining Phase-B signature components (pipeline strip, refined pills/`TraceChip`) are **deferred to Phase B part 3**, and MapLibre removal to a deliberate Phase C decision — both stated in Global Constraints. `EvidenceMap`/Timeline left untouched (Task 3 Step 3 guards the regression).

**Placeholder scan:** clean — complete code in every step; no TODO/TBD.

**Type consistency:** `fitTransform`/`toPx`/`projectRing`/`perimeter`/`gridLines`/`terrainAt`/`Point`/`Size`/`Transform` signatures match between Task 1 (definition + test) and Task 2 (consumption). `AoiEvidenceLayer` props (`boundary`, `centroid`, `assetType`, `areaHectares`, `className?`) match the Locate call site. `assetType` values (`"solar"`/`"mangrove"`) match the seed data and the `seed`/texture branches. Token names (`--c-map-bg`, `--c-accent`, `--color-border`, `--color-muted`) verified present in `globals.css`.
