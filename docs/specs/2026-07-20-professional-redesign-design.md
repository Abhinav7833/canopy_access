# Professional Redesign — B2B SaaS Visual System (light + dark green)

**Date:** 2026-07-20
**Status:** Approved design (visual direction signed off via the concept artifact), pre-implementation.
**Visual source of truth:** the approved concept — `claude.ai/code/artifact/63eaabc6-53d0-46a2-859f-e7987bc74881` (green light/dark, confidence-as-rating, AOI-as-data-layer). Snapshot of intent, not of final code.

## Goal

Make Canopy read as a funded, credible **B2B SaaS for finance people** — across both a new marketing **landing page** and a full overhaul of the **product screens** — while keeping green as the brand identity and shipping full **light + dark** parity.

Audience: finance/institutional viewers (investment committees, green-bond/carbon buyers, asset managers) evaluating whether a financed green claim holds up. The design must convey rigor and trust, and explain the pipeline to a non-technical finance reader.

This is purely a **presentation-layer** effort. No backend, API, schema, or seed changes. The data contract (`/projects`, `/projects/{id}/dossier`, etc.) is unchanged; every screen keeps reading the same payloads.

## Industry grounding (why this direction)

From researching the direct category (Sylvera, BeZero, Watershed, Isometric, CTrees, Patch…) and premium B2B fintech (Stripe, Mercury, Linear, Addepar):

- **Green survives as identity only if executed with discipline.** Credible carbon-finance players avoid leafy/gradient-green branding; green works when it is deep, restrained, and doubles as the semantic "verified/on-track" state. Canopy keeps green — executed the disciplined way, not the greenwashed way.
- **The score is the hero trust object** (BeZero AAA–D). Canopy's confidence % + risk band becomes a designed **rating badge**.
- **Satellite imagery is a designed data layer, not wallpaper** (CTrees). Canopy renders the AOI as a styled evidence layer — which also sidesteps the blank-basemap tile problem.
- **Trust = transparency, not a logo wall.** Independent evidence, cited provenance, an explained rating — all of which Canopy genuinely has.
- **Craft signals funding:** one accent, light display weights, tabular numerals everywhere, hairline borders + soft shadows, strict spacing rhythm, subtle motion.

## Non-negotiable constraints

1. **No fabricated trust signals.** No fake customer logos, testimonials, SOC-2/compliance badges, or invented metrics. Credibility comes from real craft + real substance, with honest "demo / validation set / illustrative data" framing. This is a hard ethical boundary, not a stylistic one.
2. **Self-contained assets.** Fonts self-hosted (keep Geist via `next/font`, which self-hosts at build); no external CDN/webfont/image/tile dependencies (the app's browser blocks them). Decorative/evidence visuals are CSS/Canvas/SVG, not remote images.
3. **No data/behavior change.** Same routes, same API, same seed. Redesign only.
4. **Light + dark parity.** Both themes get equal care; the second theme is not a naive invert. Respect `prefers-color-scheme`, allow a manual toggle that overrides it, persist the choice.
5. **Accessibility.** WCAG-AA contrast in both themes; status never conveyed by color alone (pair with icon/label — already the pattern); visible focus states; honor `prefers-reduced-motion`.
6. **Honor the existing system.** Extend `globals.css` `@theme` tokens and the current component kit; refine, don't rip-and-replace. Follow the "NOT the Next.js you know" note in `frontend/AGENTS.md` — read the local Next 16 docs before touching framework-level code.

## Design system

### Color tokens
Defined as CSS custom properties in `globals.css`, exposed to Tailwind v4 via `@theme`. Light on `:root`; dark redefined under `@media (prefers-color-scheme: dark)` **and** `:root[data-theme="dark"]`, with `:root[data-theme="light"]` to force back. Components style through tokens only — never hard-code a hex or branch inside the media query.

**Light** — green-biased neutrals, deep-emerald accent:
- ground `#f2f5f2` · surface `#ffffff` · surface-2 `#f7faf7`
- ink `#0d1712` · ink-2 `#38473f` · muted `#61756a` · faint `#8a9c90`
- line `#e4e9e5` · line-strong `#d4ddd7`
- accent `#0a7c4c` · accent-2 `#086b41` · accent-soft `#e8f5ee` · accent-line `#b7e4cd` · accent-ink `#ffffff`

**Dark** — near-black green-black, luminous emerald:
- ground `#0a0f0d` · surface `#111814` · surface-2 `#0e1512`
- ink `#e9efe9` · ink-2 `#b7c4bc` · muted `#8ba095` · faint `#62746a`
- line `#202b25` · line-strong `#2c3b33`
- accent `#31c07a` · accent-2 `#46d18c` · accent-soft `rgba(49,192,122,.13)` · accent-line `rgba(49,192,122,.32)` · accent-ink `#04140c`

**Semantic risk ramp** (both themes; separate from the accent, keep the existing intent): low = accent-green family, med = amber (`#b45309` / dark `#e0922f`), high = red (`#b42318` / dark `#e5645a`), each with soft/line variants. Green low-risk = the brand thread.

**Elevation:** hairline 1px borders as the primary separation; shadows soft (`0 1px 2px` resting, `0 14px 34px -14px` raised light / `0 18px 44px -18px` dark). A faint accent `--glow` used only on the brand mark and the rating in dark mode.

### Typography
- Keep **Geist Sans** (grotesk, already self-hosted, premium) for UI/headings; **Geist Mono** for the instrument-panel numerals in the rating and dossier IDs.
- Weights stay light→medium (display ~560, never black); body 400; uppercase micro-labels 650 with `+0.11–0.13em` tracking.
- Scale (approx): display 34–52 · h2 22–27 · h3 15–16 · body 16 · small 13 · micro-label 11. Tighten letter-spacing as size grows (display ≈ −0.022em).
- **`font-variant-numeric: tabular-nums`** on every figure — tables, KPIs, the score, prices, coordinates. Exposed as a `.num` utility / baked into the data components so it is automatic.

### Spacing, radius, motion
- Strict 4/8px grid; generous section padding (44–76px). Radius: cards 12–14px, controls 8px, pills full-round.
- Motion subtle: 150–250ms ease-out on hover/reveal; one orchestrated moment — the confidence arc animating to its value on load; `prefers-reduced-motion` disables all of it.

### Theming mechanics
- `<html>` carries `data-theme` when the user has chosen; absence = follow `prefers-color-scheme`.
- A toggle in `TopBar` flips and persists to `localStorage`; an inline pre-hydration script sets the attribute before first paint to avoid a flash. (Verify the Next 16 approach against the local docs before implementing.)

## Signature components (the differentiators)

1. **`ConfidenceRating`** — the hero trust object. An SVG gauge (track + accent arc animating to the on-track %), the big score in Geist Mono, a risk-band chip (Low/Med/High in semantic color), and the one-line "why". Replaces/absorbs the current `RiskMeter`. Used in the hero, the portfolio, the project header, and the Confidence tab.
2. **`AoiEvidenceLayer`** — a Canvas component that renders the AOI as a designed evidence layer: procedural terrain, the located boundary polygon in accent, a measurement grid, corner ticks, a caption strip (AOI area + coordinates + source/date). Asset-type aware (solar panel-field vs mangrove canopy texture). Redraws on theme change. Used on the landing hero/product panel and the Observe/Locate tabs — and it means the product no longer depends on live map tiles for a credible visual.
3. **Evidence pipeline strip** — the disclosure→locate→observe→cross-check→confidence sequence as a 5-node connected strip (numbered, one-line each, final node accented). Used on the landing "how it works" and as an optional in-app progress rail.
4. **Refined data primitives** — `Stat`/KPI tile (micro-label → tabular value → optional delta), status **pill** (met/on-track/behind/variance mapped to the semantic ramp), `Table` with right-aligned tabular numerics + hairline rows, `TraceChip` restyled as a quiet "← source" provenance chip.

## Scope & phasing

**Phase A — Foundation.** Dark-mode token architecture in `globals.css`; theme toggle + persistence in `TopBar`; type refinements; refactor the core primitives (`Card`, `Badge`, `Table`, `Stat`, `PageHeader`, `TopBar`, `RiskMeter`, `DossierUnavailable`, `SectionNav`) to tokens + full light/dark parity. Outcome: the existing app looks refined and supports both themes, no new screens yet.

**Phase B — Signature components.** Build `ConfidenceRating`, `AoiEvidenceLayer`, the pipeline strip, refined pills/trace chips, with light/dark + reduced-motion.

**Phase C — Product-screen overhaul.** Restyle every screen using A+B: portfolio (`/`→ see IA note), `ProjectHeader`, and the dossier tabs — Disclosure, Locate, Observe, Cross-check, Confidence, Ask, Memo — with stronger hierarchy, the rating badge, the AOI evidence layer, refined tables/tiles, and finance-legible framing/descriptions on each.

**Phase D — Landing page.** A new marketing front door: hero (outcome headline + live-dossier visual with the rating + trust microline), the 5-step pipeline, a "what the rating means" explainer, the methodology/trust band (independent evidence · everything cited · one explained rating), closing CTA, footer. Honest content only.

**IA note (decision to confirm at plan time):** introduce the landing at `/` and move the portfolio to `/portfolio` (dossier routes unchanged), with the landing CTA linking into the portfolio. Alternative: keep portfolio at `/` and put the landing at `/about`. Recommendation: landing at `/`, portfolio at `/portfolio`.

Phases are sequential (A→B→C→D) but each is independently shippable and verifiable. Phase A alone already upgrades the app; the landing (D) can follow.

## Out of scope

- Live map basemap tiles / real Sentinel raster ingestion (separate data-population track; the `AoiEvidenceLayer` intentionally removes the dependency for the demo).
- Any backend/API/schema/seed change.
- New product capabilities, copy for real customers, pricing, auth flows.

## Verification / success criteria

- Both themes render every screen with AA contrast; toggle persists; no flash-of-wrong-theme; `prefers-reduced-motion` respected.
- Frontend gate green (tsc, eslint, vitest, `next build`); no new console errors.
- A live browser drive (Playwright) through the landing + both assets' tabs in **both** themes reads as a coherent, premium, finance-credible product.
- No fabricated trust signals present anywhere.
- Existing data/behavior unchanged (same API calls, same content).
