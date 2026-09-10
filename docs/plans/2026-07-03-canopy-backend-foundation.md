# Canopy Backend Foundation — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Stand up the Canopy FastAPI backend that serves seeded, traceable evidence for the curated demo projects from a PostGIS database, over a small product-object read API.

**Architecture:** A `uv`-managed FastAPI app (`backend/`) talks to PostgreSQL 16 + PostGIS (Docker Compose) via SQLAlchemy 2.0 + GeoAlchemy2, with Alembic migrations. A seed script maps the geospatial pipeline's `§3.1` JSON output onto relational rows + local asset files; read-only endpoints serve projects, boundaries, imagery, observations, metrics, risk, and evidence. This is Plan 1 of 3 (backend foundation → LLM agent → frontend).

**Tech Stack:** Python 3.13, FastAPI, SQLAlchemy 2.0, GeoAlchemy2, Alembic, Pydantic v2 / pydantic-settings, psycopg (v3), PostgreSQL 16 + PostGIS 3.4, uv, pytest + httpx, ruff, mypy.

## Global Constraints

- **Python:** 3.13; dependency + venv management via **uv** only (no bare pip/poetry).
- **Database:** PostgreSQL **16** + PostGIS **3.4** via Docker Compose image `postgis/postgis:16-3.4`. pgvector is **deferred** to the LLM-agent stretch (retrieval is deterministic-by-`project_id` for the MVP).
- **Docker binary on this machine:** `/Applications/Docker.app/Contents/Resources/bin/docker` (not on PATH in non-interactive shells — prepend it or use the interactive terminal). Compose subcommand: `docker compose`.
- **Boundary geometry:** stored as PostGIS `Geometry(POLYGON, 4326)`, served to clients as GeoJSON via `ST_AsGeoJSON`.
- **Evidence is the central primitive:** every metric row links to an observation, and every observation carries ≥1 evidence_item. The seed step asserts this (traceability).
- **API serves product objects**, never raw implementation detail. Error envelope: `{"error": {"code", "message", "detail"}}`. Validation → 422, not-found → 404.
- **No auth** (single-user demo). **Local static-file storage** under `seed_data/assets/`, served at `/static`.
- **Commit discipline:** the pre-commit gate (`.claude/hooks/pre-commit-review.sh`) blocks code commits until `/simplify` + `/code-review` have run on the staged diff. Always `git add` and `git commit` as **separate** steps. Record the review with `git write-tree > .git/canopy-review-marker` before committing.
- **DB URLs:** dev `postgresql+psycopg://canopy:canopy@localhost:5432/canopy`; tests use a separate `canopy_test` database via `TEST_DATABASE_URL`.

---

## File Structure

```
backend/
  pyproject.toml            # uv project: deps + ruff/mypy/pytest config
  .env.example              # DATABASE_URL, TEST_DATABASE_URL
  app/
    __init__.py
    main.py                 # app factory, router mounting, /static, error handlers
    core/
      __init__.py
      config.py             # pydantic-settings Settings (env-driven)
      db.py                 # engine, SessionLocal, get_db dependency, Base
      storage.py            # Storage protocol + LocalStorage
      errors.py             # error envelope + exception handlers
    models/
      __init__.py           # re-exports all models + Base
      project.py            # Project, ProjectBoundary
      observation.py        # Observation, Metric, EvidenceItem
      risk.py               # RiskScore
      methodology.py        # Methodology
      report.py             # Report, QaLog
    schemas/
      __init__.py
      project.py            # ProjectSummary, ProjectDetail, Boundary, Imagery
      evidence.py           # ObservationOut, MetricOut, EvidenceItemOut, RiskOut
    services/
      __init__.py
      projects.py           # query helpers (list/get/boundary/imagery)
      evidence.py           # query helpers (observations/metrics/risk/evidence)
    api/
      __init__.py
      routes/
        __init__.py
        projects.py         # /projects*, /projects/{id}/boundary, /imagery
        evidence.py         # /observations, /metrics, /risk, /evidence
  alembic.ini
  alembic/
    env.py
    versions/0001_init.py
  tests/
    conftest.py             # test engine, table create, session + client fixtures
    test_health.py
    test_db.py
    test_models.py
    test_storage.py
    test_seed.py
    test_projects_api.py
    test_evidence_api.py
docker-compose.yml
seed_data/
  projects/nur_navoi.json   # curated fixture mirroring pipeline §3.1 output
scripts/
  seed.py                   # fixture JSON -> DB rows + local assets
```

---

### Task 1: Backend scaffold + health endpoint

**Files:**
- Create: `backend/pyproject.toml`, `backend/app/__init__.py`, `backend/app/main.py`, `backend/app/core/__init__.py`, `backend/app/core/config.py`, `backend/.env.example`
- Test: `backend/tests/test_health.py`

**Interfaces:**
- Produces: `app.main:create_app() -> FastAPI`; `app.core.config:Settings` with `.database_url`, `.test_database_url`, `.assets_dir`, `.static_mount` and a module-level `get_settings()` (cached).

- [ ] **Step 1: Initialize the uv project and add dependencies**

Run:
```bash
cd backend
uv init --name canopy-backend --python 3.13 --no-workspace
uv add fastapi "uvicorn[standard]" "sqlalchemy>=2" geoalchemy2 alembic "psycopg[binary]" pydantic-settings
uv add --dev pytest httpx ruff mypy
```

- [ ] **Step 2: Configure tooling in `backend/pyproject.toml`**

Append:
```toml
[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "UP", "B"]

[tool.mypy]
python_version = "3.13"
plugins = ["pydantic.mypy"]
ignore_missing_imports = true

[tool.pytest.ini_options]
addopts = "-q"
testpaths = ["tests"]
```

- [ ] **Step 3: Write `backend/app/core/config.py`**

```python
from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict

_REPO_ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    database_url: str = "postgresql+psycopg://canopy:canopy@localhost:5432/canopy"
    test_database_url: str = "postgresql+psycopg://canopy:canopy@localhost:5432/canopy_test"
    assets_dir: Path = _REPO_ROOT / "seed_data" / "assets"
    static_mount: str = "/static"


@lru_cache
def get_settings() -> Settings:
    return Settings()
```

- [ ] **Step 4: Write the failing test `backend/tests/test_health.py`**

```python
from fastapi.testclient import TestClient

from app.main import create_app


def test_health_ok():
    client = TestClient(create_app())
    resp = client.get("/health")
    assert resp.status_code == 200
    assert resp.json() == {"status": "ok"}
```

- [ ] **Step 5: Run it and confirm it fails**

Run: `cd backend && uv run pytest tests/test_health.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.main'` (or ImportError).

- [ ] **Step 6: Write `backend/app/main.py`**

```python
from fastapi import FastAPI


def create_app() -> FastAPI:
    app = FastAPI(title="Canopy API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok"}

    return app


app = create_app()
```

- [ ] **Step 7: Run the test and confirm it passes**

Run: `cd backend && uv run pytest tests/test_health.py -v`
Expected: PASS.

- [ ] **Step 8: Write `backend/.env.example`**

```dotenv
DATABASE_URL=postgresql+psycopg://canopy:canopy@localhost:5432/canopy
TEST_DATABASE_URL=postgresql+psycopg://canopy:canopy@localhost:5432/canopy_test
```

- [ ] **Step 9: Review + commit** (run `/simplify` then `/code-review` on the staged diff, apply fixes, then:)

```bash
git add backend/ .gitignore
git write-tree > .git/canopy-review-marker
git commit -m "feat(backend): scaffold FastAPI app with health endpoint"
```

---

### Task 2: Docker Compose Postgres+PostGIS + DB session

**Files:**
- Create: `docker-compose.yml`, `backend/app/core/db.py`
- Test: `backend/tests/test_db.py`, `backend/tests/conftest.py`

**Interfaces:**
- Produces: `app.core.db:Base` (DeclarativeBase), `engine`, `SessionLocal`, `get_db() -> Iterator[Session]`. `conftest` fixtures: `db_session` (rolled-back Session against `canopy_test`), `client` (TestClient with `get_db` overridden).

- [ ] **Step 1: Write `docker-compose.yml`**

```yaml
services:
  db:
    image: postgis/postgis:16-3.4
    environment:
      POSTGRES_USER: canopy
      POSTGRES_PASSWORD: canopy
      POSTGRES_DB: canopy
    ports:
      - "5432:5432"
    volumes:
      - canopy_pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U canopy"]
      interval: 5s
      timeout: 3s
      retries: 10

volumes:
  canopy_pgdata:
```

- [ ] **Step 2: Bring up the database and create the test DB**

Run (note the Docker path on this machine):
```bash
export PATH="/Applications/Docker.app/Contents/Resources/bin:$PATH"
docker compose up -d
until docker compose exec -T db pg_isready -U canopy; do sleep 1; done
docker compose exec -T db psql -U canopy -d canopy -c "CREATE DATABASE canopy_test;" || true
```
Expected: `db` healthy; `canopy_test` created (or already exists).

- [ ] **Step 3: Write `backend/app/core/db.py`**

```python
from collections.abc import Iterator

from sqlalchemy import create_engine
from sqlalchemy.orm import DeclarativeBase, Session, sessionmaker

from app.core.config import get_settings


class Base(DeclarativeBase):
    pass


engine = create_engine(get_settings().database_url, pool_pre_ping=True, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, expire_on_commit=False)


def get_db() -> Iterator[Session]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
```

- [ ] **Step 4: Write `backend/tests/conftest.py`**

```python
from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import Session, sessionmaker

from app.core.config import get_settings
from app.core.db import Base, get_db
from app.main import create_app

_engine = create_engine(get_settings().test_database_url, future=True)


@pytest.fixture(scope="session", autouse=True)
def _create_schema() -> Iterator[None]:
    with _engine.begin() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis"))
    # Import models so every table is registered on Base.metadata.
    import app.models  # noqa: F401

    Base.metadata.drop_all(_engine)
    Base.metadata.create_all(_engine)
    yield
    Base.metadata.drop_all(_engine)


@pytest.fixture
def db_session() -> Iterator[Session]:
    conn = _engine.connect()
    txn = conn.begin()
    session = sessionmaker(bind=conn, expire_on_commit=False)()
    try:
        yield session
    finally:
        session.close()
        txn.rollback()
        conn.close()


@pytest.fixture
def client(db_session: Session) -> Iterator[TestClient]:
    app = create_app()
    app.dependency_overrides[get_db] = lambda: db_session
    yield TestClient(app)
    app.dependency_overrides.clear()
```

- [ ] **Step 5: Write the failing test `backend/tests/test_db.py`**

```python
from sqlalchemy import text

from app.core.db import engine


def test_postgis_available():
    with engine.connect() as conn:
        version = conn.execute(text("SELECT postgis_version()")).scalar()
    assert version is not None and "3." in version
```

- [ ] **Step 6: Run tests and confirm they pass**

Run: `cd backend && uv run pytest tests/test_db.py -v`
Expected: PASS (requires `docker compose up -d` from Step 2).

- [ ] **Step 7: Review + commit**

```bash
git add docker-compose.yml backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(backend): postgis compose + sqlalchemy session and test fixtures"
```

---

### Task 3: ORM models + Alembic migration

**Files:**
- Create: `backend/app/models/__init__.py`, `backend/app/models/project.py`, `backend/app/models/observation.py`, `backend/app/models/risk.py`, `backend/app/models/methodology.py`, `backend/app/models/report.py`, `backend/alembic.ini`, `backend/alembic/env.py`, `backend/alembic/versions/0001_init.py`
- Test: `backend/tests/test_models.py`

**Interfaces:**
- Produces ORM classes on `app.core.db.Base`: `Project(id:str, name, asset_type, country, financing_type, monitoring_objective, status, screening_status, risk_score:int|None, risk_band, confidence:float|None, main_finding)`; `ProjectBoundary(id, project_id, geom, crs, source, area_hectares:float, validation_status)`; `Observation(id, project_id, observation_type, period_start, period_end, summary, severity, confidence:float, created_at)`; `Metric(id, observation_id, metric_name, value:float, unit, baseline_value:float|None, comparison_value:float|None, method_id)`; `EvidenceItem(id, observation_id, source_name, source_date, method_id, confidence, limitations:list, financial_relevance, supporting_assets:list)`; `RiskScore(id, project_id, score_type, score_value:int, score_band, drivers_json:dict, updated_at)`; `Methodology(id, method_id, name, description, data_sources, assumptions, limitations, version)`; `Report(id, project_id, report_type, generated_at, evidence_ids_json:list, content, report_uri)`; `QaLog(id, project_id, question, answer, evidence_ids_json:list, model, created_at)`.

- [ ] **Step 1: Write `backend/app/models/project.py`**

```python
from geoalchemy2 import Geometry
from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    name: Mapped[str] = mapped_column(String)
    asset_type: Mapped[str] = mapped_column(String)
    country: Mapped[str | None] = mapped_column(String, nullable=True)
    financing_type: Mapped[str | None] = mapped_column(String, nullable=True)
    monitoring_objective: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="monitored")
    screening_status: Mapped[str | None] = mapped_column(String, nullable=True)
    risk_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    risk_band: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    main_finding: Mapped[str | None] = mapped_column(String, nullable=True)

    boundary: Mapped["ProjectBoundary"] = relationship(back_populates="project", uselist=False)


class ProjectBoundary(Base):
    __tablename__ = "project_boundaries"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    geom: Mapped[object] = mapped_column(Geometry("POLYGON", srid=4326))
    crs: Mapped[str] = mapped_column(String, default="EPSG:4326")
    source: Mapped[str | None] = mapped_column(String, nullable=True)
    area_hectares: Mapped[float | None] = mapped_column(Float, nullable=True)
    validation_status: Mapped[str] = mapped_column(String, default="demo")

    project: Mapped[Project] = relationship(back_populates="boundary")
```

- [ ] **Step 2: Write `backend/app/models/observation.py`**

```python
from datetime import datetime

from sqlalchemy import DateTime, Float, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.db import Base


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    observation_type: Mapped[str] = mapped_column(String)
    period_start: Mapped[str | None] = mapped_column(String, nullable=True)
    period_end: Mapped[str | None] = mapped_column(String, nullable=True)
    summary: Mapped[str] = mapped_column(String)
    severity: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    metrics: Mapped[list["Metric"]] = relationship(back_populates="observation")
    evidence_items: Mapped[list["EvidenceItem"]] = relationship(back_populates="observation")


class Metric(Base):
    __tablename__ = "metrics"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    observation_id: Mapped[str] = mapped_column(ForeignKey("observations.id"))
    metric_name: Mapped[str] = mapped_column(String)
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String, nullable=True)
    baseline_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    comparison_value: Mapped[float | None] = mapped_column(Float, nullable=True)
    method_id: Mapped[str | None] = mapped_column(String, nullable=True)

    observation: Mapped[Observation] = relationship(back_populates="metrics")


class EvidenceItem(Base):
    __tablename__ = "evidence_items"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    observation_id: Mapped[str] = mapped_column(ForeignKey("observations.id"))
    source_name: Mapped[str] = mapped_column(String)
    source_date: Mapped[str | None] = mapped_column(String, nullable=True)
    method_id: Mapped[str | None] = mapped_column(String, nullable=True)
    confidence: Mapped[str | None] = mapped_column(String, nullable=True)
    limitations: Mapped[list] = mapped_column(JSONB, default=list)
    financial_relevance: Mapped[str | None] = mapped_column(String, nullable=True)
    supporting_assets: Mapped[list] = mapped_column(JSONB, default=list)

    observation: Mapped[Observation] = relationship(back_populates="evidence_items")
```

- [ ] **Step 3: Write `backend/app/models/risk.py`, `methodology.py`, `report.py`**

`risk.py`:
```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class RiskScore(Base):
    __tablename__ = "risk_scores"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    score_type: Mapped[str] = mapped_column(String, default="composite")
    score_value: Mapped[int | None] = mapped_column(Integer, nullable=True)
    score_band: Mapped[str | None] = mapped_column(String, nullable=True)
    drivers_json: Mapped[dict] = mapped_column(JSONB, default=dict)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

`methodology.py`:
```python
from sqlalchemy import String
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Methodology(Base):
    __tablename__ = "methodologies"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    method_id: Mapped[str] = mapped_column(String, unique=True)
    name: Mapped[str] = mapped_column(String)
    description: Mapped[str] = mapped_column(String)
    data_sources: Mapped[list] = mapped_column(JSONB, default=list)
    assumptions: Mapped[list] = mapped_column(JSONB, default=list)
    limitations: Mapped[list] = mapped_column(JSONB, default=list)
    version: Mapped[str] = mapped_column(String, default="v1")
```

`report.py`:
```python
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.core.db import Base


class Report(Base):
    __tablename__ = "reports"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    report_type: Mapped[str] = mapped_column(String)
    generated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    evidence_ids_json: Mapped[list] = mapped_column(JSONB, default=list)
    content: Mapped[str | None] = mapped_column(String, nullable=True)
    report_uri: Mapped[str | None] = mapped_column(String, nullable=True)


class QaLog(Base):
    __tablename__ = "qa_logs"

    id: Mapped[str] = mapped_column(String, primary_key=True)
    project_id: Mapped[str] = mapped_column(ForeignKey("projects.id"))
    question: Mapped[str] = mapped_column(String)
    answer: Mapped[str | None] = mapped_column(String, nullable=True)
    evidence_ids_json: Mapped[list] = mapped_column(JSONB, default=list)
    model: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
```

- [ ] **Step 4: Write `backend/app/models/__init__.py`**

```python
from app.core.db import Base
from app.models.methodology import Methodology
from app.models.observation import EvidenceItem, Metric, Observation
from app.models.project import Project, ProjectBoundary
from app.models.report import QaLog, Report
from app.models.risk import RiskScore

__all__ = [
    "Base", "Project", "ProjectBoundary", "Observation", "Metric",
    "EvidenceItem", "RiskScore", "Methodology", "Report", "QaLog",
]
```

- [ ] **Step 5: Write the failing test `backend/tests/test_models.py`**

```python
from app.models import EvidenceItem, Metric, Observation, Project


def test_project_observation_metric_roundtrip(db_session):
    db_session.add(Project(id="p1", name="Demo", asset_type="solar"))
    obs = Observation(id="o1", project_id="p1", observation_type="land_cover_change", summary="s")
    db_session.add(obs)
    db_session.add(Metric(id="m1", observation_id="o1", metric_name="veg_change_pct", value=17.3))
    db_session.add(
        EvidenceItem(id="e1", observation_id="o1", source_name="Sentinel-2", limitations=["proxy"])
    )
    db_session.flush()

    got = db_session.get(Observation, "o1")
    assert got.metrics[0].metric_name == "veg_change_pct"
    assert got.evidence_items[0].source_name == "Sentinel-2"
```

- [ ] **Step 6: Run it and confirm it passes** (tables come from `conftest`'s `create_all`)

Run: `cd backend && uv run pytest tests/test_models.py -v`
Expected: PASS.

- [ ] **Step 7: Initialize Alembic and write the init migration**

Run: `cd backend && uv run alembic init -t async alembic` is NOT used; instead:
```bash
cd backend && uv run alembic init alembic
```
Then set `sqlalchemy.url` handling in `backend/alembic/env.py` — replace its body with:
```python
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.core.config import get_settings
from app.core.db import Base
import app.models  # noqa: F401  (register all tables)

config = context.config
config.set_main_option("sqlalchemy.url", get_settings().database_url)
if config.config_file_name:
    fileConfig(config.config_file_name)
target_metadata = Base.metadata


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.", poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
```

- [ ] **Step 8: Autogenerate + apply the migration**

```bash
cd backend
uv run alembic revision --autogenerate -m "init schema"
# rename the generated file to versions/0001_init.py for stable ordering
uv run alembic upgrade head
```
Then edit the migration's `upgrade()` to prepend `op.execute("CREATE EXTENSION IF NOT EXISTS postgis")` before table creation.
Expected: migration applies cleanly to the `canopy` dev DB.

- [ ] **Step 9: Review + commit**

```bash
git add backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(backend): ORM models for evidence data model + alembic init migration"
```

---

### Task 4: Pydantic response schemas

**Files:**
- Create: `backend/app/schemas/__init__.py`, `backend/app/schemas/project.py`, `backend/app/schemas/evidence.py`
- Test: `backend/tests/test_schemas.py` (folded into Task 7/8 API tests is acceptable; a minimal unit test here)

**Interfaces:**
- Produces: `ProjectSummary`, `ProjectDetail`, `Imagery`, `ObservationOut`, `MetricOut`, `EvidenceItemOut`, `RiskOut` — all `model_config = ConfigDict(from_attributes=True)`.

- [ ] **Step 1: Write `backend/app/schemas/project.py`**

```python
from pydantic import BaseModel, ConfigDict


class ProjectSummary(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    name: str
    asset_type: str
    country: str | None = None
    financing_type: str | None = None
    status: str
    risk_score: int | None = None
    risk_band: str | None = None


class ProjectDetail(ProjectSummary):
    monitoring_objective: str | None = None
    screening_status: str | None = None
    confidence: float | None = None
    main_finding: str | None = None


class ImageLayer(BaseModel):
    key: str
    label: str
    url: str
    kind: str  # "rgb" | "overlay"
    date: str | None = None


class Imagery(BaseModel):
    project_id: str
    layers: list[ImageLayer]
```

- [ ] **Step 2: Write `backend/app/schemas/evidence.py`**

```python
from pydantic import BaseModel, ConfigDict


class MetricOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    metric_name: str
    value: float | None = None
    unit: str | None = None
    baseline_value: float | None = None
    comparison_value: float | None = None
    method_id: str | None = None


class EvidenceItemOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    observation_id: str
    source_name: str
    source_date: str | None = None
    method_id: str | None = None
    confidence: str | None = None
    limitations: list[str] = []
    financial_relevance: str | None = None
    supporting_assets: list[str] = []


class ObservationOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    observation_type: str
    period_start: str | None = None
    period_end: str | None = None
    summary: str
    severity: str | None = None
    confidence: float | None = None
    metrics: list[MetricOut] = []


class RiskOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    score_type: str
    score_value: int | None = None
    score_band: str | None = None
    drivers_json: dict = {}
```

- [ ] **Step 3: Write `backend/tests/test_schemas.py`**

```python
from app.models import Project
from app.schemas.project import ProjectSummary


def test_project_summary_from_orm():
    p = Project(id="p1", name="Demo", asset_type="solar", status="monitored", risk_score=61)
    out = ProjectSummary.model_validate(p)
    assert out.id == "p1" and out.risk_score == 61
```

- [ ] **Step 4: Run and confirm it passes**

Run: `cd backend && uv run pytest tests/test_schemas.py -v`
Expected: PASS.

- [ ] **Step 5: Review + commit**

```bash
git add backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(backend): pydantic response schemas for product objects"
```

---

### Task 5: Local storage abstraction + static mount

**Files:**
- Create: `backend/app/core/storage.py`; modify `backend/app/main.py` to mount `/static`
- Test: `backend/tests/test_storage.py`

**Interfaces:**
- Produces: `Storage` protocol (`save(key: str, data: bytes) -> str`, `url_for(key: str) -> str`, `path_for(key: str) -> Path`) and `LocalStorage(root: Path, mount: str)`; `get_storage()` factory.

- [ ] **Step 1: Write `backend/app/core/storage.py`**

```python
from pathlib import Path
from typing import Protocol

from app.core.config import get_settings


class Storage(Protocol):
    def save(self, key: str, data: bytes) -> str: ...
    def url_for(self, key: str) -> str: ...
    def path_for(self, key: str) -> Path: ...


class LocalStorage:
    def __init__(self, root: Path, mount: str) -> None:
        self._root = root
        self._mount = mount.rstrip("/")

    def path_for(self, key: str) -> Path:
        return self._root / key

    def save(self, key: str, data: bytes) -> str:
        dest = self.path_for(key)
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_bytes(data)
        return self.url_for(key)

    def url_for(self, key: str) -> str:
        return f"{self._mount}/{key}"


def get_storage() -> Storage:
    s = get_settings()
    return LocalStorage(s.assets_dir, s.static_mount)
```

- [ ] **Step 2: Mount `/static` in `create_app()` (edit `app/main.py`)**

Add inside `create_app()` before `return app`:
```python
    from fastapi.staticfiles import StaticFiles

    settings = get_settings()
    settings.assets_dir.mkdir(parents=True, exist_ok=True)
    app.mount(settings.static_mount, StaticFiles(directory=settings.assets_dir), name="static")
```
And add `from app.core.config import get_settings` at the top.

- [ ] **Step 3: Write `backend/tests/test_storage.py`**

```python
from app.core.storage import LocalStorage


def test_local_storage_save_and_url(tmp_path):
    store = LocalStorage(tmp_path, "/static")
    url = store.save("solar/before.png", b"\x89PNG")
    assert url == "/static/solar/before.png"
    assert (tmp_path / "solar" / "before.png").read_bytes() == b"\x89PNG"
```

- [ ] **Step 4: Run and confirm it passes**

Run: `cd backend && uv run pytest tests/test_storage.py -v`
Expected: PASS.

- [ ] **Step 5: Review + commit**

```bash
git add backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(backend): local storage abstraction + static mount"
```

---

### Task 6: Seed fixture + seed script + traceability

**Files:**
- Create: `seed_data/projects/nur_navoi.json`, `scripts/seed.py`
- Test: `backend/tests/test_seed.py`

**Interfaces:**
- Produces: `scripts.seed:seed_project(session, fixture: dict) -> str` (returns project id) and `scripts.seed:load_fixture(path: Path) -> dict`. Maps pipeline `§3.1` JSON → rows; asserts every observation has ≥1 evidence_item and every metric links to an observation.

- [ ] **Step 1: Write the curated fixture `seed_data/projects/nur_navoi.json`**

This mirrors the pipeline's `export/json_export.py` output shape for the solar (non-veg) case, plus the finance fields the backend owns. Representative values (regenerate from a real `run_pipeline` when GEE auth is available):
```json
{
  "analysis_id": "nur_navoi_solar",
  "project_name": "Nur Navoi Solar (100 MW), Uzbekistan",
  "asset_type": "solar",
  "country": "Uzbekistan",
  "financing_type": "development_finance",
  "monitoring_objective": "Verify build-out and ongoing operation vs stated use of proceeds.",
  "aoi_coords": [[64.978, 40.104], [64.994, 40.104], [64.994, 40.120], [64.978, 40.120], [64.978, 40.104]],
  "summary": {
    "screening_status": "Partially consistent",
    "risk_score": 61, "risk_band": "High", "confidence": 0.72,
    "change_detected": true, "human_review_recommended": true,
    "main_finding": "Visible site build-out consistent with construction; elevated flood exposure on flat terrain."
  },
  "metrics": {
    "vegetation_change_percent": 34.1, "flood_risk_score": 61, "fire_risk_score": 22,
    "deforestation_detected": false
  },
  "evidence": [
    {
      "observation_type": "land_cover_change",
      "summary": "Land-cover change consistent with construction / operation.",
      "metric": {"name": "vegetation_change_percent", "value": 34.1,
                 "baseline_period": "2019-04", "comparison_period": "2023-04"},
      "source": {"name": "Sentinel-2 + Sentinel-1", "resolution": "10 m",
                 "processing": "median composite; SAR water layer"},
      "method": "bi-temporal change + SAR flood proxy (method_id: build_v1)",
      "confidence": "medium",
      "financial_relevance": "Construction footprint indicator relevant to use-of-proceeds monitoring.",
      "limitations": ["confirms build/land-cover change, not generation output",
                      "generation/carbon proxy needs ground truth to certify",
                      "no independent metering in the demo"],
      "supporting_assets": ["before_rgb.png", "after_rgb.png", "change_overlay.png"]
    }
  ],
  "map_outputs": {"rgb_composite_url": "before_rgb.png"},
  "metadata": {"date_range": {"start": "2019-04-01", "end": "2023-09-30"},
               "aoi_area_hectares": 231.4}
}
```

- [ ] **Step 2: Write `scripts/seed.py`**

```python
from __future__ import annotations

import json
import sys
from pathlib import Path

from geoalchemy2.shape import from_shape
from shapely.geometry import Polygon
from sqlalchemy.orm import Session

# make `app` importable when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "backend"))

from app.core.db import SessionLocal  # noqa: E402
from app.models import (  # noqa: E402
    EvidenceItem, Metric, Observation, Project, ProjectBoundary, RiskScore,
)


def load_fixture(path: Path) -> dict:
    return json.loads(path.read_text())


def seed_project(session: Session, fx: dict) -> str:
    pid = fx["analysis_id"]
    s = fx["summary"]
    session.merge(Project(
        id=pid, name=fx["project_name"], asset_type=fx["asset_type"],
        country=fx.get("country"), financing_type=fx.get("financing_type"),
        monitoring_objective=fx.get("monitoring_objective"), status="monitored",
        screening_status=s["screening_status"], risk_score=s["risk_score"],
        risk_band=s["risk_band"], confidence=s["confidence"], main_finding=s["main_finding"],
    ))
    poly = Polygon(fx["aoi_coords"])
    session.merge(ProjectBoundary(
        id=f"{pid}_boundary", project_id=pid,
        geom=from_shape(poly, srid=4326), source="demo_fixture",
        area_hectares=fx["metadata"].get("aoi_area_hectares"),
    ))
    session.merge(RiskScore(
        id=f"{pid}_risk", project_id=pid, score_type="composite",
        score_value=s["risk_score"], score_band=s["risk_band"],
        drivers_json={"flood": fx["metrics"].get("flood_risk_score"),
                      "fire": fx["metrics"].get("fire_risk_score")},
    ))
    for i, card in enumerate(fx["evidence"]):
        oid = f"{pid}_obs_{i}"
        session.merge(Observation(
            id=oid, project_id=pid, observation_type=card["observation_type"],
            period_start=card["metric"].get("baseline_period"),
            period_end=card["metric"].get("comparison_period"),
            summary=card["summary"], severity=s["risk_band"], confidence=s["confidence"],
        ))
        session.merge(Metric(
            id=f"{oid}_metric", observation_id=oid, metric_name=card["metric"]["name"],
            value=card["metric"].get("value"), method_id=_method_id(card["method"]),
        ))
        session.merge(EvidenceItem(
            id=f"{pid}_ev_{i}", observation_id=oid, source_name=card["source"]["name"],
            source_date=card["metric"].get("comparison_period"), method_id=_method_id(card["method"]),
            confidence=card["confidence"], limitations=card.get("limitations", []),
            financial_relevance=card.get("financial_relevance"),
            supporting_assets=card.get("supporting_assets", []),
        ))
    session.flush()
    _assert_traceable(session, pid)
    return pid


def _method_id(method: str) -> str | None:
    return method.split("method_id:")[-1].strip(" )") if "method_id:" in method else None


def _assert_traceable(session: Session, pid: str) -> None:
    obs = session.query(Observation).filter_by(project_id=pid).all()
    assert obs, f"{pid}: no observations"
    for o in obs:
        assert o.evidence_items, f"observation {o.id} has no evidence"


def main() -> None:
    fixture = Path(sys.argv[1]) if len(sys.argv) > 1 else (
        Path(__file__).resolve().parents[1] / "seed_data" / "projects" / "nur_navoi.json"
    )
    session = SessionLocal()
    try:
        pid = seed_project(session, load_fixture(fixture))
        session.commit()
        print(f"seeded {pid}")
    finally:
        session.close()


if __name__ == "__main__":
    main()
```

- [ ] **Step 3: Add the seed script's runtime deps**

Run: `cd backend && uv add shapely`
(`geoalchemy2` is already present; `shapely` builds the polygon.)

- [ ] **Step 4: Write the failing test `backend/tests/test_seed.py`**

```python
import json
from pathlib import Path

from app.models import EvidenceItem, Metric, Observation, Project
from scripts.seed import seed_project

FIXTURE = Path(__file__).resolve().parents[2] / "seed_data" / "projects" / "nur_navoi.json"


def test_seed_populates_and_is_traceable(db_session):
    pid = seed_project(db_session, json.loads(FIXTURE.read_text()))
    assert db_session.get(Project, pid) is not None
    metrics = db_session.query(Metric).all()
    obs_ids = {o.id for o in db_session.query(Observation).all()}
    assert metrics and all(m.observation_id in obs_ids for m in metrics)
    assert db_session.query(EvidenceItem).count() >= 1
```
Add `sys.path` for `scripts` import at top of the test (or a `conftest` path insert):
```python
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
```

- [ ] **Step 5: Run and confirm it passes**

Run: `cd backend && uv run pytest tests/test_seed.py -v`
Expected: PASS (traceability assert holds).

- [ ] **Step 6: Seed the dev DB and eyeball it**

```bash
cd backend && uv run python ../scripts/seed.py
uv run python -c "from app.core.db import SessionLocal; from app.models import Project; print([p.id for p in SessionLocal().query(Project).all()])"
```
Expected: `seeded nur_navoi_solar` then `['nur_navoi_solar']`.

- [ ] **Step 7: Review + commit**

```bash
git add backend/ scripts/ seed_data/
git write-tree > .git/canopy-review-marker
git commit -m "feat(backend): seed script + curated fixture with traceability check"
```

---

### Task 7: Projects endpoints (list / detail / boundary / imagery)

**Files:**
- Create: `backend/app/services/projects.py`, `backend/app/api/routes/projects.py`, `backend/app/core/errors.py`; modify `backend/app/main.py` to include the router + error handlers
- Test: `backend/tests/test_projects_api.py`

**Interfaces:**
- Consumes: models from Task 3, schemas from Task 4, `seed_project` from Task 6 (tests seed into `db_session`).
- Produces routes: `GET /projects -> list[ProjectSummary]`, `GET /projects/{id} -> ProjectDetail` (404 envelope if missing), `GET /projects/{id}/boundary -> GeoJSON Feature`, `GET /projects/{id}/imagery -> Imagery`.

- [ ] **Step 1: Write `backend/app/core/errors.py`**

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse


class NotFound(Exception):
    def __init__(self, message: str) -> None:
        self.message = message


def install_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(NotFound)
    async def _not_found(_: Request, exc: NotFound) -> JSONResponse:
        return JSONResponse(
            status_code=404,
            content={"error": {"code": "not_found", "message": exc.message, "detail": None}},
        )
```

- [ ] **Step 2: Write `backend/app/services/projects.py`**

```python
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import Project, ProjectBoundary


def list_projects(db: Session) -> list[Project]:
    return list(db.scalars(select(Project).order_by(Project.name)))


def get_project(db: Session, project_id: str) -> Project:
    p = db.get(Project, project_id)
    if p is None:
        raise NotFound(f"project {project_id} not found")
    return p


def get_boundary_geojson(db: Session, project_id: str) -> dict:
    row = db.execute(
        select(ProjectBoundary, func.ST_AsGeoJSON(ProjectBoundary.geom))
        .where(ProjectBoundary.project_id == project_id)
    ).first()
    if row is None:
        raise NotFound(f"boundary for {project_id} not found")
    boundary, geojson = row
    import json

    return {
        "type": "Feature",
        "geometry": json.loads(geojson),
        "properties": {"project_id": project_id, "area_hectares": boundary.area_hectares},
    }
```

- [ ] **Step 3: Write `backend/app/services/projects.py` imagery helper (append)**

```python
from app.core.storage import get_storage
from app.schemas.project import ImageLayer, Imagery
from app.models import EvidenceItem, Observation


def get_imagery(db: Session, project_id: str) -> Imagery:
    get_project(db, project_id)  # 404 if missing
    store = get_storage()
    assets: list[str] = []
    for ev in db.scalars(
        select(EvidenceItem).join(Observation).where(Observation.project_id == project_id)
    ):
        assets.extend(ev.supporting_assets or [])
    seen: dict[str, ImageLayer] = {}
    for name in assets:
        if name in seen:
            continue
        kind = "rgb" if "rgb" in name else "overlay"
        seen[name] = ImageLayer(
            key=name, label=name.replace("_", " ").rsplit(".", 1)[0],
            url=store.url_for(f"{project_id}/{name}"), kind=kind,
        )
    return Imagery(project_id=project_id, layers=list(seen.values()))
```

- [ ] **Step 4: Write `backend/app/api/routes/projects.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.project import Imagery, ProjectDetail, ProjectSummary
from app.services import projects as svc

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSummary])
def list_projects(db: Session = Depends(get_db)) -> list[ProjectSummary]:
    return [ProjectSummary.model_validate(p) for p in svc.list_projects(db)]


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: str, db: Session = Depends(get_db)) -> ProjectDetail:
    return ProjectDetail.model_validate(svc.get_project(db, project_id))


@router.get("/{project_id}/boundary")
def get_boundary(project_id: str, db: Session = Depends(get_db)) -> dict:
    return svc.get_boundary_geojson(db, project_id)


@router.get("/{project_id}/imagery", response_model=Imagery)
def get_imagery(project_id: str, db: Session = Depends(get_db)) -> Imagery:
    return svc.get_imagery(db, project_id)
```

- [ ] **Step 5: Wire router + error handlers into `app/main.py`**

Inside `create_app()` before `return app`:
```python
    from app.api.routes import projects as projects_routes
    from app.core.errors import install_error_handlers

    install_error_handlers(app)
    app.include_router(projects_routes.router)
```

- [ ] **Step 6: Write the failing test `backend/tests/test_projects_api.py`**

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.seed import seed_project  # noqa: E402

FIXTURE = Path(__file__).resolve().parents[2] / "seed_data" / "projects" / "nur_navoi.json"


def _seed(db):
    seed_project(db, json.loads(FIXTURE.read_text()))
    db.flush()


def test_list_and_detail(client, db_session):
    _seed(db_session)
    assert client.get("/projects").json()[0]["id"] == "nur_navoi_solar"
    detail = client.get("/projects/nur_navoi_solar").json()
    assert detail["risk_band"] == "High"


def test_detail_404(client):
    body = client.get("/projects/missing").json()
    assert body["error"]["code"] == "not_found"


def test_boundary_is_geojson(client, db_session):
    _seed(db_session)
    feat = client.get("/projects/nur_navoi_solar/boundary").json()
    assert feat["type"] == "Feature" and feat["geometry"]["type"] == "Polygon"


def test_imagery_layers(client, db_session):
    _seed(db_session)
    layers = client.get("/projects/nur_navoi_solar/imagery").json()["layers"]
    assert any(layer["kind"] == "rgb" for layer in layers)
```

- [ ] **Step 7: Run and confirm all pass**

Run: `cd backend && uv run pytest tests/test_projects_api.py -v`
Expected: 4 PASS.

- [ ] **Step 8: Review + commit**

```bash
git add backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(backend): projects/boundary/imagery endpoints + error envelope"
```

---

### Task 8: Evidence endpoints (observations / metrics / risk / evidence)

**Files:**
- Create: `backend/app/services/evidence.py`, `backend/app/api/routes/evidence.py`; modify `app/main.py` to include the router
- Test: `backend/tests/test_evidence_api.py`

**Interfaces:**
- Produces routes: `GET /projects/{id}/observations -> list[ObservationOut]`, `GET /projects/{id}/metrics -> list[MetricOut]`, `GET /projects/{id}/risk -> RiskOut`, `GET /projects/{id}/evidence -> list[EvidenceItemOut]`.

- [ ] **Step 1: Write `backend/app/services/evidence.py`**

```python
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.errors import NotFound
from app.models import EvidenceItem, Metric, Observation, RiskScore


def observations(db: Session, project_id: str) -> list[Observation]:
    return list(db.scalars(select(Observation).where(Observation.project_id == project_id)))


def metrics(db: Session, project_id: str) -> list[Metric]:
    return list(
        db.scalars(select(Metric).join(Observation).where(Observation.project_id == project_id))
    )


def risk(db: Session, project_id: str) -> RiskScore:
    r = db.scalars(select(RiskScore).where(RiskScore.project_id == project_id)).first()
    if r is None:
        raise NotFound(f"risk for {project_id} not found")
    return r


def evidence(db: Session, project_id: str) -> list[EvidenceItem]:
    return list(
        db.scalars(
            select(EvidenceItem).join(Observation).where(Observation.project_id == project_id)
        )
    )
```

- [ ] **Step 2: Write `backend/app/api/routes/evidence.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.evidence import EvidenceItemOut, MetricOut, ObservationOut, RiskOut
from app.services import evidence as svc

router = APIRouter(prefix="/projects", tags=["evidence"])


@router.get("/{project_id}/observations", response_model=list[ObservationOut])
def observations(project_id: str, db: Session = Depends(get_db)) -> list[ObservationOut]:
    return [ObservationOut.model_validate(o) for o in svc.observations(db, project_id)]


@router.get("/{project_id}/metrics", response_model=list[MetricOut])
def metrics(project_id: str, db: Session = Depends(get_db)) -> list[MetricOut]:
    return [MetricOut.model_validate(m) for m in svc.metrics(db, project_id)]


@router.get("/{project_id}/risk", response_model=RiskOut)
def risk(project_id: str, db: Session = Depends(get_db)) -> RiskOut:
    return RiskOut.model_validate(svc.risk(db, project_id))


@router.get("/{project_id}/evidence", response_model=list[EvidenceItemOut])
def evidence(project_id: str, db: Session = Depends(get_db)) -> list[EvidenceItemOut]:
    return [EvidenceItemOut.model_validate(e) for e in svc.evidence(db, project_id)]
```

- [ ] **Step 3: Include the router in `app/main.py`**

```python
    from app.api.routes import evidence as evidence_routes
    app.include_router(evidence_routes.router)
```

- [ ] **Step 4: Write the failing test `backend/tests/test_evidence_api.py`**

```python
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from scripts.seed import seed_project  # noqa: E402

FIXTURE = Path(__file__).resolve().parents[2] / "seed_data" / "projects" / "nur_navoi.json"


def _seed(db):
    seed_project(db, json.loads(FIXTURE.read_text()))
    db.flush()


def test_metrics_and_evidence_are_linked(client, db_session):
    _seed(db_session)
    obs = client.get("/projects/nur_navoi_solar/observations").json()
    metrics = client.get("/projects/nur_navoi_solar/metrics").json()
    evidence = client.get("/projects/nur_navoi_solar/evidence").json()
    obs_ids = {o["id"] for o in obs}
    assert metrics and all(m["id"] for m in metrics)
    assert evidence and all(e["observation_id"] in obs_ids for e in evidence)


def test_risk(client, db_session):
    _seed(db_session)
    r = client.get("/projects/nur_navoi_solar/risk").json()
    assert r["score_value"] == 61 and r["score_band"] == "High"
```

- [ ] **Step 5: Run the full suite and confirm green**

Run: `cd backend && uv run pytest -v`
Expected: all tests PASS.

- [ ] **Step 6: Manual smoke test the API**

```bash
cd backend && uv run uvicorn app.main:app --port 8000 &
sleep 2
curl -s localhost:8000/projects | head -c 300
curl -s localhost:8000/projects/nur_navoi_solar/evidence | head -c 300
kill %1
```
Expected: JSON arrays for projects and evidence.

- [ ] **Step 7: Review + commit**

```bash
git add backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(backend): observations/metrics/risk/evidence endpoints"
```

---

## Self-Review

**Spec coverage (spec §4–§12):**
- §4 repo layout → Tasks 1–8 create `backend/app/{core,models,schemas,services,api}`, `scripts/seed.py`, `seed_data/`, `docker-compose.yml`. ✅
- §5 data model (9 tables) → Task 3 (all tables) + Task 6 seeds them. ✅
- §6 seed pipeline (fixture path, traceability) → Task 6. ✅
- §7 read endpoints (7 of them) → Tasks 7–8. `/ask`, `/reports`, `/analyses` are Plan 2/3 (out of scope here). ✅ (documented deferral)
- §10 storage abstraction → Task 5. ✅
- §11 error envelope → Task 7 (`errors.py`). ✅
- §12 traceability + determinism → Task 6 assert + fixture-based seed (no live GEE). ✅
- pgvector (§5 stretch) → explicitly deferred in Global Constraints. ✅

**Placeholder scan:** no TBD/TODO; every code step shows full code; the fixture carries representative-but-real-shaped values with a regeneration note. ✅

**Type consistency:** `seed_project(session, fx) -> str`, `get_project/list_projects/get_boundary_geojson/get_imagery` signatures match their callers in routes and tests; schema field names (`score_value`, `risk_band`, `supporting_assets`) match model attributes used in services. ✅

**Deferred to later plans:** `/ask` + `/reports` + guardrails (Plan 2, LLM agent); all 7 frontend screens + MapLibre (Plan 3); live `POST /analyses` (stretch).
