# Confidence explainer as an expandable, on a shared Disclosure primitive

**Date:** 2026-07-24
**Status:** Built
**Request:** Make the description on the Confidence screen expandable, and move the description
into the card (accordion, like the legal card).

## Change

- The standalone intro paragraph at the top of the Confidence screen is removed; its short
  generic text becomes the always-visible lead-in inside the On-track confidence card.
- The long per-asset assessment (`confidence.rationale`) folds into a collapsed "What this
  rating means" toggle beneath that lead-in, so the card stays compact until someone opens it.

## Shared primitive

The legal card review flagged that the `<details>` + chevron + hover chrome should be lifted
into a shared component once a second expandable appeared. This is that second caller, so:

- `components/ui/Disclosure.tsx` — a generic `<details>/<summary>` wrapper owning only the
  chrome (chevron, marker reset, open-rotation). Padding, borders and hover are caller-supplied
  via `summaryClassName`/`bodyClassName`, because a full-width card row and a compact inline
  toggle want different spacing. `aside` slots a status pill or count before the chevron;
  `defaultOpen` forces the row open (needed for print, since a collapsed `<details>` hides its
  body in a PDF).
- `LegalChecks` refactored onto it (behaviour identical).

## Fixes folded in from the code review of this diff

- Confidence risk-score headline no longer prints "—/100" when the score is null.
- `HazardList` dedups its shared-scale footer by rendered line, not object identity.
- `Stat` passes `showScale={false}` to its label when it already prints the scale caption, so
  the scale isn't stated twice.
- `LegalChecks`: the register 'as of' date survives a null authority; the count pluralizes
  ("1 check"); rows use a content-stable key rather than the array index (native `<details>`
  state is keyed by position).
- `MetricInfo` tooltip stays open long enough to move the pointer onto the portalled panel and
  read or select its text.

## Tests

`Disclosure.test.tsx` (open/close, defaultOpen, caller classes); `MetricInfo` hover-grace
tests; `LegalChecks` pluralization and null-authority-date tests. The confidence page's
integration is covered by the Disclosure unit tests plus browser verification — the page has no
query-mock harness, and the null risk-score guard is a one-line conditional verified by
inspection.

## Scope

1 new primitive + test, `LegalChecks` refactor, Confidence page edit, plus the six review
fixes above. No backend, no new dependencies.
