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
    assert "Executive Summary" in (fake.last_user or "")
    assert "Canopy" in (fake.last_system or "")
