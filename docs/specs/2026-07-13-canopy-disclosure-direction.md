# Canopy — Disclosure-Anchored Direction (spec + sprint build plan)

**Date:** 2026-07-13 · **Supersedes** the portfolio-monitor framing (see the New Direction Engineering Brief). **Deadline:** Wednesday — a working end-to-end *skeleton*. Demo = ~5–6 **precomputed** screens bound to the LLM, **no live processing**. Primary AOI: **Francisco Pizarro** solar (Extremadura, Spain); backup **Núñez**. Explicitly a **validation set, not production**.

## Thesis
`Disclosure → locate asset → observe (Sentinel) → cross-check vs promised → confidence + memo`, with **every figure traceable to the disclosure** (evidence graph = anti-hallucination + audit trail). Not a detection contest. The **confidence number** ("~X% on-track") is the product.

## Demo screen flow (linear narrative — replaces the portfolio grid as the spine)
1. **Disclosure** — the green-bond doc + extracted **claims** (capacity MW, area ha, financing date, promised COD/timeline). "Every number starts here."
2. **Locate** — claimed **region → located asset** on the map + a **localization confidence**. The wedge.
3. **Observe** — Sentinel **time-series build progress** (dated snapshots; the before/after/timeline).
4. **Cross-check** — **promised vs observed** table per claim (built? on schedule? at stated scale?).
5. **Score + Confidence** — headline **on-track confidence %** + risk score, each traced to evidence.
6. **Memo** — LLM-drafted; cites the disclosure + evidence nodes.

(Portfolio list survives as an entry point / validation-set switcher: Pizarro, Núñez, Nur Navoi.)

## Stub strategy (fastest path to a skeleton)
Serve the whole narrative as a **precomputed "dossier"** per project — a fixture JSON — via a read-only backend endpoint. **No new DB tables / migrations this sprint** (the DB keeps project/boundary/observations/risk as-is; the new disclosure/claims/localization/cross-check/confidence layers are served from the fixture). Luna's real evidence-graph schema + DB persistence replaces the fixture reads later.

- **`GET /projects/{id}/dossier`** → `{ disclosure, claims[], localization, observation_series[], cross_check[], confidence, memo_ready }`, read from `seed_data/projects/<id>.dossier.json` (or an extended `<id>.json`).
- Each value carries `{ source, date, method, confidence, traces_to }` (a claim id or "disclosure") — the minimal evidence-graph trace.

## Data shapes (dossier fixture)
- `disclosure`: `{ title, issuer, instrument, financing_date, doc_ref, region_hint, summary }`
- `claims[]`: `{ id, kind: capacity_mw|area_ha|cod_date|timeline_months, promised, unit, source_span }`
- `localization`: `{ region_hint, located_centroid:[lon,lat], aoi_ref, confidence, method, alternatives_rejected }`
- `observation_series[]`: `{ date, image_key, footprint_ha, ndvi, note }` (2–4 dated snapshots → the build)
- `cross_check[]`: `{ claim_id, observed, status: met|on_track|behind|variance, variance, evidence_ids }`
- `confidence`: `{ on_track_pct, rationale, drivers[] }` + existing `risk_score/band`

## Seed — Pizarro (stubbed but real-looking)
- **AOI:** approximate Francisco Pizarro PV footprint (Extremadura ~39.53, −5.72); Luna supplies the real polygon (GEM + OSM + Catastro) later.
- **Imagery:** real **Esri World Imagery** of the *actual* plant (keyless, server-side, already wired) as the Sentinel stand-in; 2–4 "dated" snapshots for the build-progress timeline (same image acceptable as a stub, flagged; real dated Sentinel from Luna replaces it).
- **Disclosure + claims:** fabricated-but-plausible green-bond claims (capacity ~590 MW, area, financing date, promised COD) — clearly a stub until real docs from Abhinav.
- **Cross-check + confidence:** derived from promised vs (stub) observed.

## Real vs stub (be explicit — it's a validation set)
- **Real now:** the asset location + Esri imagery of the real plant, the screen flow, the traceability model, the precomputed-store architecture.
- **Stub now:** disclosure doc + claims (fabricated), Sentinel time-series (Esri stand-in), localization (precomputed answer, no ML), cross-check numbers.
- **Drops in from team:** Luna → real polygons, Sentinel time-series, evidence-graph schema, cross-check + backtest. Abhinav → locate-the-asset, disclosure docs.

## Build phases
- **P1 — data + API (backend):** `<id>.dossier.json` for Pizarro (+ Núñez stub, + a Nur-Navoi dossier so the existing case fits the new shape); `GET /projects/{id}/dossier`; keep it fixture-served. Reuse the Esri fetch for real plant imagery.
- **P2 — frontend narrative:** the 6-screen linear flow + a validation-set switcher; reshape nav from "portfolio monitor" to the disclosure→confidence story. Reuse existing map/timeline/memo components.
- **P3 — truth + polish:** relabel imagery source accurately (Esri, not "Sentinel-2") until real Sentinel lands; wire real dated snapshots + real polygons as Luna delivers; on-track confidence as the headline stat.

## Non-goals (this sprint)
Live processing, real localization ML, DB migration for the new layers, sub-metre/premium, Argentina lemons, unbuilt/tranche-phased asset handling (documented boundary, not built).
