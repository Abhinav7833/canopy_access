"""End-to-end persistence: a report written through get_db()'s commit is visible
in a brand-new session.

This deliberately does NOT use the rolled-back `db_session` fixture — it drives
committing sessions on the test database, so it genuinely exercises cross-session
persistence (the failure mode the shared-transaction fixture masked in review
finding #1). No LLM key is required: the client is faked.
"""

import json
from pathlib import Path

from scripts.seed import _seed_methodologies, seed_project
from sqlalchemy import create_engine, delete
from sqlalchemy.orm import sessionmaker

import app.core.db as db_module
from app.core.config import get_settings
from app.models import Project, Report
from app.schemas.agent import ReportRequest
from app.services import agent as svc
from tests.fakes import FakeLLMClient

_PID = "persist_probe"
_FIXTURE = Path(__file__).resolve().parents[2] / "seed_data" / "projects" / "nur_navoi_solar.json"


def _cleanup(engine) -> None:
    session = sessionmaker(bind=engine)()
    try:
        # Reports have no cascade FK; delete them first, then the project cascades the rest.
        session.execute(delete(Report).where(Report.project_id == _PID))
        session.execute(delete(Project).where(Project.id == _PID))
        session.commit()
    finally:
        session.close()


def test_report_persists_across_sessions(monkeypatch):
    engine = create_engine(get_settings().test_database_url, future=True)
    monkeypatch.setattr(
        db_module, "SessionLocal", sessionmaker(bind=engine, expire_on_commit=False)
    )
    fixture = json.loads(_FIXTURE.read_text())
    fixture["id"] = _PID
    fake = FakeLLMClient(response="# Canopy Monitoring Memo")

    try:
        # Request 1: seed + create a report through the real get_db() lifecycle,
        # which commits when the dependency generator is exhausted.
        gen = db_module.get_db()
        db1 = next(gen)
        _seed_methodologies(db1)  # evidence.method_id FKs to methodologies
        seed_project(db1, fixture)
        report_id = svc.create_report(db1, fake, _PID, ReportRequest()).id
        next(gen, None)  # runs get_db()'s commit + close

        # Request 2: a brand-new session must see the committed report.
        gen2 = db_module.get_db()
        db2 = next(gen2)
        fetched = svc.get_report(db2, report_id)
        assert fetched.id == report_id
        assert (fetched.content or "").startswith("# Canopy Monitoring Memo")
        next(gen2, None)
    finally:
        _cleanup(engine)
        engine.dispose()
