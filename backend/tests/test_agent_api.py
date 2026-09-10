import json

from app.agent.client import get_llm_client
from app.core.config import Settings
from tests.fakes import FakeLLMClient


def _use_fake(test_client, response: str) -> FakeLLMClient:
    fake = FakeLLMClient(response=response)
    test_client.app.dependency_overrides[get_llm_client] = lambda: fake
    return fake


def test_ask_endpoint_returns_cited_answer(client, seed):
    seed()
    _use_fake(
        client,
        json.dumps(
            {
                "answer": "Build-out visible.",
                "evidence_used": ["nur_navoi_solar_ev_0"],
                "confidence": "medium",
                "limitations": [],
                "unsupported_claims_refused": [],
            }
        ),
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


def test_latest_report_is_null_before_any_generated(client, seed):
    seed()
    resp = client.get("/projects/nur_navoi_solar/reports/latest")
    assert resp.status_code == 200
    assert resp.json() is None


def test_latest_report_returns_most_recent(client, db_session, seed):
    from datetime import UTC, datetime, timedelta

    from app.models import Report

    seed()
    _use_fake(client, "# Canopy Monitoring Memo\nfirst")
    first = client.post("/projects/nur_navoi_solar/reports", json={}).json()
    _use_fake(client, "# Canopy Monitoring Memo\nsecond")
    second = client.post("/projects/nur_navoi_solar/reports", json={}).json()

    # The test harness runs both POSTs inside one transaction, so func.now() ties; in
    # production each POST is its own transaction with a distinct timestamp. Age the first
    # report so the ordering is exercised the way separate production transactions produce it.
    older = datetime.now(UTC) - timedelta(days=1)
    db_session.get(Report, first["id"]).generated_at = older
    db_session.flush()

    latest = client.get("/projects/nur_navoi_solar/reports/latest").json()
    # The memo screen reloads this on mount, so it must be the newest, not the first.
    assert latest["id"] == second["id"] != first["id"]
    assert latest["content"].endswith("second")


def test_deleting_a_project_cascades_to_reports_and_qa_logs(client, db_session, seed):
    # The idempotent reseed deletes the project and relies on children cascading; a leftover
    # memo or Q&A must not block it (it did before reports/qa_logs got ON DELETE CASCADE).
    from app.models import Project, QaLog, Report

    seed()
    _use_fake(client, json.dumps({"answer": "a", "confidence": "low"}))
    client.post("/projects/nur_navoi_solar/ask", json={"question": "q"})
    _use_fake(client, "# Canopy Monitoring Memo\n...")
    client.post("/projects/nur_navoi_solar/reports", json={})
    assert db_session.query(Report).filter_by(project_id="nur_navoi_solar").count() == 1
    assert db_session.query(QaLog).filter_by(project_id="nur_navoi_solar").count() == 1

    db_session.query(Project).filter_by(id="nur_navoi_solar").delete()
    db_session.flush()  # would raise ForeignKeyViolation without the cascade

    assert db_session.query(Report).filter_by(project_id="nur_navoi_solar").count() == 0
    assert db_session.query(QaLog).filter_by(project_id="nur_navoi_solar").count() == 0


def test_ask_without_llm_key_returns_503(client, seed, monkeypatch):
    seed()
    monkeypatch.setattr("app.agent.client.get_settings", lambda: Settings(llm_api_key=""))
    resp = client.post("/projects/nur_navoi_solar/ask", json={"question": "q"})
    assert resp.status_code == 503
    body = resp.json()
    assert body["error"]["code"] == "llm_not_configured"
    assert "LLM_API_KEY" in body["error"]["message"]


def test_reports_without_llm_key_returns_503(client, seed, monkeypatch):
    seed()
    monkeypatch.setattr("app.agent.client.get_settings", lambda: Settings(llm_api_key=""))
    resp = client.post("/projects/nur_navoi_solar/reports", json={})
    assert resp.status_code == 503
    assert resp.json()["error"]["code"] == "llm_not_configured"
