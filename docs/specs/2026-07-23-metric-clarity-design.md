# Metric clarity: hover descriptions and visible scale

**Date:** 2026-07-23
**Status:** Approved, ready to implement
**Feedback:** "Clarify risk metrics and scale. To clarify each metric add hovering description box."

## Problem

The dossier shows a dozen numbers on at least three different scales, and the page states
none of them. Three failures compound:

1. **Opposite polarity, identical colour ramp.** On the Confidence screen, on-track
   confidence (`82%`, higher is better) sits beside the risk score (`34`, higher is worse).
   Both are painted from the same green -> amber -> red tokens. A reader who does not already
   know the model cannot tell which direction is good.
2. **Band thresholds are never stated.** `Low <25 / Medium <50 / High <75 / Critical 75+`
   lives only in `canopy_pipeline/analytics/risk_scoring.py:33` (`band_for`). Nothing on screen
   says why 34 is "Medium".
3. **Two figures are silently narrower than their labels.** The Confidence screen's "Risk
   score" is the *physical-hazard composite only* (`scripts/seed.py:320`), and that composite is
   `max(fire, flood)` — not an average (`risk_scoring.py:63`). Both facts change how the number
   should be read, and neither is visible.

### Metric inventory

| Metric | Range | Direction | Screen |
| --- | --- | --- | --- |
| On-track confidence | 0-100% | higher = better | Confidence |
| Risk score | 0-100 | higher = worse | Confidence |
| Fire / Flood / Heat / Water stress / Composite | 0-100 | higher = worse | Confidence |
| Vegetation loss / Composite | 0-100 | higher = worse | Confidence |
| Localization confidence | 0-1 shown as % | higher = better | Locate |
| Avg. risk score | 0-100 | higher = worse | Portfolio |

## Known gap: heat and water stress are not scored

`PhysicalRiskOut` declares `heat` and `water_stress` (`backend/app/schemas/project.py:142-143`)
and the Confidence screen renders both rows, but no fixture supplies them
(`seed_data/projects/*.json` carry only fire, flood and composite) and no module in
`canopy_pipeline/analytics/` computes them. They always render "—".

They therefore get an honest description box stating they are not scored yet. Writing a
methodology for them would fabricate a trust signal for a metric that does not exist.

## Design

### 1. `src/lib/metrics.ts` — one registry

Every definition lives in a single typed registry, the same discipline `format.ts` applies to
colour. No definition strings scattered across pages.

```ts
export type MetricDirection = "higher-worse" | "higher-better";

export type MetricDoc = {
  label: string;
  summary: string;                 // what it means, one sentence
  scale?: {                        // absent when the pipeline does not score the metric
    min: number; max: number; unit?: string;
    direction: MetricDirection;
    bands?: string;
  };
  inputs?: string;                 // what feeds it, plus the honest caveat
};

export const METRICS: Record<MetricKey, MetricDoc>;
```

A scale carries endpoints rather than a pre-rendered string, so the `/100` a screen prints and
the "0–100" a description reads come from the same place. Three functions compose it, and
every surface that states a scale goes through one of them — otherwise the registry ends drift
between screens only to reintroduce it between formatters:

- `rangeLabel(scale)` -> `"0–100"`, `"0–100%"`
- `scaleLine(scale)` -> `"0–100 · higher = more risk"`
- `scaleNote(scale)` -> the line plus the band cutoffs, for a card footer

`RISK_BANDS` is a hand-kept copy of `risk_scoring.band_for`, which the API does not publish.
The localization cutoffs are not copied: `format.ts` owns `CONFIDENCE_HIGH` / `CONFIDENCE_MEDIUM`,
`confidenceValueTone` switches on them, and the registry renders its band string from them — so
the words in the description cannot disagree with the colour on the bar.

### 2. `src/components/ui/MetricInfo.tsx` — the hover box

A button carrying the information glyph. No new dependency: nothing is added to
`package.json`, which also keeps it clear of the CDN-blocker constraint.

- **Opens** on `mouseenter`, `focus`, and `click`/tap.
- **Closes** on `mouseleave`, `blur`, `Escape`, and outside click.
- Panel is `role="tooltip"` linked by `aria-describedby`; the trigger carries `aria-expanded`.
  Screen-reader users get the same text as sighted users.
- Flips above/below and clamps horizontally from a `getBoundingClientRect()` measurement, so a
  box on the last row of a table does not fall off the viewport.
- Renders summary -> scale line -> bands -> inputs, scale line in mono so ranges stay legible.

`MetricLabel` pairs a label with its trigger, so the ~20 call sites stay one-liners.

### 3. Visible scale cues

Hover alone is invisible on touch, in screenshots, and in exported PDFs — which is how these
dossiers get shared. Each number also carries its scale on the page.

- **Headline numbers** (Risk score, On-track confidence): the value in mono with a faint
  `/100`, and a caption stating direction (`Higher = more risk` / `Higher = better`). This is
  the pair that misleads most.
- **Hazard lists**: one shared footer per card, from `scaleNote()`. Repeating `/100` on five
  rows is noise when every row shares one scale; the per-row trigger still carries the
  specifics. `HazardList` derives the footer from the scales of the rows it was handed and
  omits it unless they agree — the list also carries rows the pipeline does not score, and a
  footer must not assert banding over numbers that aren't there.
- **Portfolio**: `Stat` takes an optional `metric`, rendering label, trigger and scale caption
  from the registry. A tile stating a scale in wording no other screen uses is then not
  expressible. Plus a trigger on the `Rating` column header.
- **Locate**: localization confidence gains `Higher = better` and the 75/50 thresholds that
  `confidenceValueTone` (`format.ts:91`) actually applies.

### 4. Coverage

| Screen | Metrics gaining a description box |
| --- | --- |
| Confidence | On-track confidence, Risk score, Fire, Flood, Heat, Water stress, both Composites, Vegetation loss, Land disturbed, Water change, Generation, Avoided emissions, Carbon stock, CO2 intensity, Assurance, Additionality |
| Portfolio | Avg. risk score, High/critical, Avoided emissions, Rating column |
| Locate | Localization confidence, AOI assurance |

### 5. Content rules

All content is derived from the scoring code. Two caveats the current UI hides go into the
boxes verbatim:

- The composite is `max(fire, flood)`, **not** an average.
- The Confidence screen's risk score is the physical-hazard composite **only** — it excludes
  the asset's impact on nature, which is scored separately and deliberately never merged
  (double materiality, `risk_scoring.py` module docstring).

No invented magnitudes, no named methodology a metric does not have.

### 6. Tests

- `MetricInfo.test.tsx` — opens on focus, closes on Escape, `aria-describedby` wiring holds.
- `metrics.test.ts` — every registry key has a summary; every scored metric declares a
  direction; the band string matches the backend cutoffs.

Both fit the existing vitest + testing-library setup.

## Scope

3 new files, 5 edited files, no new dependencies.

## Known follow-up, deliberately out of scope

`RatingExplainer.tsx` on the landing page is a second statement of what the risk bands mean.
It carries no numeric cutoffs, so it cannot drift numerically from the registry, but it
describes bands in confidence-flavoured prose while painting them with risk-band tones, and it
omits `Critical`. Folding it into the registry is a copy decision about the landing page, not
part of clarifying the dossier's metrics, so it is left for a separate change.

The registry's long-term home is the API: range, direction and cutoffs are properties of the
scorer. The frontend never *computes* a band today — the API returns `risk_band` as a string
and the registry is descriptive copy, not a second implementation — so a typed frontend file is
defensible for now. The visible leak is `heat` / `waterStress` documenting backend state
("not scored… no model is wired into the pipeline yet"): when a heat model lands, the UI keeps
saying "not scored" and nothing fails.
