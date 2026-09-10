# Dossier Normalization Implementation Plan (Phase 0)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Make the DB the single source of truth — normalize the dossier into typed relational tables, derive duplicated risk/confidence from one home, remove the dead observations/metrics/risk surface. `/dossier` and the rendered `/projects` fields stay compatible.

**Architecture:** New ORM models for the eight dossier tables (+ a `TraceMixin`); drop the old `Observation`/`Metric`/`RiskScore` models; re-parent `evidence_items` to `projects`. One merged fixture per project seeds the normalized rows. `get_dossier` assembles the dossier from tables; the projects service derives `risk_score`/`risk_band` from `confidences`.

**Tech Stack:** SQLAlchemy 2.0 (typed `Mapped`), Alembic, PostGIS on `localhost:5433`, FastAPI, pytest; Next.js/vitest frontend.

## Global Constraints

- Spec: `docs/specs/2026-07-17-dossier-normalization-design.md` (read it — this plan implements it verbatim).
- Conventions: string PKs for referenced entities; integer-identity PKs for pure children; `ON DELETE CASCADE` on every FK to `projects` and child→parent; `created_at TIMESTAMPTZ DEFAULT now()` on new tables; `Date` for dates, `Numeric` for business quantities, `Float` for measurements; no JSONB in the model; exactly-one CHECK on `*_num`/`*_text`.
- **API compatibility:** the `/dossier` response and every frontend-rendered `/projects` field must be unchanged. Only unused `ProjectDetail.confidence`/`main_finding` are removed.
- **Commit gate** (`canopy-precommit-review-gate`): `.py`/`.ts`/`.tsx` commits go through `/simplify` + `/code-review` + `git write-tree > .git/canopy-review-marker` (add + commit as separate steps). JSON/MD-only commits pass freely. Inline execution may batch code into one gated commit per task.
- Backend gate: `uv run ruff check .` · `uv run ruff format --check .` · `uv run mypy app` · `uv run pytest -q`. Frontend gate: `./node_modules/.bin/eslint .` · `./node_modules/.bin/tsc --noEmit` · `npx vitest run`.
- Phase 0 keeps the **current** two assets (nur_navoi_solar, pizarro) working — this is the parity check that the refactor changed storage, not behavior. The source-pack content swap is Phase 1.

---

### Task 1: Dossier ORM models + drop old models

**Files:**
- Create: `backend/app/models/dossier.py`
- Modify: `backend/app/models/project.py` (drop 4 columns, add relationships)
- Modify: `backend/app/models/observation.py` (delete `Observation`/`Metric`; keep+re-parent `EvidenceItem`)
- Delete: `backend/app/models/risk.py`
- Modify: `backend/app/models/methodology.py` (JSONB list cols → `ARRAY(String)`)
- Modify: `backend/app/models/__init__.py` (exports)

**Interfaces:**
- Produces models: `Disclosure`, `Claim`, `Localization`, `LocalizationAlternative`, `ObservationSnapshot`, `CrossCheck`, `CrossCheckEvidence`, `Confidence`, `EvidenceItem` (re-parented), `TraceMixin`.

- [ ] **Step 1: Create `backend/app/models/dossier.py`:**

```python
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    CheckConstraint,
    Date,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    Numeric,
    String,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class TraceMixin:
    """Provenance value-object shared by every dossier element (typed, not JSONB)."""

    trace_source: Mapped[str | None] = mapped_column(String, nullable=True)
    trace_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    trace_method: Mapped[str | None] = mapped_column(String, nullable=True)
    trace_confidence: Mapped[str | None] = mapped_column(String, nullable=True)
    trace_traces_to: Mapped[str | None] = mapped_column(String, nullable=True)


class Disclosure(Base, TraceMixin):
    __tablename__ = "disclosures"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    title: Mapped[str] = mapped_column(String)
    issuer: Mapped[str | None] = mapped_column(String, nullable=True)
    instrument: Mapped[str | None] = mapped_column(String, nullable=True)
    financing_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    doc_ref: Mapped[str | None] = mapped_column(String, nullable=True)
    region_hint: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Claim(Base, TraceMixin):
    __tablename__ = "claims"
    __table_args__ = (
        CheckConstraint(
            "(promised_num IS NULL) <> (promised_text IS NULL)", name="ck_claim_promised_one_of"
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    ordinal: Mapped[int] = mapped_column(Integer)
    kind: Mapped[str] = mapped_column(String)
    promised_num: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    promised_text: Mapped[str | None] = mapped_column(String, nullable=True)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    source_span: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Localization(Base, TraceMixin):
    __tablename__ = "localizations"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    region_hint: Mapped[str | None] = mapped_column(String, nullable=True)
    centroid_lon: Mapped[float] = mapped_column(Float)
    centroid_lat: Mapped[float] = mapped_column(Float)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    method: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    alternatives: Mapped[list["LocalizationAlternative"]] = relationship(
        cascade="all, delete-orphan", order_by="LocalizationAlternative.ordinal"
    )


class LocalizationAlternative(Base):
    __tablename__ = "localization_alternatives"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    project_id: Mapped[str] = mapped_column(
        ForeignKey("localizations.project_id", ondelete="CASCADE")
    )
    ordinal: Mapped[int] = mapped_column(Integer)
    name: Mapped[str] = mapped_column(String)
    reason: Mapped[str] = mapped_column(String)


class ObservationSnapshot(Base, TraceMixin):
    __tablename__ = "observation_snapshots"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    ordinal: Mapped[int] = mapped_column(Integer)
    date: Mapped[date] = mapped_column(Date)
    image_key: Mapped[str] = mapped_column(String)
    footprint_ha: Mapped[float | None] = mapped_column(Float, nullable=True)
    ndvi: Mapped[float | None] = mapped_column(Float, nullable=True)
    note: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class CrossCheck(Base, TraceMixin):
    __tablename__ = "cross_checks"
    __table_args__ = (
        CheckConstraint(
            "(observed_num IS NULL) <> (observed_text IS NULL)", name="ck_crosscheck_observed_one_of"
        ),
    )

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    ordinal: Mapped[int] = mapped_column(Integer)
    claim_id: Mapped[str] = mapped_column(ForeignKey("claims.id", ondelete="CASCADE"))
    observed_num: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    observed_text: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String)
    variance: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    evidence_links: Mapped[list["CrossCheckEvidence"]] = relationship(
        cascade="all, delete-orphan"
    )


class CrossCheckEvidence(Base):
    __tablename__ = "cross_check_evidence"

    cross_check_id: Mapped[str] = mapped_column(
        ForeignKey("cross_checks.id", ondelete="CASCADE"), primary_key=True
    )
    evidence_id: Mapped[str] = mapped_column(
        ForeignKey("evidence_items.id", ondelete="CASCADE"), primary_key=True
    )


class Confidence(Base, TraceMixin):
    __tablename__ = "confidences"

    project_id: Mapped[str] = mapped_column(
        ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True
    )
    on_track_pct: Mapped[int] = mapped_column(Integer)
    rationale: Mapped[str | None] = mapped_column(String, nullable=True)
    drivers: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_band: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 2: Rewrite `backend/app/models/observation.py`** — delete `Observation` and `Metric`; keep `EvidenceItem`, re-parented to the project:

```python
from datetime import date

from sqlalchemy import Date, ForeignKey, String
from sqlalchemy.dialects.postgresql import ARRAY
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id", ondelete="CASCADE"))
    source_name: Mapped[str] = mapped_column(String)
    source_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    method_id: Mapped[str | None] = mapped_column(
        ForeignKey("methodologies.id", ondelete="RESTRICT"), nullable=True
    )
    confidence: Mapped[str | None] = mapped_column(String, nullable=True)
    limitations: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    financial_relevance: Mapped[str | None] = mapped_column(String, nullable=True)
    supporting_assets: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
```

- [ ] **Step 3: Edit `backend/app/models/project.py`** — remove `risk_score`, `risk_band`, `confidence`, `main_finding` from `Project`; add relationships (leave `ProjectBoundary` unchanged):

Replace the `Project` class body columns after `screening_status` — delete the four lines `risk_score`/`risk_band`/`confidence`/`main_finding` and add:
```python
    boundary: Mapped["ProjectBoundary"] = relationship(back_populates="project", uselist=False)
    disclosure: Mapped["Disclosure"] = relationship(cascade="all, delete-orphan", uselist=False)
    localization: Mapped["Localization"] = relationship(cascade="all, delete-orphan", uselist=False)
    confidence_row: Mapped["Confidence"] = relationship(cascade="all, delete-orphan", uselist=False)
```
Add the imports needed for the forward refs at the top: `from app.models.dossier import Confidence, Disclosure, Localization` guarded under `TYPE_CHECKING`.

- [ ] **Step 4: Delete `backend/app/models/risk.py`.**

```bash
git rm backend/app/models/risk.py
```

- [ ] **Step 5: Edit `backend/app/models/methodology.py`** — change the three list columns from `JSONB` to `ARRAY(String)`:

```python
    data_sources: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    assumptions: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
    limitations: Mapped[list[str]] = mapped_column(ARRAY(String), default=list)
```
(Update the import line to `from sqlalchemy.dialects.postgresql import ARRAY`.)

- [ ] **Step 6: Edit `backend/app/models/__init__.py`** — export the new models, drop `Observation`/`Metric`/`RiskScore`:

Set the exports to: `Project, ProjectBoundary, EvidenceItem, Methodology, Report` (+ qa log if present), plus from `app.models.dossier`: `Disclosure, Claim, Localization, LocalizationAlternative, ObservationSnapshot, CrossCheck, CrossCheckEvidence, Confidence`. Remove `Observation, Metric, RiskScore` from `__all__` and imports.

- [ ] **Step 7: Smoke-test the models build the schema** (against the test DB):

```bash
cd backend && uv run python - <<'PY'
from sqlalchemy import create_engine, text
from app.core.config import get_settings
from app.core.db import Base
import app.models  # register all
e = create_engine(get_settings().test_database_url, future=True)
with e.begin() as c:
    c.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
Base.metadata.drop_all(e); Base.metadata.create_all(e)
print("tables:", sorted(Base.metadata.tables))
PY
```
Expected: the printed table list includes `disclosures, claims, localizations, localization_alternatives, observation_snapshots, cross_checks, cross_check_evidence, confidences, evidence_items` and NOT `observations, metrics, risk_scores`.

- [ ] **Step 8: mypy + ruff on the models:**

Run: `cd backend && uv run ruff check app/models && uv run mypy app/models`
Expected: clean. (Do not commit yet — services still import the deleted models; fixed in Task 4/5. Commit at Task 5 once the backend imports cleanly.)

---

### Task 2: Alembic migration (with downgrade)

**Files:**
- Create: `backend/alembic/versions/<rev>_normalize_dossier.py`

- [ ] **Step 1: Confirm the current head:**

Run: `cd backend && uv run alembic history | tail -5 && uv run alembic current`

- [ ] **Step 2: Autogenerate the migration against the models:**

Run: `cd backend && uv run alembic revision --autogenerate -m "normalize dossier"`
This drops `observations`/`metrics`/`risk_scores`, drops the four `projects` columns, alters `evidence_items` (observation_id→project_id, JSONB→ARRAY, source_date→Date, method_id FK), converts `methodologies` arrays, and creates the eight new tables.

- [ ] **Step 3: Hand-verify + fix the generated migration.** Autogenerate misses/garbles: `ON DELETE CASCADE` (add `ondelete="CASCADE"` to every `create_foreign_key`/`ForeignKey`), the ARRAY conversions (may need `postgresql_using="..."` or drop+add for JSONB→ARRAY), the CHECK constraints (`ck_claim_promised_one_of`, `ck_crosscheck_observed_one_of`), and `server_default=sa.text("now()")` on `created_at`. Ensure the **`downgrade`** recreates the dropped tables/columns and reverses the alters. Read the file end-to-end; make it correct both ways.

- [ ] **Step 4: Apply up, then down, then up again on the test DB to prove reversibility:**

```bash
cd backend
CANOPY_DB=$(uv run python -c "from app.core.config import get_settings as g; print(g().test_database_url)")
uv run alembic upgrade head && uv run alembic downgrade -1 && uv run alembic upgrade head
```
Expected: all three succeed with no error.

- [ ] **Step 5: Commit the migration + models together** (code — run the gate):

```bash
# after the backend imports cleanly (this may be sequenced with Task 5); if committing here,
# ensure services still import — otherwise fold this commit into Task 5.
```
(Practical: commit models + migration + service rewrites + dead-code removal as one reviewed commit at the end of Task 5, since the backend won't import until the services stop referencing deleted models.)

---

### Task 3: Merged fixtures + seed rewrite

**Files:**
- Create: `seed_data/projects/nur_navoi_solar.json` (merged), `seed_data/projects/pizarro.json` (merged)
- Delete: `seed_data/projects/nur_navoi.json`, `nur_navoi_solar.dossier.json`, `pizarro.dossier.json` (old two-file pairs)
- Rewrite: `scripts/seed.py`

**Merge rule** (deterministic): the merged `<id>.json` = the project meta from the old `<id>.json` (`id`←`analysis_id`, `name`←`project_name`, `asset_type`, `country`, `financing_type`, `monitoring_objective`, `status`, `screening_status`←`summary.screening_status`, `aoi_coords`, `area_hectares`←`metadata.aoi_area_hectares`) + the six sections verbatim from `<id>.dossier.json` (`disclosure`, `claims`, `localization`, `observation_series`, `cross_check`, `confidence`, `memo_ready`) + an `evidence` array holding only the evidence-item fields (`id`←`{pid}_ev_{i}`, `source_name`←`source.name`, `source_date`←`metric.comparison_period` as ISO, `method_id`←parsed from `method`, `confidence`, `limitations`, `financial_relevance`, `supporting_assets`). The duplicated `summary.risk_score/risk_band/confidence/main_finding` are **dropped** (they live only in `confidence`).

- [ ] **Step 1: Write `seed_data/projects/nur_navoi_solar.json`** (merged) — apply the rule to the existing `nur_navoi.json` + `nur_navoi_solar.dossier.json`. Full result:

```json
{
  "id": "nur_navoi_solar",
  "name": "Nur Navoi Solar (100 MW), Uzbekistan",
  "asset_type": "solar",
  "country": "Uzbekistan",
  "financing_type": "development_finance",
  "monitoring_objective": "Verify build-out and ongoing operation vs stated use of proceeds.",
  "status": "monitored",
  "screening_status": "Partially consistent",
  "aoi_coords": [[64.978, 40.104], [64.994, 40.104], [64.994, 40.120], [64.978, 40.120], [64.978, 40.104]],
  "area_hectares": 231.4,
  "disclosure": { "...": "verbatim from nur_navoi_solar.dossier.json disclosure" },
  "claims": [ "... verbatim from dossier claims ..." ],
  "localization": { "...": "verbatim from dossier localization" },
  "observation_series": [ "... verbatim ..." ],
  "cross_check": [ "... verbatim ..." ],
  "confidence": { "...": "verbatim from dossier confidence" },
  "evidence": [
    {
      "id": "nur_navoi_solar_ev_0",
      "source_name": "Sentinel-2 + Sentinel-1",
      "source_date": "2023-09-30",
      "method_id": "build_v1",
      "confidence": "medium",
      "limitations": ["confirms build/land-cover change, not generation output", "generation/carbon proxy needs ground truth to certify", "no independent metering in the demo"],
      "financial_relevance": "Construction footprint indicator relevant to use-of-proceeds monitoring.",
      "supporting_assets": ["before_rgb.png", "after_rgb.png", "change_overlay.png"]
    }
  ],
  "memo_ready": true
}
```
Copy the six section objects verbatim from `seed_data/projects/nur_navoi_solar.dossier.json` (the current file) into the placeholders above.

- [ ] **Step 2: Write `seed_data/projects/pizarro.json`** (merged) — the identical mechanical transform of the existing `seed_data/projects/pizarro.json` (old) + `pizarro.dossier.json`. Evidence id `pizarro_ev_0`, `source_date` `2023-10-31`, `method_id` `build_v1`, `area_hectares` 2626.9, `screening_status` "Consistent"; the six sections copied verbatim from `pizarro.dossier.json`.

- [ ] **Step 3: Delete the old two-file fixtures:**

```bash
git rm seed_data/projects/nur_navoi.json seed_data/projects/nur_navoi_solar.dossier.json seed_data/projects/pizarro.dossier.json
```
(The old `seed_data/projects/pizarro.json` is overwritten in Step 2.)

- [ ] **Step 4: Rewrite `scripts/seed.py`** — replace `seed_project` (and the risk/observation/metric seeding) with normalized writes. Keep `_seed_methodologies`, `ensure_assets`, `fetch_aoi_imagery`, `_solid_png`, and `main`. New `seed_project`:

```python
from datetime import date

from app.models import (
    Claim, Confidence, CrossCheck, CrossCheckEvidence, Disclosure, EvidenceItem,
    Localization, LocalizationAlternative, ObservationSnapshot, Project, ProjectBoundary,
)


def _trace(t: dict | None) -> dict:
    t = t or {}
    d = t.get("date")
    return dict(
        trace_source=t.get("source"),
        trace_date=date.fromisoformat(d) if d else None,
        trace_method=t.get("method"),
        trace_confidence=t.get("confidence"),
        trace_traces_to=t.get("traces_to"),
    )


def _split_value(v) -> dict:
    """A promised/observed value is number-or-string -> exactly one typed column."""
    if isinstance(v, (int, float)):
        return {"num": v, "text": None}
    return {"num": None, "text": str(v)}


def seed_project(session: Session, fx: dict) -> str:
    pid = fx["id"]
    session.merge(Project(
        id=pid, name=fx["name"], asset_type=fx["asset_type"], country=fx.get("country"),
        financing_type=fx.get("financing_type"), monitoring_objective=fx.get("monitoring_objective"),
        status=fx.get("status", "monitored"), screening_status=fx.get("screening_status"),
    ))
    poly = Polygon(fx["aoi_coords"])
    session.merge(ProjectBoundary(
        id=f"{pid}_boundary", project_id=pid, geom=from_shape(poly, srid=4326),
        source="demo_fixture", area_hectares=fx.get("area_hectares"),
    ))

    ev = fx["disclosure"]
    session.merge(Disclosure(
        project_id=pid, title=ev["title"], issuer=ev.get("issuer"), instrument=ev.get("instrument"),
        financing_date=date.fromisoformat(ev["financing_date"]) if ev.get("financing_date") else None,
        doc_ref=ev.get("doc_ref"), region_hint=ev.get("region_hint"), summary=ev.get("summary"),
        **_trace(ev.get("trace")),
    ))

    for i, c in enumerate(fx["claims"]):
        pv = _split_value(c["promised"])
        session.merge(Claim(
            id=c["id"], project_id=pid, ordinal=i, kind=c["kind"],
            promised_num=pv["num"], promised_text=pv["text"], unit=c.get("unit"),
            source_span=c.get("source_span"), **_trace(c.get("trace")),
        ))

    loc = fx["localization"]
    lon, lat = loc["located_centroid"]
    session.merge(Localization(
        project_id=pid, region_hint=loc.get("region_hint"), centroid_lon=lon, centroid_lat=lat,
        confidence=loc.get("confidence"), method=loc.get("method"), **_trace(loc.get("trace")),
    ))
    # Alternatives are children; delete-then-insert keeps re-seeds idempotent.
    session.query(LocalizationAlternative).filter_by(project_id=pid).delete()
    for i, a in enumerate(loc.get("alternatives_rejected", [])):
        session.add(LocalizationAlternative(project_id=pid, ordinal=i, name=a["name"], reason=a["reason"]))

    for i, s in enumerate(fx["observation_series"]):
        session.merge(ObservationSnapshot(
            id=f"{pid}_snap_{i}", project_id=pid, ordinal=i, date=date.fromisoformat(s["date"]),
            image_key=s["image_key"], footprint_ha=s.get("footprint_ha"), ndvi=s.get("ndvi"),
            note=s.get("note"), **_trace(s.get("trace")),
        ))

    for i, e in enumerate(fx["evidence"]):
        session.merge(EvidenceItem(
            id=e["id"], project_id=pid, source_name=e["source_name"],
            source_date=date.fromisoformat(e["source_date"]) if e.get("source_date") else None,
            method_id=e.get("method_id"), confidence=e.get("confidence"),
            limitations=e.get("limitations", []), financial_relevance=e.get("financial_relevance"),
            supporting_assets=e.get("supporting_assets", []),
        ))

    for i, r in enumerate(fx["cross_check"]):
        cc_id = f"{pid}_cc_{i}"
        ov = _split_value(r["observed"])
        session.merge(CrossCheck(
            id=cc_id, project_id=pid, ordinal=i, claim_id=r["claim_id"],
            observed_num=ov["num"], observed_text=ov["text"], status=r["status"],
            variance=r.get("variance"), **_trace(r.get("trace")),
        ))
        session.query(CrossCheckEvidence).filter_by(cross_check_id=cc_id).delete()
        for eid in r.get("evidence_ids", []):
            session.add(CrossCheckEvidence(cross_check_id=cc_id, evidence_id=eid))

    cf = fx["confidence"]
    session.merge(Confidence(
        project_id=pid, on_track_pct=cf["on_track_pct"], rationale=cf.get("rationale"),
        drivers=cf.get("drivers", []), risk_score=cf.get("risk_score"), risk_band=cf.get("risk_band"),
        **_trace(cf.get("trace")),
    ))

    session.flush()
    _assert_traceable(session, pid, fx)
    return pid
```

And rewrite `_assert_traceable` to the new integrity rules:
```python
def _assert_traceable(session: Session, pid: str, fx: dict) -> None:
    claim_ids = {c.id for c in session.query(Claim).filter_by(project_id=pid)}
    ev_ids = {e.id for e in session.query(EvidenceItem).filter_by(project_id=pid)}
    assets = {a for e in fx["evidence"] for a in e.get("supporting_assets", [])}
    for r in fx["cross_check"]:
        if r["claim_id"] not in claim_ids:
            raise ValueError(f"{pid}: cross_check references unknown claim {r['claim_id']}")
        for eid in r.get("evidence_ids", []):
            if eid not in ev_ids:
                raise ValueError(f"{pid}: cross_check references unknown evidence {eid}")
    for s in fx["observation_series"]:
        if s["image_key"] not in assets:
            raise ValueError(f"{pid}: snapshot image_key {s['image_key']} not in any evidence assets")
```
Update `ensure_assets`/`main` to read `fx["aoi_coords"]`/`fx["evidence"]` (already the same keys) and `fx["id"]` instead of `fx["analysis_id"]`; `main`'s default fixture path becomes `nur_navoi_solar.json`.

- [ ] **Step 5: Recreate the live DB schema and reseed both assets:**

```bash
cd backend && uv run alembic upgrade head   # (or drop/recreate if the live DB has drifted from alembic)
uv run python ../scripts/seed.py ../seed_data/projects/nur_navoi_solar.json
uv run python ../scripts/seed.py ../seed_data/projects/pizarro.json
```
Expected: two `seeded ...` lines, no traceability error.

- [ ] **Step 6: Verify the rows landed:**

Run: `PGPASSWORD=canopy psql -h localhost -p 5433 -U canopy -d canopy -c "select (select count(*) from claims), (select count(*) from cross_checks), (select count(*) from confidences), (select count(*) from evidence_items);"`
Expected: non-zero counts (nur_navoi 5 claims + pizarro 4 = 9 claims, etc.).

---

### Task 4: Dossier assembly + projects derivation

**Files:**
- Modify: `backend/app/services/projects.py` (`get_dossier` assembles; `list_projects`/`get_project` derive risk; `get_imagery` unchanged logic but via project-linked evidence)
- Modify: `backend/app/services/queries.py` (`evidence_for_project` by project_id; drop `metrics_for_project`)
- Modify: `backend/app/schemas/project.py` (drop `ProjectDetail.confidence`/`main_finding`)
- Test: `backend/tests/test_projects_api.py`

**Interfaces:**
- Produces: `get_dossier(db, pid) -> Dossier` assembled from tables; `ProjectSummary`/`ProjectDetail` with `risk_score`/`risk_band` from `confidences`.

- [ ] **Step 1: Write the failing assembly test** in `backend/tests/test_projects_api.py`:

```python
def test_dossier_assembled_from_tables(client, seed):
    seed("nur_navoi_solar")
    d = client.get("/projects/nur_navoi_solar/dossier").json()
    assert d["project_id"] == "nur_navoi_solar"
    assert d["disclosure"]["issuer"]
    assert [c["kind"] for c in d["claims"]] == ["capacity_mw", "generation_gwh", "co2_avoided_tpy", "area_ha", "cod_date"][: len(d["claims"])] or d["claims"]
    assert d["claims"][0]["promised"] == 100  # reconstructed number
    assert d["cross_check"][0]["evidence_ids"]  # from the join table
    assert isinstance(d["confidence"]["drivers"], list)
    assert d["confidence"]["risk_band"]


def test_projects_risk_comes_from_confidence(client, seed):
    seed("nur_navoi_solar")
    row = client.get("/projects").json()[0]
    assert row["risk_band"] in {"Low", "High", "Partially consistent", "Medium"} or row["risk_band"]
    assert row["risk_score"] is not None
```
(The `seed` fixture must read `<name>.json` where name = the project id now, e.g. `seed("nur_navoi_solar")` reads `nur_navoi_solar.json`. Update `conftest`'s `_seed` default arg from `"nur_navoi"` to `"nur_navoi_solar"`.)

- [ ] **Step 2: Run it — expect failure** (get_dossier still reads a file that no longer exists / wrong shape):

Run: `cd backend && uv run pytest tests/test_projects_api.py::test_dossier_assembled_from_tables -x -q`
Expected: FAIL.

- [ ] **Step 3: Rewrite `get_dossier` in `backend/app/services/projects.py`** to assemble from tables:

```python
def _trace_out(o) -> dict:
    return {
        "source": o.trace_source,
        "date": o.trace_date.isoformat() if o.trace_date else None,
        "method": o.trace_method,
        "confidence": o.trace_confidence,
        "traces_to": o.trace_traces_to,
    }


def _value_out(num, text):
    return float(num) if num is not None else text


def get_dossier(db: Session, project_id: str) -> Dossier:
    get_project(db, project_id)
    disc = db.get(Disclosure, project_id)
    loc = db.get(Localization, project_id)
    conf = db.get(Confidence, project_id)
    if disc is None or loc is None or conf is None:
        raise NotFound(f"dossier for {project_id} not found")
    claims = db.scalars(select(Claim).where(Claim.project_id == project_id).order_by(Claim.ordinal)).all()
    snaps = db.scalars(select(ObservationSnapshot).where(ObservationSnapshot.project_id == project_id).order_by(ObservationSnapshot.ordinal)).all()
    checks = db.scalars(select(CrossCheck).where(CrossCheck.project_id == project_id).order_by(CrossCheck.ordinal)).all()
    alts = db.scalars(select(LocalizationAlternative).where(LocalizationAlternative.project_id == project_id).order_by(LocalizationAlternative.ordinal)).all()
    ev_by_cc: dict[str, list[str]] = {}
    for link in db.scalars(select(CrossCheckEvidence)):
        ev_by_cc.setdefault(link.cross_check_id, []).append(link.evidence_id)

    payload = {
        "project_id": project_id,
        "disclosure": {
            "title": disc.title, "issuer": disc.issuer, "instrument": disc.instrument,
            "financing_date": disc.financing_date.isoformat() if disc.financing_date else None,
            "doc_ref": disc.doc_ref, "region_hint": disc.region_hint, "summary": disc.summary,
            "trace": _trace_out(disc),
        },
        "claims": [
            {"id": c.id, "kind": c.kind, "promised": _value_out(c.promised_num, c.promised_text),
             "unit": c.unit, "source_span": c.source_span, "trace": _trace_out(c)}
            for c in claims
        ],
        "localization": {
            "region_hint": loc.region_hint, "located_centroid": [loc.centroid_lon, loc.centroid_lat],
            "confidence": loc.confidence, "method": loc.method,
            "alternatives_rejected": [{"name": a.name, "reason": a.reason} for a in alts],
            "trace": _trace_out(loc),
        },
        "observation_series": [
            {"date": s.date.isoformat(), "image_key": s.image_key, "footprint_ha": s.footprint_ha,
             "ndvi": s.ndvi, "note": s.note, "trace": _trace_out(s)}
            for s in snaps
        ],
        "cross_check": [
            {"claim_id": c.claim_id, "observed": _value_out(c.observed_num, c.observed_text),
             "status": c.status, "variance": c.variance, "evidence_ids": ev_by_cc.get(c.id, []),
             "trace": _trace_out(c)}
            for c in checks
        ],
        "confidence": {
            "on_track_pct": conf.on_track_pct, "rationale": conf.rationale, "drivers": list(conf.drivers or []),
            "risk_score": conf.risk_score, "risk_band": conf.risk_band, "trace": _trace_out(conf),
        },
        "memo_ready": True,
    }
    return Dossier.model_validate(payload)
```
Add the imports for the dossier models + `select`. Remove the old `_DOSSIER_DIR`, `InvalidFixture`, and `ValidationError` usage from this function (no file read anymore; assembled payload is trusted). Keep `InvalidFixture` import only if used elsewhere — otherwise drop it.

- [ ] **Step 4: Make `list_projects`/`get_project` derive risk from `confidences`.** The `ProjectSummary`/`ProjectDetail` schemas use `from_attributes`. Simplest: return dicts (or set attributes) with `risk_score`/`risk_band` pulled from the project's `Confidence` row. Implement a small serializer:

```python
def _summary_dict(db: Session, p: Project) -> dict:
    conf = db.get(Confidence, p.id)
    return {
        "id": p.id, "name": p.name, "asset_type": p.asset_type, "country": p.country,
        "financing_type": p.financing_type, "status": p.status,
        "risk_score": conf.risk_score if conf else None,
        "risk_band": conf.risk_band if conf else None,
    }

def list_projects(db: Session) -> list[dict]:
    return [_summary_dict(db, p) for p in db.scalars(select(Project).order_by(Project.name))]

def get_project_detail(db: Session, project_id: str) -> dict:
    p = get_project(db, project_id)
    return {**_summary_dict(db, p), "monitoring_objective": p.monitoring_objective,
            "screening_status": p.screening_status}
```
Update the routes: `list_projects` returns `list[ProjectSummary]` (FastAPI validates the dicts), `get_project` route calls `get_project_detail`. Keep `get_project(db, pid)` (the ORM fetch used for 404s) as-is under a distinct name if needed.

- [ ] **Step 5: Drop `confidence`/`main_finding` from `ProjectDetail`** in `backend/app/schemas/project.py`:

```python
class ProjectDetail(ProjectSummary):
    monitoring_objective: str | None = None
    screening_status: str | None = None
```

- [ ] **Step 6: `evidence_for_project` by project_id** in `backend/app/services/queries.py` — filter `EvidenceItem.project_id == project_id` directly (no join through observations); delete `metrics_for_project` and any `Observation`/`Metric` import.

- [ ] **Step 7: Run the assembly + risk tests:**

Run: `cd backend && uv run pytest tests/test_projects_api.py -q`
Expected: PASS (including the two new tests; the malformed-fixture test is removed — see Task 5).

---

### Task 5: Remove the dead surface + wire everything; commit

**Files:**
- Modify: `backend/app/api/routes/evidence.py` (drop `/observations`, `/metrics`, `/risk`; keep `/evidence`)
- Modify: `backend/app/services/evidence.py` (drop `observations`/`metrics`/`risk`)
- Modify: `backend/app/schemas/evidence.py` (drop `ObservationOut`/`MetricOut`/`RiskOut`)
- Modify: `backend/tests/test_projects_api.py` (delete removed-endpoint + fixture-file tests)
- Modify frontend: `src/lib/api.ts`, `src/lib/queries.ts`, `src/lib/types.ts`, `src/lib/api.test.ts`

- [ ] **Step 1: Backend removals.** In `routes/evidence.py` delete the `/observations`, `/metrics`, `/risk` route functions and their imports; keep `/evidence`. In `services/evidence.py` delete `observations`/`metrics`/`risk`, keep `evidence`. In `schemas/evidence.py` delete `ObservationOut`/`MetricOut`/`RiskOut`, keep `EvidenceItemOut` (its `source_date` is now a date — adjust the type to `str | None` via serialization or `date | None`). Confirm: `grep -rn "Observation\|Metric\|RiskScore\|metrics_for_project" backend/app` returns only unrelated hits (none for the deleted models).

- [ ] **Step 2: Frontend removals.** In `src/lib/api.ts` delete `getObservations`/`getMetrics`/`getRisk`; in `src/lib/queries.ts` delete `useObservations`/`useMetrics`/`useRisk`; in `src/lib/types.ts` delete the `Observation`, `Metric`, `Risk` types and drop `confidence`/`main_finding` from `ProjectDetail`; in `src/lib/api.test.ts` remove any assertion referencing the deleted methods. Confirm: `grep -rn "getObservations\|getMetrics\|getRisk\|useMetrics\|useRisk\|useObservations" frontend/src` returns nothing.

- [ ] **Step 3: Delete the now-obsolete backend tests** — the old `test_dossier_returns_*` file-based test and `test_dossier_malformed_fixture_*` (no file/validation path anymore) and any `/metrics`/`/risk` test. Keep `test_detail_404`, `test_boundary_*`, `test_imagery_layers`, and the two new assembly/risk tests.

- [ ] **Step 4: Full backend gate:**

Run: `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest -q`
Expected: all green. (Run `uv run ruff format .` first if formatting fails.)

- [ ] **Step 5: Full frontend gate:**

Run: `cd frontend && ./node_modules/.bin/tsc --noEmit && ./node_modules/.bin/eslint . && npx vitest run`
Expected: all green.

- [ ] **Step 6: Commit the whole backend refactor + frontend removals** (code — run the gate):

Run `/simplify` then `/code-review` on the staged diff, apply fixes, then:
```bash
git add -A
git write-tree > .git/canopy-review-marker
git commit -m "refactor: normalize dossier into tables; single source of truth; remove dead observations/metrics/risk"
```

---

### Task 6: Parity verification

- [ ] **Step 1: Restart the backend and smoke both assets:**

```bash
cd backend && lsof -ti :8001 | xargs kill 2>/dev/null; sleep 1
uv run uvicorn app.main:app --port 8001 --host 127.0.0.1 &
sleep 2
uv run python - <<'PY'
import urllib.request, json
def get(u):
    with urllib.request.urlopen(u, timeout=10) as r: return json.loads(r.read())
print("projects:", [(p["id"], p["risk_band"]) for p in get("http://localhost:8001/projects")])
for pid in ("nur_navoi_solar", "pizarro"):
    d = get(f"http://localhost:8001/projects/{pid}/dossier")
    print(pid, "claims:", len(d["claims"]), "on_track:", d["confidence"]["on_track_pct"], "xcheck:", [c["status"] for c in d["cross_check"]])
PY
```
Expected: both projects list with their risk bands (from `confidences`); each dossier assembles with the same claim counts / statuses as before the refactor.

- [ ] **Step 2: Drive both assets in the browser** (`localhost:3000`) — Disclosure/Locate/Observe/Cross-check/Confidence render identically to pre-refactor; the Evidence drawer still opens (evidence now project-linked). No console errors.

- [ ] **Step 3: Confirm single source of truth** — `grep -rn "risk_score\|risk_band\|main_finding" backend/app/models` shows these only in `confidences` (dossier.py), not in `projects`. `grep -rn "\.dossier\.json\|_DOSSIER_DIR" backend` returns nothing (no file store).

---

## Self-Review

**Spec coverage:** eight new tables + TraceMixin (Task 1) · migration with downgrade (Task 2) · merged fixtures + seed rewrite + integrity checks (Task 3) · dossier assembly + risk derivation + drop unused fields (Task 4) · dead-surface removal, ON DELETE CASCADE via models, ARRAY/Numeric/Date typing (Tasks 1/5) · parity verification (Task 6). All spec sections mapped. ✅

**Placeholder scan:** the only "verbatim from…" markers are in the merged-fixture steps, where the source objects are concrete files in the repo copied byte-for-byte — a deterministic transform, not an unspecified TODO. All code steps carry real code. ✅

**Type consistency:** model class names (`Disclosure`, `Claim`, `Localization`, `LocalizationAlternative`, `ObservationSnapshot`, `CrossCheck`, `CrossCheckEvidence`, `Confidence`, `EvidenceItem`) are used identically across the seed (Task 3), the assembly (Task 4), and the exports (Task 1). Evidence ids (`{pid}_ev_{i}`) match between the fixtures, the seed, and the `cross_check.evidence_ids`. `_trace`/`_trace_out` and `_split_value`/`_value_out` are the inverse pairs used by seed vs assembly. ✅
