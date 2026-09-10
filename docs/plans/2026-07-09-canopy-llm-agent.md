# Canopy LLM Reasoning Agent — Implementation Plan (Plan 2 of 3)

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add Canopy's reasoning layer — bounded, evidence-cited Q&A (`/ask`) and finance-ready memo generation (`/reports`) over the stored evidence, with guardrails that keep the LLM an evidence *explainer*, never an inference engine.

**Architecture:** A thin provider-agnostic `LLMClient` (OpenAI-compatible, injectable for tests) sits behind an `agent` package: `retrieval` builds a cited evidence context deterministically by `project_id`; `agent` orchestrates prompt → LLM → parsed result under the §9 guardrail system prompt; a service layer persists Q&A (`qa_logs`) and memos (`reports`). Routes expose `POST /projects/{id}/ask`, `POST /projects/{id}/reports`, `GET /reports/{id}`. **All tests use a `FakeLLMClient` — no API key needed until the live smoke test.**

**Tech Stack:** builds on Plan 1 (FastAPI, SQLAlchemy 2.0, Postgres/PostGIS, Pydantic v2, uv, pytest). Adds the `openai` SDK (used only as an OpenAI-compatible HTTP client).

## Global Constraints

- **Provider-agnostic + BYOK:** an OpenAI-compatible client configured by `LLM_BASE_URL` + `LLM_API_KEY` + `LLM_MODEL` from `.env`. Works with OpenAI / Anthropic / Google / local endpoints. No provider hardcoded.
- **The LLM explains; it never computes.** Answer only from supplied evidence/metrics/methodology; never infer from imagery; always cite evidence IDs; state uncertainty/limitations; refuse legal/audit/regulatory/carbon-verification/investment-advice claims; recommend human review when evidence is insufficient. (Engineering Supplement §9 — the system prompt is used verbatim.)
- **Deterministic retrieval** by `project_id` (+ optional `allowed_evidence_ids` scoping). pgvector semantic retrieval stays a Plan-3+ stretch.
- **Traceability:** every `/ask` answer and `/reports` memo records the evidence IDs it used (`qa_logs`, `reports.evidence_ids_json`).
- **Testing:** inject a `FakeLLMClient` via the `get_llm_client` FastAPI dependency; assert the guardrail prompt + evidence context reach the client and that responses parse. One live smoke test is gated on `LLM_API_KEY` being set.
- **DB is on host port 5433**; run gate via `uv` (`cd backend && uv run …`); `git add`/`git commit` are separate steps; record the review marker before committing (per the pre-commit gate).
- **Error envelope + `get_project` 404 guard** (from Plan 1) apply to the new endpoints too.

---

## File Structure

```
backend/app/
  core/config.py              # + llm_base_url / llm_api_key / llm_model
  agent/
    __init__.py
    client.py                 # LLMClient protocol + OpenAIClient + get_llm_client()
    prompts.py                # SYSTEM_PROMPT (§9), ask/memo message builders, MEMO_TEMPLATE
    retrieval.py              # Context dataclass + build_context()
    agent.py                  # answer_question() + generate_memo()
  schemas/agent.py            # AskRequest, AskResponse, ReportRequest, ReportOut
  services/agent.py           # ask(), create_report(), get_report() + persistence
  api/routes/agent.py         # /projects/{id}/ask, /projects/{id}/reports, /reports/{id}
  main.py                     # include agent router
backend/tests/
  fakes.py                    # FakeLLMClient test double
  test_agent_retrieval.py
  test_agent_ask.py
  test_agent_memo.py
  test_agent_api.py
backend/.env.example          # + LLM_* placeholders
```

---

### Task 1: LLM client abstraction + config + fake double

**Files:**
- Modify: `backend/app/core/config.py`
- Create: `backend/app/agent/__init__.py`, `backend/app/agent/client.py`, `backend/tests/fakes.py`
- Modify: `backend/.env.example`
- Test: `backend/tests/test_agent_client.py`

**Interfaces:**
- Produces: `LLMClient` protocol with `complete(self, system: str, user: str) -> str`; `OpenAIClient(base_url, api_key, model)`; `get_llm_client() -> LLMClient`; `FakeLLMClient(response=...)` recording `.last_system` / `.last_user`.

- [ ] **Step 1: Add the openai dependency**

Run: `cd backend && uv add openai`

- [ ] **Step 2: Extend Settings (`app/core/config.py`)**

Add these fields to `Settings` (after `static_mount`):
```python
    llm_base_url: str = "https://api.openai.com/v1"
    llm_api_key: str = ""
    llm_model: str = "gpt-4o-mini"
```

- [ ] **Step 3: Write `backend/tests/fakes.py`**

```python
class FakeLLMClient:
    """Test double for LLMClient — returns a canned response and records inputs."""

    def __init__(self, response: str = "ok") -> None:
        self.response = response
        self.last_system: str | None = None
        self.last_user: str | None = None
        self.calls = 0

    def complete(self, system: str, user: str) -> str:
        self.last_system = system
        self.last_user = user
        self.calls += 1
        return self.response
```

- [ ] **Step 4: Write the failing test `backend/tests/test_agent_client.py`**

```python
from app.agent.client import OpenAIClient, get_llm_client
from tests.fakes import FakeLLMClient


def test_fake_client_records_inputs():
    fake = FakeLLMClient(response="hello")
    assert fake.complete("sys", "usr") == "hello"
    assert fake.last_system == "sys"
    assert fake.last_user == "usr"


def test_get_llm_client_builds_openai_client():
    client = get_llm_client()
    assert isinstance(client, OpenAIClient)
    assert hasattr(client, "complete")
```

- [ ] **Step 5: Run it and confirm it fails**

Run: `cd backend && uv run pytest tests/test_agent_client.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'app.agent'`.

- [ ] **Step 6: Write `backend/app/agent/__init__.py`** (empty) and **`backend/app/agent/client.py`**

```python
from typing import Protocol

from openai import OpenAI

from app.core.config import get_settings


class LLMClient(Protocol):
    def complete(self, system: str, user: str) -> str: ...


class OpenAIClient:
    """Provider-agnostic OpenAI-compatible chat client."""

    def __init__(self, base_url: str, api_key: str, model: str) -> None:
        self._client = OpenAI(base_url=base_url, api_key=api_key or "not-set")
        self._model = model

    def complete(self, system: str, user: str) -> str:
        resp = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            temperature=0,
        )
        return resp.choices[0].message.content or ""


def get_llm_client() -> LLMClient:
    s = get_settings()
    return OpenAIClient(s.llm_base_url, s.llm_api_key, s.llm_model)
```

- [ ] **Step 7: Run tests to confirm they pass**

Run: `cd backend && uv run pytest tests/test_agent_client.py -v`
Expected: PASS (no network call — `OpenAI(...)` construction is lazy).

- [ ] **Step 8: Document the env vars (`backend/.env.example`)**

Append:
```dotenv
# LLM — any OpenAI-compatible endpoint (OpenAI, Anthropic, Google, local).
LLM_BASE_URL=https://api.openai.com/v1
LLM_API_KEY=
LLM_MODEL=gpt-4o-mini
```

- [ ] **Step 9: Review + commit**

```bash
git add backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(agent): provider-agnostic LLM client + config + test double"
```

---

### Task 2: Guardrail system prompt + message builders

**Files:**
- Create: `backend/app/agent/prompts.py`
- Test: `backend/tests/test_agent_prompts.py`

**Interfaces:**
- Produces: `SYSTEM_PROMPT: str`; `ask_user_message(question: str, context: str) -> str`; `MEMO_TEMPLATE: str`; `memo_user_message(report_type: str, context: str) -> str`.

- [ ] **Step 1: Write the failing test `backend/tests/test_agent_prompts.py`**

```python
from app.agent.prompts import SYSTEM_PROMPT, ask_user_message, memo_user_message


def test_system_prompt_encodes_guardrails():
    for phrase in ["cite evidence", "human review", "investment advice", "only from"]:
        assert phrase.lower() in SYSTEM_PROMPT.lower()


def test_ask_message_embeds_question_and_context():
    msg = ask_user_message("What changed?", "EVIDENCE: ev_1 ...")
    assert "What changed?" in msg
    assert "ev_1" in msg
    assert "json" in msg.lower()  # asks for a structured answer


def test_memo_message_embeds_report_type_and_context():
    msg = memo_user_message("investment_monitoring", "EVIDENCE: ev_1 ...")
    assert "investment_monitoring" in msg
    assert "Executive Summary" in msg  # the Appendix B skeleton
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `cd backend && uv run pytest tests/test_agent_prompts.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `backend/app/agent/prompts.py`**

```python
SYSTEM_PROMPT = (
    "You are Canopy, an environmental finance evidence assistant.\n"
    "Answer only from the supplied project evidence, metrics, methodology, and report "
    "context.\n"
    "Do not infer facts from raw imagery unless a structured evidence item states the "
    "finding.\n"
    "Separate observed evidence, modelled/proxy indicators, and unsupported conclusions.\n"
    "Always cite the evidence IDs you used in the answer.\n"
    "State uncertainty and limitations clearly.\n"
    "If the evidence is insufficient, say what is missing and recommend human review.\n"
    "Do not provide legal, audit, regulatory, carbon-verification, or investment advice."
)

_ASK_FORMAT = (
    "Respond ONLY with a JSON object with these keys:\n"
    '  "answer": string,\n'
    '  "evidence_used": array of evidence IDs you cited,\n'
    '  "confidence": one of "high" | "medium" | "low",\n'
    '  "limitations": array of strings,\n'
    '  "unsupported_claims_refused": array of strings for anything the evidence '
    "cannot support."
)

MEMO_TEMPLATE = (
    "# Canopy Monitoring Memo\n\n"
    "## 1. Executive Summary\n"
    "## 2. Key Observations (cite evidence IDs)\n"
    "## 3. Risk and Compliance Relevance\n"
    "## 4. Evidence Table (ID | Observation | Source | Method | Confidence | Limitation)\n"
    "## 5. Limitations\n"
    "## 6. Recommended Next Review"
)


def ask_user_message(question: str, context: str) -> str:
    return f"QUESTION:\n{question}\n\nAVAILABLE EVIDENCE:\n{context}\n\n{_ASK_FORMAT}"


def memo_user_message(report_type: str, context: str) -> str:
    return (
        f"Generate a '{report_type}' memo in Markdown, filling this skeleton exactly and "
        f"citing evidence IDs inline. Use only the evidence below.\n\n"
        f"{MEMO_TEMPLATE}\n\nAVAILABLE EVIDENCE:\n{context}"
    )
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `cd backend && uv run pytest tests/test_agent_prompts.py -v`
Expected: PASS.

- [ ] **Step 5: Review + commit**

```bash
git add backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(agent): guardrail system prompt + ask/memo message builders"
```

---

### Task 3: Evidence retrieval / context builder

**Files:**
- Create: `backend/app/agent/retrieval.py`
- Test: `backend/tests/test_agent_retrieval.py`

**Interfaces:**
- Consumes: models from Plan 1; `seed` fixture from `conftest`.
- Produces: `Context` dataclass with `text: str` and `evidence_ids: list[str]`; `build_context(db: Session, project_id: str, allowed_evidence_ids: list[str] | None = None) -> Context` (raises `NotFound` if the project is unknown).

- [ ] **Step 1: Write the failing test `backend/tests/test_agent_retrieval.py`**

```python
from app.agent.retrieval import build_context


def test_context_includes_evidence_ids_and_metrics(db_session, seed):
    seed()
    ctx = build_context(db_session, "nur_navoi_solar")
    assert ctx.evidence_ids  # non-empty
    assert ctx.evidence_ids[0] in ctx.text
    assert "vegetation_change_percent" in ctx.text


def test_allowed_evidence_ids_filters_context(db_session, seed):
    seed()
    full = build_context(db_session, "nur_navoi_solar")
    scoped = build_context(db_session, "nur_navoi_solar", allowed_evidence_ids=[])
    assert full.evidence_ids
    assert scoped.evidence_ids == []
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `cd backend && uv run pytest tests/test_agent_retrieval.py -v`
Expected: FAIL — module not found.

- [ ] **Step 3: Write `backend/app/agent/retrieval.py`**

```python
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EvidenceItem, Metric, Observation
from app.services.projects import get_project


@dataclass
class Context:
    text: str
    evidence_ids: list[str]


def build_context(
    db: Session, project_id: str, allowed_evidence_ids: list[str] | None = None
) -> Context:
    project = get_project(db, project_id)  # 404 if unknown
    evidence = list(
        db.scalars(
            select(EvidenceItem).join(Observation).where(Observation.project_id == project_id)
        )
    )
    if allowed_evidence_ids is not None:
        allowed = set(allowed_evidence_ids)
        evidence = [e for e in evidence if e.id in allowed]
    metrics = {
        m.observation_id: m
        for m in db.scalars(
            select(Metric).join(Observation).where(Observation.project_id == project_id)
        )
    }

    lines = [
        f"PROJECT {project.id}: {project.name} ({project.asset_type}); "
        f"screening={project.screening_status}; risk={project.risk_score}/{project.risk_band}; "
        f"finding={project.main_finding}",
    ]
    for ev in evidence:
        metric = metrics.get(ev.observation_id)
        metric_txt = f"{metric.metric_name}={metric.value}" if metric else "n/a"
        lines.append(
            f"EVIDENCE {ev.id}: source={ev.source_name}; method={ev.method_id}; "
            f"metric={metric_txt}; confidence={ev.confidence}; "
            f"financial_relevance={ev.financial_relevance}; "
            f"limitations={'; '.join(ev.limitations or [])}"
        )
    return Context(text="\n".join(lines), evidence_ids=[e.id for e in evidence])
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `cd backend && uv run pytest tests/test_agent_retrieval.py -v`
Expected: PASS.

- [ ] **Step 5: Review + commit**

```bash
git add backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(agent): deterministic evidence context builder"
```

---

### Task 4: Agent schemas + `answer_question` (the ask brain)

**Files:**
- Create: `backend/app/schemas/agent.py`, `backend/app/agent/agent.py`
- Test: `backend/tests/test_agent_ask.py`

**Interfaces:**
- Produces schemas: `AskRequest(question: str, report_style: str = "investment_monitoring", allowed_evidence_ids: list[str] | None = None)`; `AskResponse(answer: str, evidence_used: list[str] = [], confidence: str = "low", limitations: list[str] = [], unsupported_claims_refused: list[str] = [])`; `ReportRequest(report_type: str = "investment_monitoring")`; `ReportOut(id, project_id, report_type, content, evidence_ids: list[str], generated_at)` (with `from_attributes`, mapping `evidence_ids` from `evidence_ids_json`).
- Produces: `answer_question(db, client: LLMClient, project_id, question, allowed_evidence_ids=None) -> AskResponse` (parses the LLM's JSON; falls back to a low-confidence wrapper on unparseable output).

- [ ] **Step 1: Write `backend/app/schemas/agent.py`**

```python
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AskRequest(BaseModel):
    question: str
    report_style: str = "investment_monitoring"
    allowed_evidence_ids: list[str] | None = None


class AskResponse(BaseModel):
    answer: str
    evidence_used: list[str] = []
    confidence: str = "low"
    limitations: list[str] = []
    unsupported_claims_refused: list[str] = []


class ReportRequest(BaseModel):
    report_type: str = "investment_monitoring"


class ReportOut(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    project_id: str
    report_type: str
    content: str | None = None
    evidence_ids: list[str] = Field(default=[], validation_alias="evidence_ids_json")
    generated_at: datetime
```

- [ ] **Step 2: Write the failing test `backend/tests/test_agent_ask.py`**

```python
import json

from app.agent.agent import answer_question
from tests.fakes import FakeLLMClient


def test_answer_question_parses_and_passes_guardrails(db_session, seed):
    seed()
    payload = json.dumps(
        {"answer": "Site build-out is visible.", "evidence_used": ["nur_navoi_solar_ev_0"],
         "confidence": "medium", "limitations": ["no ground truth"], "unsupported_claims_refused": []}
    )
    fake = FakeLLMClient(response=payload)
    result = answer_question(db_session, fake, "nur_navoi_solar", "What changed?")
    assert result.answer.startswith("Site build-out")
    assert result.evidence_used == ["nur_navoi_solar_ev_0"]
    assert "Canopy" in (fake.last_system or "")           # guardrail prompt reached the client
    assert "nur_navoi_solar_ev_0" in (fake.last_user or "")  # evidence context reached the client


def test_answer_question_falls_back_on_unparseable_output(db_session, seed):
    seed()
    fake = FakeLLMClient(response="not json at all")
    result = answer_question(db_session, fake, "nur_navoi_solar", "What changed?")
    assert result.answer == "not json at all"
    assert result.confidence == "low"
    assert result.evidence_used == []
```

- [ ] **Step 3: Run it and confirm it fails**

Run: `cd backend && uv run pytest tests/test_agent_ask.py -v`
Expected: FAIL — `app.agent.agent` not found.

- [ ] **Step 4: Write `backend/app/agent/agent.py`**

```python
import json

from sqlalchemy.orm import Session

from app.agent.client import LLMClient
from app.agent.prompts import SYSTEM_PROMPT, ask_user_message
from app.agent.retrieval import build_context
from app.schemas.agent import AskResponse


def answer_question(
    db: Session,
    client: LLMClient,
    project_id: str,
    question: str,
    allowed_evidence_ids: list[str] | None = None,
) -> AskResponse:
    ctx = build_context(db, project_id, allowed_evidence_ids)
    raw = client.complete(SYSTEM_PROMPT, ask_user_message(question, ctx.text))
    try:
        data = json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return AskResponse(
            answer=raw,
            confidence="low",
            limitations=["The assistant response was not structured; treat with caution."],
        )
    # Keep only evidence IDs that actually exist in the retrieved context.
    used = [e for e in data.get("evidence_used", []) if e in ctx.evidence_ids]
    return AskResponse(
        answer=data.get("answer", ""),
        evidence_used=used,
        confidence=data.get("confidence", "low"),
        limitations=data.get("limitations", []),
        unsupported_claims_refused=data.get("unsupported_claims_refused", []),
    )
```

- [ ] **Step 5: Run tests to confirm they pass**

Run: `cd backend && uv run pytest tests/test_agent_ask.py -v`
Expected: PASS.

- [ ] **Step 6: Review + commit**

```bash
git add backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(agent): bounded evidence-cited answer_question + agent schemas"
```

---

### Task 5: `generate_memo` (the report brain)

**Files:**
- Modify: `backend/app/agent/agent.py`
- Test: `backend/tests/test_agent_memo.py`

**Interfaces:**
- Produces: `generate_memo(db, client: LLMClient, project_id, report_type) -> tuple[str, list[str]]` — returns `(markdown_content, evidence_ids_used)`; evidence IDs are the retrieved context IDs (the memo is grounded in exactly those).

- [ ] **Step 1: Write the failing test `backend/tests/test_agent_memo.py`**

```python
from app.agent.agent import generate_memo
from tests.fakes import FakeLLMClient


def test_generate_memo_returns_content_and_evidence(db_session, seed):
    seed()
    fake = FakeLLMClient(response="# Canopy Monitoring Memo\n... [nur_navoi_solar_ev_0]")
    content, evidence_ids = generate_memo(
        db_session, fake, "nur_navoi_solar", "investment_monitoring"
    )
    assert content.startswith("# Canopy Monitoring Memo")
    assert "nur_navoi_solar_ev_0" in evidence_ids
    assert "Executive Summary" in (fake.last_user or "")   # skeleton reached the client
    assert "Canopy" in (fake.last_system or "")            # guardrails applied
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `cd backend && uv run pytest tests/test_agent_memo.py -v`
Expected: FAIL — `cannot import name 'generate_memo'`.

- [ ] **Step 3: Add `generate_memo` to `backend/app/agent/agent.py`**

Add the import and function:
```python
from app.agent.prompts import SYSTEM_PROMPT, ask_user_message, memo_user_message


def generate_memo(
    db: Session, client: LLMClient, project_id: str, report_type: str
) -> tuple[str, list[str]]:
    ctx = build_context(db, project_id)
    content = client.complete(SYSTEM_PROMPT, memo_user_message(report_type, ctx.text))
    return content, ctx.evidence_ids
```
(Adjust the existing `from app.agent.prompts import ...` line to include `memo_user_message`.)

- [ ] **Step 4: Run tests to confirm they pass**

Run: `cd backend && uv run pytest tests/test_agent_memo.py -v`
Expected: PASS.

- [ ] **Step 5: Review + commit**

```bash
git add backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(agent): finance-memo generation grounded in evidence"
```

---

### Task 6: Service layer + persistence

**Files:**
- Create: `backend/app/services/agent.py`
- Test: `backend/tests/test_agent_service.py`

**Interfaces:**
- Produces: `ask(db, client, project_id, req: AskRequest) -> AskResponse` (also writes a `QaLog` row); `create_report(db, client, project_id, req: ReportRequest) -> ReportOut` (writes a `Report` row with a stable id); `get_report(db, report_id) -> Report` (raises `NotFound`).

- [ ] **Step 1: Write the failing test `backend/tests/test_agent_service.py`**

```python
import json

from app.models import QaLog, Report
from app.schemas.agent import AskRequest, ReportRequest
from app.services import agent as svc
from tests.fakes import FakeLLMClient


def test_ask_persists_qa_log(db_session, seed):
    seed()
    fake = FakeLLMClient(response=json.dumps({"answer": "a", "evidence_used": [], "confidence": "low"}))
    out = svc.ask(db_session, fake, "nur_navoi_solar", AskRequest(question="q?"))
    assert out.answer == "a"
    assert db_session.query(QaLog).filter_by(project_id="nur_navoi_solar").count() == 1


def test_create_and_get_report(db_session, seed):
    seed()
    fake = FakeLLMClient(response="# Canopy Monitoring Memo")
    created = svc.create_report(db_session, fake, "nur_navoi_solar", ReportRequest())
    assert created.content.startswith("# Canopy Monitoring Memo")
    assert db_session.query(Report).count() == 1
    fetched = svc.get_report(db_session, created.id)
    assert fetched.id == created.id
```

- [ ] **Step 2: Run it and confirm it fails**

Run: `cd backend && uv run pytest tests/test_agent_service.py -v`
Expected: FAIL — `app.services.agent` not found.

- [ ] **Step 3: Write `backend/app/services/agent.py`**

```python
from sqlalchemy.orm import Session

from app.agent.agent import answer_question, generate_memo
from app.agent.client import LLMClient
from app.core.config import get_settings
from app.core.errors import NotFound
from app.models import QaLog, Report
from app.schemas.agent import AskRequest, AskResponse, ReportOut, ReportRequest


def ask(db: Session, client: LLMClient, project_id: str, req: AskRequest) -> AskResponse:
    result = answer_question(db, client, project_id, req.question, req.allowed_evidence_ids)
    count = db.query(QaLog).filter_by(project_id=project_id).count()
    db.add(
        QaLog(
            id=f"{project_id}_qa_{count}",
            project_id=project_id,
            question=req.question,
            answer=result.answer,
            evidence_ids_json=result.evidence_used,
            model=get_settings().llm_model,
        )
    )
    db.flush()
    return result


def create_report(
    db: Session, client: LLMClient, project_id: str, req: ReportRequest
) -> ReportOut:
    content, evidence_ids = generate_memo(db, client, project_id, req.report_type)
    count = db.query(Report).filter_by(project_id=project_id).count()
    report = Report(
        id=f"{project_id}_report_{count}",
        project_id=project_id,
        report_type=req.report_type,
        evidence_ids_json=evidence_ids,
        content=content,
    )
    db.add(report)
    db.flush()
    return ReportOut.model_validate(report)


def get_report(db: Session, report_id: str) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise NotFound(f"report {report_id} not found")
    return report
```

- [ ] **Step 4: Run tests to confirm they pass**

Run: `cd backend && uv run pytest tests/test_agent_service.py -v`
Expected: PASS.

- [ ] **Step 5: Review + commit**

```bash
git add backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(agent): service layer persisting Q&A logs and reports"
```

---

### Task 7: Routes + dependency wiring + API tests

**Files:**
- Create: `backend/app/api/routes/agent.py`
- Modify: `backend/app/main.py` (include the router)
- Test: `backend/tests/test_agent_api.py`

**Interfaces:**
- Produces routes: `POST /projects/{project_id}/ask -> AskResponse`; `POST /projects/{project_id}/reports -> ReportOut`; `GET /reports/{report_id} -> ReportOut`. All resolve the LLM client via `Depends(get_llm_client)` so tests can override it.

- [ ] **Step 1: Write `backend/app/api/routes/agent.py`**

```python
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.agent.client import LLMClient, get_llm_client
from app.core.db import get_db
from app.schemas.agent import AskRequest, AskResponse, ReportOut, ReportRequest
from app.services import agent as svc

router = APIRouter(tags=["agent"])


@router.post("/projects/{project_id}/ask", response_model=AskResponse)
def ask(
    project_id: str,
    req: AskRequest,
    db: Session = Depends(get_db),
    client: LLMClient = Depends(get_llm_client),
):
    return svc.ask(db, client, project_id, req)


@router.post("/projects/{project_id}/reports", response_model=ReportOut)
def create_report(
    project_id: str,
    req: ReportRequest,
    db: Session = Depends(get_db),
    client: LLMClient = Depends(get_llm_client),
):
    return svc.create_report(db, client, project_id, req)


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: str, db: Session = Depends(get_db)):
    return svc.get_report(db, report_id)
```

- [ ] **Step 2: Wire the router into `app/main.py`**

Add the import with the other route imports:
```python
    from app.api.routes import agent as agent_routes
```
And include it alongside the others:
```python
    app.include_router(agent_routes.router)
```

- [ ] **Step 3: Write the failing test `backend/tests/test_agent_api.py`**

```python
import json

from app.agent.client import get_llm_client
from tests.fakes import FakeLLMClient


def _use_fake(client_app, response: str) -> FakeLLMClient:
    fake = FakeLLMClient(response=response)
    client_app.app.dependency_overrides[get_llm_client] = lambda: fake
    return fake


def test_ask_endpoint_returns_cited_answer(client, seed):
    seed()
    _use_fake(
        client,
        json.dumps({"answer": "Build-out visible.", "evidence_used": ["nur_navoi_solar_ev_0"],
                    "confidence": "medium", "limitations": [], "unsupported_claims_refused": []}),
    )
    body = client.post("/projects/nur_navoi_solar/ask", json={"question": "What changed?"}).json()
    assert body["evidence_used"] == ["nur_navoi_solar_ev_0"]


def test_ask_unknown_project_404(client):
    _use_fake(client, json.dumps({"answer": "x"}))
    body = client.post("/projects/missing/ask", json={"question": "q"}).json()
    assert body["error"]["code"] == "not_found"


def test_report_roundtrip(client, seed):
    seed()
    _use_fake(client, "# Canopy Monitoring Memo\n...")
    created = client.post("/projects/nur_navoi_solar/reports", json={}).json()
    assert created["content"].startswith("# Canopy Monitoring Memo")
    fetched = client.get(f"/reports/{created['id']}").json()
    assert fetched["id"] == created["id"]
```

Note: the `client` fixture exposes the app at `client.app` (Starlette `TestClient`), so `client.app.dependency_overrides` works.

- [ ] **Step 4: Run tests to confirm they pass**

Run: `cd backend && uv run pytest tests/test_agent_api.py -v`
Expected: PASS.

- [ ] **Step 5: Run the full suite + gate**

Run: `cd backend && uv run ruff check . && uv run ruff format --check . && uv run mypy app && uv run pytest -q`
Expected: all clean, all pass.

- [ ] **Step 6: (Optional) live smoke test — only if `LLM_API_KEY` is set**

```bash
# Set LLM_BASE_URL / LLM_API_KEY / LLM_MODEL in backend/.env first.
cd backend && uv run uvicorn app.main:app --port 8001 &
sleep 2
curl -s -X POST localhost:8001/projects/nur_navoi_solar/ask \
  -H 'content-type: application/json' \
  -d '{"question":"What should a green-bond investor flag from the latest evidence?"}'
kill %1
```
Expected: a JSON `AskResponse` with a cited answer. (Skipped when no key is configured — all behaviour is covered by the fake-client tests.)

- [ ] **Step 7: Review + commit**

```bash
git add backend/
git write-tree > .git/canopy-review-marker
git commit -m "feat(agent): /ask, /reports, /reports/{id} endpoints with injectable LLM client"
```

---

## Self-Review

**Spec coverage (spec §7–§8):**
- §7 `POST /projects/{id}/ask` → Tasks 4, 6, 7. ✅
- §7 `POST /projects/{id}/reports` + `GET /reports/{id}` → Tasks 5, 6, 7. ✅
- §8 provider-agnostic OpenAI-compatible client + BYOK → Task 1. ✅
- §8 deterministic retrieval by `project_id` + `allowed_evidence_ids` → Task 3 (+ used in 4). ✅
- §8 guardrails (cite IDs, uncertainty, refusals, human review) → Task 2 system prompt; enforced in the `answer_question` parse (evidence IDs filtered to retrieved set). ✅
- §8 memo generation from the Appendix B skeleton → Tasks 2 (template) + 5. ✅
- Traceability / audit trail (`qa_logs`, `reports.evidence_ids_json`) → Task 6. ✅
- pgvector semantic retrieval → explicitly deferred (Global Constraints). ✅

**Placeholder scan:** no TBD/TODO; every code step is complete; the one optional live step is clearly gated on a key. ✅

**Type consistency:** `LLMClient.complete(system, user) -> str` is used identically by `OpenAIClient`, `FakeLLMClient`, `answer_question`, and `generate_memo`. `build_context(...) -> Context(text, evidence_ids)` is consumed consistently. `AskRequest`/`AskResponse`/`ReportRequest`/`ReportOut` names match across schemas, services, and routes. `ReportOut.evidence_ids` maps from `Report.evidence_ids_json` via `validation_alias`. ✅

**Deferred to Plan 3:** the frontend Ask Canopy chat + Generate Memo screens consume these endpoints; PDF export and pgvector retrieval remain stretch.
