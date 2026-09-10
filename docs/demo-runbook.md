# Canopy — Demo Runbook

Cold-boot the full stack from scratch and run the demo. Verified end-to-end on 2026-07-10
(DB → backend → frontend, browser→`/api`→backend proxy returning real data).

## What you're demoing

The Canopy MVP: an evidence→decision layer over a green-finance monitoring pipeline. One seeded
project — **Nur Navoi Solar (100 MW), Uzbekistan** (risk 61, band "High"). 7 screens; **5 work with
no API key**, 2 (Ask Canopy, Generate Memo) need an LLM key (see §4).

## 0. Prerequisites

- **Docker Desktop running** (the Postgres/PostGIS container).
- **`uv`** (backend Python env) and **Node/npm** (frontend) installed.
- The `docker` CLI may not be on the non-interactive PATH — it lives at
  `/Applications/Docker.app/Contents/Resources/bin/docker`. If `docker` isn't found, either open
  Docker Desktop (which adds it) or `export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"`.

**Ports (and why these, not the defaults):**

| Service  | Port | Note |
|----------|------|------|
| Postgres | **5433** | host **5432** is a pre-existing local Postgres — do not use it |
| Backend  | **8001** | host **8000** is a pre-existing server — do not use it |
| Frontend | **3000** | Next.js dev default |

## 1. Cold boot (run in order, from the repo root)

```bash
# 1) Database (waits until healthy)
docker compose up -d --wait

# 2) Migrate schema (once per fresh DB; idempotent)
cd backend && uv run alembic upgrade head

# 3) Seed the demo projects (re-runnable). Also copies the committed Wayback timelapse
#    frames from seed_data/imagery/ into the asset store, so the timeline works out of the box.
uv run python ../scripts/seed.py            # -> "seeded mikoko_pamoja (imagery complete)" (x2)

# 4) Backend API on :8001 (leave running in its own terminal)
uv run uvicorn app.main:app --port 8001

# 5) Frontend on :3000 (new terminal, from repo root)
cd frontend && npm run dev
```

Then open **http://localhost:3000**.

## 2. Health checks (paste-able)

```bash
curl -s http://localhost:8001/health                       # -> {"status":"ok"}
curl -s http://localhost:8001/projects                     # -> [ { "id":"nur_navoi_solar", ... } ]
curl -s http://localhost:3000/api/projects                 # same data THROUGH the Next proxy
curl -s http://localhost:3000/api/projects/nur_navoi_solar/metrics   # real metric rows
```

Backend routes (served at root; the frontend's `/api/*` rewrite maps onto them):
`GET /health`, `GET /projects`, `GET /projects/{id}`, `GET /projects/{id}/{boundary|evidence|imagery|metrics|observations|risk}`,
`POST /projects/{id}/ask`, `POST /projects/{id}/reports`, `GET /reports/{id}`.

## 3. Screens that work with NO key

Portfolio home, Project overview + map, Timeline (dated satellite timelapse — play/scrub), Metrics dashboard +
evidence drawer. All render from the seeded evidence store — no LLM, no CDN, no base tiles.

## 4. Ask Canopy + Generate Memo (need an LLM key)

These two screens call an OpenAI-compatible LLM. **Without a key, `POST /ask` and `POST /reports`
return a clean HTTP 503** with `code: "llm_not_configured"` and a message telling you which env vars
to set (they no longer throw an opaque 500). To enable them:

```bash
# backend/.env  (gitignored; any OpenAI-compatible endpoint — OpenAI, Anthropic-compat, Google, or a local server)
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=sk-...
LLM_MODEL=gpt-4o-mini
```

Restart the backend (step 1.4) after creating it. Guardrails are on: answers must cite stored evidence
IDs and refuse legal/audit/carbon-verification/investment-advice claims.

## 5. Demo click-path (~90 seconds)

1. **Portfolio home** (`/`) — the Nur Navoi Solar card, risk **61 / High**.
2. **Open the project** — Overview + MapLibre map (georeferenced RGB/overlay imagery pinned to the AOI
   boundary; no base tiles).
3. **Timeline** — press play (or scrub the slider) to watch the dated satellite timelapse; for Nur Navoi the solar panels appear across the frames (desert → array).
4. **Metrics** — dashboard; click a metric (e.g. `vegetation_change_percent = 34.1`) → the **evidence
   drawer** traces it to its stored observation. This is the pitch: every number is evidence-backed.
5. **Ask Canopy** *(key required)* — ask "What's the risk?"; get an evidence-cited answer.
6. **Generate Memo** *(key required)* — produce the finance memo draft.

## 6. Known rough edges (be aware during a live demo)

- **Ask/Memo need a key** — without `backend/.env` they return a clean 503 (`llm_not_configured`),
  not a crash; still, set the key or avoid those two screens for a keyless demo. A *wrong* key
  currently still surfaces a 500 (upstream 401) — only the unconfigured case is handled gracefully.
- **Single project** — the portfolio is one card; there's no cross-project comparison story yet.
- Seed is re-runnable, so a botched DB can be reset with steps 1.1–1.3.

## 7. Teardown

```bash
# stop the two dev servers with Ctrl-C in their terminals, then:
docker compose stop        # keep the data (fast restart next time)
# or
docker compose down -v     # wipe the DB volume (next boot re-migrates + re-seeds)
```
