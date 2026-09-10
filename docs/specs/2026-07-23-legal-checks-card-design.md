# Legal & regulatory as an expandable card

**Date:** 2026-07-23
**Status:** Built
**Request:** Show the legal section as a card whose rows expand on click (accordion), like the
reference image.

## Starting point

Legal checks already exist end to end: `LegalCheck` model, `LegalCheckOut` schema, the API
`legal_checks[]`, the frontend `LegalCheck` type, and seed data for both assets. They rendered
as a wide five-column table at the bottom of the Cross-check screen, and two of the six fields
— `reference` and `trace` — were shown nowhere in the app.

So this is a presentation change with a real payload: the expand is what makes the dropped
provenance visible.

## Design

`frontend/src/components/features/LegalChecks.tsx` — one `Card`, one row per check, using native
`<details>/<summary>` rather than a JS accordion. Keyboard activation, the open/closed state
being announced, and rows opening independently all come from the element; there is no
open-state to manage; and an expanded row stays expanded in a screenshot or printed PDF, which
is how these dossiers circulate.

- **Collapsed** row: check type, subject, and verdict via the existing `StatusPill` +
  `crossCheckTone`, plus a chevron that rotates on open.
- **Expanded** row: the finding (`detail`), the authority with its `as_of` date, the source
  `reference`, and the `TraceChip`. The as-of date shows even when null ("as of —") — a
  register verdict means nothing without the date it reflects.
- Empty `legal_checks` renders nothing (the section, prose and card all disappear).

The card replaces the table on `crosscheck/page.tsx`; the intro prose moves onto the card.

## Honest note on the data

Across both seeded assets, most verdicts are `partially_consistent` or `insufficient_data`
("Not yet confirmed against a corporate register", "No permit register is connected"). That is
deliberate and correct — an unreachable register reads `insufficient_data`, never a reassuring
`consistent` — so the expanded rows mostly say "not checked yet", because that is the true
state.

## Tests

`LegalChecks.test.tsx`: renders every check and counts them; finding and reference are absent
while collapsed and present once expanded; an unreachable register renders as insufficient, not
consistent; the register shows its as-of date; rows open independently; empty input renders
nothing.

## Scope

1 new component + 1 test, ~40 lines removed from `crosscheck/page.tsx`, no new dependencies, no
backend change.
