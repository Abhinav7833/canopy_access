# Professional Redesign — Phase A (Foundation) Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Give Canopy a token-driven light **and** dark theme (green identity, disciplined execution) with a persistent, no-flash theme toggle, so the entire existing app renders correctly in both themes — the foundation the later redesign phases build on.

**Architecture:** The app already styles through Tailwind v4 `@theme` token utilities (`bg-surface`, `text-ink`, `border-border`, `bg-accent`, …). We redefine the palette as runtime CSS custom properties with a light default and a dark override (via `prefers-color-scheme` **and** `data-theme`), so nearly every component flips for free. A tiny theme utility + pre-hydration script + a `TopBar` toggle drive it. The only hard-coded colors (MapLibre paint in `EvidenceMap`) are made theme-aware explicitly.

**Tech Stack:** Next.js 16 (App Router, Turbopack), Tailwind CSS v4 (`@theme` in `globals.css`), `next/font` (Geist — kept, self-hosted), TypeScript, Vitest + Testing Library (jsdom), MapLibre GL.

## Global Constraints

- **No fabricated trust signals** anywhere (no fake logos/testimonials/compliance badges/metrics). Phase A adds none; keep it that way.
- **Self-contained assets only** — no external CDN/webfont/image/tile. Keep Geist via `next/font` (self-hosts at build).
- **No backend/API/schema/seed/data change.** Presentation only; same routes, same payloads.
- **Light + dark parity** — both themes AA-legible; dark is not a naive invert. Respect `prefers-color-scheme`; a manual toggle overrides and persists; no flash-of-wrong-theme on load.
- **Accessibility** — status never by color alone (already the pattern); visible `:focus-visible`; honor `prefers-reduced-motion`.
- **Framework caution** — `frontend/AGENTS.md`: "This is NOT the Next.js you know — read the relevant guide in `node_modules/next/dist/docs/` before writing any code." Consult it before the `layout.tsx` script change.
- **Green palette** (verbatim). Light: ground `#f2f5f2`, surface `#ffffff`, surface-2 `#f7faf7`, ink `#0d1712`, ink-2 `#38473f`, muted `#5c7167`, faint `#708577`, line `#e4e9e5`, line-strong `#d4ddd7`, accent `#0a7c4c`, accent-2 `#086b41`, accent-soft `#e8f5ee`, accent-line `#b7e4cd`, accent-ink `#ffffff`. Dark: ground `#0a0f0d`, surface `#111814`, surface-2 `#0e1512`, ink `#e9efe9`, ink-2 `#b7c4bc`, muted `#8ba095`, faint `#697c72`, line `#202b25`, line-strong `#2c3b33`, accent `#31c07a`, accent-2 `#46d18c`, accent-soft `rgba(49,192,122,.13)`, accent-line `rgba(49,192,122,.32)`, accent-ink `#04140c`. Risk ramp: low = accent-green; med `#b45309`/dark `#e0922f`; high `#b42318`/dark `#e5645a` (+ soft/line variants). Muted/faint values updated 2026-07-20 to meet WCAG AA contrast (muted ≥4.5:1, faint ≥3.0:1 against both surface and canvas in each theme) — see `.superpowers/sdd/task-1-report.md` for the contrast-ratio table.
- **Theme storage key:** `canopy-theme`; values `"light"|"dark"`; attribute `data-theme` on `<html>`.

**Run commands** (from `frontend/`): typecheck `npx tsc --noEmit` · lint `npx eslint` · unit `npx vitest run` · build `npx next build`. Dev server is typically already running on `:3000` (backend proxied on `:8001`).

---

### Task 1: Token architecture — light + dark palette in `globals.css`

**Files:**
- Modify: `frontend/src/app/globals.css` (replace the `@theme` + `:root` legacy-alias blocks; keep `.label`, `.num`, `body`, `::selection`).

**Interfaces:**
- Produces: runtime CSS custom properties `--c-*` (palette) on `:root` (light) and under `@media (prefers-color-scheme: dark)` + `:root[data-theme="dark"]` / `:root[data-theme="light"]`; `@theme` maps `--color-*` → `var(--c-*)` so existing utilities (`bg-surface`, `text-ink`, `border-border`, `bg-accent`, `text-muted`, `text-faint`, `bg-canvas`, risk-* …) resolve at runtime and flip with the theme.

- [ ] **Step 1: Read the current file and the Tailwind v4 dark-mode guidance**

Read `frontend/src/app/globals.css` in full. Then confirm the v4 mechanism (theme vars referenced as `var(--color-*)` by utilities; overriding the referenced runtime var flips them) against `node_modules/tailwindcss` docs or the installed version's changelog. The indirection pattern below (`--color-x: var(--c-x)`) is the robust form.

- [ ] **Step 2: Replace the theme/token blocks**

Replace everything from the top `@theme { … }` block through the legacy `:root { --bg … }` block with:

```css
@import "tailwindcss";

/* ------------------------------------------------------------------ *
 * Canopy design system — green identity, light + dark parity.
 * Palette lives in runtime --c-* vars; @theme maps --color-* to them
 * so Tailwind utilities flip with the theme. Green-biased neutrals,
 * one deep-emerald accent, semantic risk ramp.
 * ------------------------------------------------------------------ */

/* light (default) */
:root {
  --c-canvas:#f2f5f2; --c-surface:#ffffff; --c-surface-muted:#f7faf7;
  --c-ink:#0d1712; --c-ink-2:#38473f; --c-muted:#61756a; --c-faint:#8a9c90;
  --c-border:#e4e9e5; --c-border-strong:#d4ddd7;
  --c-accent:#0a7c4c; --c-accent-hover:#086b41; --c-accent-soft:#e8f5ee; --c-accent-border:#b7e4cd; --c-accent-ink:#ffffff;
  --c-risk-low:#0a7c4c; --c-risk-low-soft:#e8f5ee; --c-risk-low-border:#b7e4cd;
  --c-risk-med:#b45309; --c-risk-med-soft:#fbf1e4; --c-risk-med-border:#f0d6a6;
  --c-risk-high:#b42318; --c-risk-high-soft:#fbeeec; --c-risk-high-border:#f2cbc6;
  --c-risk-critical:#7a271a;
  --c-map-bg:#eef1f5;
  --shadow-card:0 1px 2px rgba(13,23,18,.05);
  --shadow-raised:0 14px 34px -14px rgba(13,23,18,.16);
  --shadow-overlay:0 20px 40px -12px rgba(13,23,18,.22);
  --glow:none;
  color-scheme:light;
}

/* Dark values, applied when the OS prefers dark and the user has not chosen
   light, and again for the explicit-dark root (so the toggle always wins). */
@media (prefers-color-scheme: dark) {
  :root:not([data-theme="light"]) {
    --c-canvas:#0a0f0d; --c-surface:#111814; --c-surface-muted:#0e1512;
    --c-ink:#e9efe9; --c-ink-2:#b7c4bc; --c-muted:#8ba095; --c-faint:#62746a;
    --c-border:#202b25; --c-border-strong:#2c3b33;
    --c-accent:#31c07a; --c-accent-hover:#46d18c; --c-accent-soft:rgba(49,192,122,.13); --c-accent-border:rgba(49,192,122,.32); --c-accent-ink:#04140c;
    --c-risk-low:#31c07a; --c-risk-low-soft:rgba(49,192,122,.13); --c-risk-low-border:rgba(49,192,122,.32);
    --c-risk-med:#e0922f; --c-risk-med-soft:rgba(224,146,47,.13); --c-risk-med-border:rgba(224,146,47,.30);
    --c-risk-high:#e5645a; --c-risk-high-soft:rgba(229,100,90,.13); --c-risk-high-border:rgba(229,100,90,.30);
    --c-risk-critical:#f0857a;
    --c-map-bg:#0e1512;
    --shadow-card:0 1px 2px rgba(0,0,0,.4);
    --shadow-raised:0 18px 44px -18px rgba(0,0,0,.62);
    --shadow-overlay:0 24px 48px -14px rgba(0,0,0,.7);
    --glow:0 0 34px rgba(49,192,122,.14);
    color-scheme:dark;
  }
}
:root[data-theme="dark"] {
  --c-canvas:#0a0f0d; --c-surface:#111814; --c-surface-muted:#0e1512;
  --c-ink:#e9efe9; --c-ink-2:#b7c4bc; --c-muted:#8ba095; --c-faint:#62746a;
  --c-border:#202b25; --c-border-strong:#2c3b33;
  --c-accent:#31c07a; --c-accent-hover:#46d18c; --c-accent-soft:rgba(49,192,122,.13); --c-accent-border:rgba(49,192,122,.32); --c-accent-ink:#04140c;
  --c-risk-low:#31c07a; --c-risk-low-soft:rgba(49,192,122,.13); --c-risk-low-border:rgba(49,192,122,.32);
  --c-risk-med:#e0922f; --c-risk-med-soft:rgba(224,146,47,.13); --c-risk-med-border:rgba(224,146,47,.30);
  --c-risk-high:#e5645a; --c-risk-high-soft:rgba(229,100,90,.13); --c-risk-high-border:rgba(229,100,90,.30);
  --c-risk-critical:#f0857a;
  --c-map-bg:#0e1512;
  --shadow-card:0 1px 2px rgba(0,0,0,.4);
  --shadow-raised:0 18px 44px -18px rgba(0,0,0,.62);
  --shadow-overlay:0 24px 48px -14px rgba(0,0,0,.7);
  --glow:0 0 34px rgba(49,192,122,.14);
  color-scheme:dark;
}

@theme {
  --font-sans: var(--font-geist-sans), ui-sans-serif, system-ui, sans-serif;
  --font-mono: var(--font-geist-mono), ui-monospace, "SF Mono", monospace;

  --color-canvas: var(--c-canvas);
  --color-surface: var(--c-surface);
  --color-surface-muted: var(--c-surface-muted);
  --color-border: var(--c-border);
  --color-border-strong: var(--c-border-strong);
  --color-ink: var(--c-ink);
  --color-ink-2: var(--c-ink-2);
  --color-muted: var(--c-muted);
  --color-faint: var(--c-faint);
  --color-accent: var(--c-accent);
  --color-accent-hover: var(--c-accent-hover);
  --color-accent-soft: var(--c-accent-soft);
  --color-accent-border: var(--c-accent-border);
  --color-accent-ink: var(--c-accent-ink);
  --color-risk-low: var(--c-risk-low);
  --color-risk-low-soft: var(--c-risk-low-soft);
  --color-risk-low-border: var(--c-risk-low-border);
  --color-risk-med: var(--c-risk-med);
  --color-risk-med-soft: var(--c-risk-med-soft);
  --color-risk-med-border: var(--c-risk-med-border);
  --color-risk-high: var(--c-risk-high);
  --color-risk-high-soft: var(--c-risk-high-soft);
  --color-risk-high-border: var(--c-risk-high-border);
  --color-risk-critical: var(--c-risk-critical);

  --radius-card: 12px;
  --shadow-card: var(--shadow-card);
  --shadow-raised: var(--shadow-raised);
  --shadow-overlay: var(--shadow-overlay);
}
```

Then keep the existing `body`, `.tnum`/`table`/`.font-mono` tabular rule, `.label`, and `::selection` rules that follow — but change `body` transitions to include theme:

```css
body {
  background: var(--color-canvas);
  color: var(--color-ink);
  font-family: var(--font-sans);
  -webkit-font-smoothing: antialiased;
  transition: background .25s ease, color .25s ease;
}
```

Remove the old legacy `:root { --bg … }` alias block **only if** a grep shows nothing consumes those `var(--bg)`/`var(--panel)`/etc. aliases (see next step); otherwise keep it, pointing the aliases at the new `--color-*`.

- [ ] **Step 3: Check for legacy-alias consumers before deleting them**

Run: `grep -rnE "var\(--(bg|panel|text|danger|warn)\)" frontend/src`
Expected: no matches (all migrated). If any exist, retain a `:root { --bg:var(--color-canvas); --panel:var(--color-surface); --border:var(--color-border); --text:var(--color-ink); --muted:var(--color-muted); --accent:var(--color-accent); --danger:var(--color-risk-high); --warn:var(--color-risk-med); }` block instead of deleting it.

- [ ] **Step 4: Build to confirm tokens compile and light is unchanged**

Run: `cd frontend && npx next build`
Expected: build succeeds. Then `npx tsc --noEmit` → exit 0.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/app/globals.css
git commit -m "feat(ui): token architecture for light + dark green themes"
```

---

### Task 2: Theme utility + tests

**Files:**
- Create: `frontend/src/lib/theme.ts`
- Test: `frontend/src/lib/theme.test.ts`

**Interfaces:**
- Produces: `type Theme = "light" | "dark"`; `THEME_KEY: "canopy-theme"`; `storedTheme(): Theme | null`; `systemTheme(): Theme`; `resolveTheme(): Theme`; `applyTheme(t: Theme): void`; `setTheme(t: Theme): void`; `toggleTheme(): Theme`.

- [ ] **Step 1: Write the failing test**

Create `frontend/src/lib/theme.test.ts`:

```ts
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { resolveTheme, setTheme, storedTheme, THEME_KEY, toggleTheme } from "@/lib/theme";

function mockMatchMedia(dark: boolean) {
  vi.stubGlobal("matchMedia", (q: string) => ({
    matches: q.includes("dark") ? dark : !dark,
    media: q, addEventListener() {}, removeEventListener() {},
    addListener() {}, removeListener() {}, dispatchEvent() { return false; },
    onchange: null,
  }));
}

describe("theme", () => {
  beforeEach(() => { localStorage.clear(); document.documentElement.removeAttribute("data-theme"); });
  afterEach(() => vi.unstubAllGlobals());

  it("falls back to the system preference when nothing is stored", () => {
    mockMatchMedia(true);
    expect(storedTheme()).toBeNull();
    expect(resolveTheme()).toBe("dark");
  });

  it("prefers the stored choice over the system preference", () => {
    mockMatchMedia(true);
    setTheme("light");
    expect(localStorage.getItem(THEME_KEY)).toBe("light");
    expect(resolveTheme()).toBe("light");
    expect(document.documentElement.getAttribute("data-theme")).toBe("light");
  });

  it("toggles, persists, and applies the opposite theme", () => {
    mockMatchMedia(false); // system light
    expect(toggleTheme()).toBe("dark");
    expect(document.documentElement.getAttribute("data-theme")).toBe("dark");
    expect(toggleTheme()).toBe("light");
  });
});
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd frontend && npx vitest run src/lib/theme.test.ts`
Expected: FAIL — cannot resolve `@/lib/theme`.

- [ ] **Step 3: Implement `theme.ts`**

```ts
export type Theme = "light" | "dark";
export const THEME_KEY = "canopy-theme";

export function storedTheme(): Theme | null {
  try {
    const v = localStorage.getItem(THEME_KEY);
    return v === "light" || v === "dark" ? v : null;
  } catch {
    return null;
  }
}

export function systemTheme(): Theme {
  return typeof matchMedia === "function" && matchMedia("(prefers-color-scheme: dark)").matches
    ? "dark"
    : "light";
}

export function resolveTheme(): Theme {
  return storedTheme() ?? systemTheme();
}

export function applyTheme(theme: Theme): void {
  document.documentElement.setAttribute("data-theme", theme);
}

export function setTheme(theme: Theme): void {
  try {
    localStorage.setItem(THEME_KEY, theme);
  } catch {
    /* storage unavailable — still apply for this session */
  }
  applyTheme(theme);
}

export function toggleTheme(): Theme {
  const next: Theme = resolveTheme() === "dark" ? "light" : "dark";
  setTheme(next);
  return next;
}
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `cd frontend && npx vitest run src/lib/theme.test.ts`
Expected: PASS (3 tests).

- [ ] **Step 5: Commit**

```bash
git add frontend/src/lib/theme.ts frontend/src/lib/theme.test.ts
git commit -m "feat(ui): theme resolve/persist/toggle utility with tests"
```

---

### Task 3: No-flash pre-hydration script in `layout.tsx`

**Files:**
- Modify: `frontend/src/app/layout.tsx`

**Interfaces:**
- Consumes: `THEME_KEY` semantics (inlined literally in the script — it runs before modules load, so it cannot import).
- Produces: `data-theme` set on `<html>` before first paint; `suppressHydrationWarning` so React does not warn about the script-set attribute.

- [ ] **Step 1: Read the Next 16 layout guidance**

Per `frontend/AGENTS.md`, skim `node_modules/next/dist/docs/` for the App Router root-layout / inline-script conventions before editing.

- [ ] **Step 2: Add the script + suppressHydrationWarning**

Modify `frontend/src/app/layout.tsx` — add `suppressHydrationWarning` to `<html>` and render an inline script as the first child of `<body>`:

```tsx
    <html
      lang="en"
      suppressHydrationWarning
      className={`${geistSans.variable} ${geistMono.variable} h-full antialiased`}
    >
      <body className="min-h-full bg-canvas text-ink">
        <script
          dangerouslySetInnerHTML={{
            __html:
              "(function(){try{var k='canopy-theme';var t=localStorage.getItem(k);" +
              "if(t!=='light'&&t!=='dark'){t=matchMedia('(prefers-color-scheme: dark)').matches?'dark':'light';}" +
              "document.documentElement.setAttribute('data-theme',t);}catch(e){}})();",
          }}
        />
        <Providers>
          <TopBar />
          <div className="mx-auto max-w-6xl px-6 py-8">{children}</div>
        </Providers>
      </body>
    </html>
```

- [ ] **Step 3: Verify build + no hydration warning**

Run: `cd frontend && npx next build` → succeeds. Then with the dev server running, load `/` and confirm no React hydration warning in the browser console and `<html>` carries `data-theme`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/app/layout.tsx
git commit -m "feat(ui): pre-hydration theme script (no flash of wrong theme)"
```

---

### Task 4: `ThemeToggle` + `TopBar` refresh (drop the leaf mark)

**Files:**
- Create: `frontend/src/components/layout/ThemeToggle.tsx`
- Modify: `frontend/src/components/layout/TopBar.tsx`

**Interfaces:**
- Consumes: `resolveTheme`, `toggleTheme`, `type Theme` from `@/lib/theme`.
- Produces: `<ThemeToggle />` (client component) rendered in `TopBar`.

- [ ] **Step 1: Create `ThemeToggle.tsx`**

```tsx
"use client";
import { useEffect, useState } from "react";
import { resolveTheme, toggleTheme, type Theme } from "@/lib/theme";

export function ThemeToggle() {
  // Start "light" for a deterministic SSR render; sync to the real theme after mount
  // (the pre-hydration script has already set the correct <html data-theme>).
  const [theme, setThemeState] = useState<Theme>("light");
  useEffect(() => setThemeState(resolveTheme()), []);

  const dark = theme === "dark";
  return (
    <button
      type="button"
      onClick={() => setThemeState(toggleTheme())}
      aria-label={`Switch to ${dark ? "light" : "dark"} theme`}
      title="Toggle theme"
      className="grid h-8 w-8 place-items-center rounded-lg border border-border-strong bg-surface text-muted transition-colors hover:border-faint hover:text-ink"
    >
      <svg viewBox="0 0 24 24" className="h-4 w-4" fill="none" stroke="currentColor" strokeWidth="1.7" strokeLinecap="round" strokeLinejoin="round">
        {dark ? (
          <>
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2M12 20v2M2 12h2M20 12h2M5 5l1.4 1.4M17.6 17.6L19 19M19 5l-1.4 1.4M6.4 17.6L5 19" />
          </>
        ) : (
          <path d="M20 14.5A7.5 7.5 0 1 1 9.5 4a6 6 0 0 0 10.5 10.5z" />
        )}
      </svg>
    </button>
  );
}
```

- [ ] **Step 2: Refresh `TopBar.tsx` — abstract mark + toggle**

Replace `LeafMark` with an abstract wordmark tile (no leaf) and add the toggle:

```tsx
import Link from "next/link";
import { ThemeToggle } from "@/components/layout/ThemeToggle";

function BrandMark() {
  return (
    <span className="relative grid h-6 w-6 place-items-center rounded-md bg-accent" aria-hidden="true">
      <span className="absolute inset-x-1.5 top-1.5 h-0.5 rounded bg-accent-ink/90" />
      <span className="absolute inset-x-1.5 bottom-2 h-0.5 rounded bg-accent-ink/60" />
    </span>
  );
}

export function TopBar() {
  return (
    <header className="sticky top-0 z-40 border-b border-border bg-surface/80 backdrop-blur">
      <div className="mx-auto flex h-14 max-w-6xl items-center gap-3 px-6">
        <Link href="/" className="flex items-center gap-2.5">
          <BrandMark />
          <span className="text-[13px] font-semibold tracking-[0.18em] text-ink">CANOPY</span>
        </Link>
        <span className="hidden text-faint sm:inline">/</span>
        <span className="hidden text-sm text-muted sm:inline">Evidence &amp; Risk</span>
        <div className="ml-auto flex items-center gap-2">
          <span className="inline-flex items-center gap-1.5 rounded-md border border-border bg-surface px-2.5 py-1 text-xs text-muted">
            <span className="h-1.5 w-1.5 rounded-full bg-accent" />
            Demo environment
          </span>
          <ThemeToggle />
        </div>
      </div>
    </header>
  );
}
```

- [ ] **Step 3: Verify gates**

Run: `cd frontend && npx tsc --noEmit && npx eslint && npx vitest run`
Expected: tsc exit 0, eslint exit 0, all vitest pass.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/layout/ThemeToggle.tsx frontend/src/components/layout/TopBar.tsx
git commit -m "feat(ui): theme toggle in TopBar; replace leaf mark with abstract wordmark"
```

---

### Task 5: Make `EvidenceMap` theme-aware

**Files:**
- Modify: `frontend/src/components/map/EvidenceMap.tsx` (hard-coded `#eef1f5`, `#067647` at ~lines 24, 124, 130)

**Interfaces:**
- Consumes: the runtime tokens `--c-map-bg` and `--c-accent` from `globals.css`.
- Produces: a map whose no-tile background and boundary color follow the theme and update when `data-theme` changes.

- [ ] **Step 1: Read the component**

Read `frontend/src/components/map/EvidenceMap.tsx` fully to locate the style/`addLayer`/`setPaintProperty` calls and the map lifecycle (where the `map` instance and boundary layer are created).

- [ ] **Step 2: Read tokens instead of hard-coding, and re-apply on theme change**

Add a token reader and use it for the background layer and boundary paint; then observe `data-theme` and update. Replace the literal `#eef1f5` background with `token("--c-map-bg", "#eef1f5")` and the two `#067647` boundary values with `token("--c-accent", "#0a7c4c")`:

```ts
function token(name: string, fallback: string): string {
  if (typeof window === "undefined") return fallback;
  const v = getComputedStyle(document.documentElement).getPropertyValue(name).trim();
  return v || fallback;
}
```

After the map and layers are created, wire a `MutationObserver` (inside the existing map-setup `useEffect`, before its cleanup return) to recolor on theme flip:

```ts
const observer = new MutationObserver(() => {
  if (!map.isStyleLoaded()) return;
  map.setPaintProperty("bg", "background-color", token("--c-map-bg", "#eef1f5"));
  if (map.getLayer("boundary-fill")) map.setPaintProperty("boundary-fill", "fill-color", token("--c-accent", "#0a7c4c"));
  if (map.getLayer("boundary-line")) map.setPaintProperty("boundary-line", "line-color", token("--c-accent", "#0a7c4c"));
});
observer.observe(document.documentElement, { attributes: true, attributeFilter: ["data-theme"] });
```

Add `observer.disconnect();` to the effect's cleanup. Adjust the layer ids (`"bg"`, `"boundary-fill"`, `"boundary-line"`) to whatever the file actually uses — read them in Step 1 and match exactly.

- [ ] **Step 3: Verify gates + a manual map check**

Run: `cd frontend && npx tsc --noEmit && npx next build` → both succeed. With the dev server running, open a project's Locate/Observe tab, toggle the theme, and confirm the map background and AOI boundary recolor (no console errors).

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/map/EvidenceMap.tsx
git commit -m "feat(ui): make EvidenceMap background + boundary theme-aware"
```

---

### Task 6: Full verification — both themes across the app

**Files:** none (verification task).

- [ ] **Step 1: Green gates**

Run from `frontend/`: `npx tsc --noEmit && npx eslint && npx vitest run && npx next build`. All must pass with no new errors.

- [ ] **Step 2: Drive both themes in a browser (Playwright)**

With the dev (`:3000`) + backend (`:8001`) servers running, drive: the portfolio `/`, a solar dossier (`/projects/nur_navoi_solar` and its `/timeline`, `/crosscheck`), and a mangrove dossier (`/projects/mikoko_pamoja`). For each, snapshot/screenshot in **light** then toggle to **dark** and re-check. Confirm:
- The toggle flips every surface (nav, cards, tables, badges, pills, meters, map) — no element stuck in the wrong theme (watch for any missed hard-coded color).
- Text meets AA contrast in both themes; the accent green is legible on both grounds.
- No flash-of-wrong-theme on a hard reload with `data-theme="dark"` chosen.
- Zero console errors; `prefers-reduced-motion` honored.

- [ ] **Step 3: Record findings & fix stragglers**

If any component didn't flip, it has a hard-coded color or a non-token utility — grep it, convert to the token utility (or a `--c-*` read), and re-verify. Note the check outcome in the commit body.

- [ ] **Step 4: Run the pre-commit review gate + commit the phase**

Run `/simplify` then `/code-review` on the Phase A diff, apply real findings, then commit any fixes (record the review marker as the gate requires). Phase A is complete when both themes render every existing screen cleanly and all gates are green.

---

## Self-Review

**Spec coverage (Phase A slice):** token architecture + dark palette (Task 1) ✓; theme resolve/persist/toggle + no-flash (Tasks 2–4) ✓; light/dark parity across existing components (Tasks 1, 5, 6) ✓; drop the leaf mark / disciplined green (Task 4) ✓; a11y + reduced-motion + AA (Task 6) ✓; no data/behavior change (all tasks presentation-only) ✓; self-hosted assets / keep Geist (unchanged) ✓; no fabricated trust signals (none added) ✓. Signature components, product-screen overhaul, and the landing page are **out of scope for Phase A** — they are Phases B/C/D, each getting its own plan after A lands.

**Placeholder scan:** clean — no TBD/TODO/"handle edge cases"; every code step contains complete, copy-ready content. (One thing to confirm at execution, not a placeholder: the exact MapLibre layer ids in Task 5 must be read from the file and matched.)

**Type consistency:** `theme.ts` exports (`Theme`, `THEME_KEY`, `storedTheme`, `systemTheme`, `resolveTheme`, `applyTheme`, `setTheme`, `toggleTheme`) are used with matching names/signatures in `theme.test.ts` and `ThemeToggle.tsx`. Token names `--c-*` in Task 1 match the reads in Task 5 (`--c-map-bg`, `--c-accent`). `data-theme` attribute + `canopy-theme` key are consistent across the script (Task 3), utility (Task 2), and tests.
