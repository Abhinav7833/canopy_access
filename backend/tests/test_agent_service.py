import json

from app.models import QaLog, Report
from app.schemas.agent import AskRequest, ReportRequest
from app.services import agent as svc
from tests.fakes import FakeLLMClient


def test_ask_persists_qa_log(db_session, seed):
    seed()
    fake = FakeLLMClient(
        response=json.dumps({"answer": "a", "evidence_used": [], "confidence": "low"})
    )
    out = svc.ask(db_session, fake, "nur_navoi_solar", AskRequest(question="q?"))
    assert out.answer == "a"
    assert db_session.query(QaLog).filter_by(project_id="nur_navoi_solar").count() == 1


def test_create_and_get_report(db_session, seed):
    seed()
    fake = FakeLLMClient(response="# Canopy Monitoring Memo")
    created = svc.create_report(db_session, fake, "nur_navoi_solar", ReportRequest())
    assert created.content.startswith("# Canopy Monitoring Memo")
    assert created.evidence_ids  # grounded in the retrieved evidence
    assert db_session.query(Report).count() == 1
    fetched = svc.get_report(db_session, created.id)
    assert fetched.id == created.id


def test_two_asks_get_distinct_ids(db_session, seed):
    seed()
    fake = FakeLLMClient(
        response=json.dumps({"answer": "a", "evidence_used": [], "confidence": "low"})
    )
    svc.ask(db_session, fake, "nur_navoi_solar", AskRequest(question="q1"))
    svc.ask(db_session, fake, "nur_navoi_solar", AskRequest(question="q2"))
    ids = [q.id for q in db_session.query(QaLog).filter_by(project_id="nur_navoi_solar").all()]
    assert len(ids) == 2
    assert len(set(ids)) == 2  # unique ids, no COUNT-based collision
