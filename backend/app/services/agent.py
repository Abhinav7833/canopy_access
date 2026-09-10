import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.agent.agent import answer_question, generate_memo
from app.agent.client import LLMClient
from app.core.config import get_settings
from app.core.errors import NotFound
from app.models import QaLog, Report
from app.schemas.agent import AskRequest, AskResponse, ReportOut, ReportRequest


def ask(db: Session, client: LLMClient, project_id: str, req: AskRequest) -> AskResponse:
    result = answer_question(db, client, project_id, req.question, req.allowed_evidence_ids)
    db.add(
        QaLog(
            id=f"{project_id}_qa_{uuid.uuid4().hex[:12]}",
            project_id=project_id,
            question=req.question,
            answer=result.answer,
            evidence_ids_json=result.evidence_used,
            model=get_settings().llm_model,
        )
    )
    db.flush()
    return result


def create_report(db: Session, client: LLMClient, project_id: str, req: ReportRequest) -> ReportOut:
    content, evidence_ids = generate_memo(db, client, project_id, req.report_type)
    report = Report(
        id=f"{project_id}_report_{uuid.uuid4().hex[:12]}",
        project_id=project_id,
        report_type=req.report_type,
        evidence_ids_json=evidence_ids,
        content=content,
    )
    db.add(report)
    db.flush()
    db.refresh(report)  # populate server-default generated_at
    return ReportOut.model_validate(report)


def get_report(db: Session, report_id: str) -> Report:
    report = db.get(Report, report_id)
    if report is None:
        raise NotFound(f"report {report_id} not found")
    return report


def get_latest_report(db: Session, project_id: str) -> ReportOut | None:
    """The most recently generated memo for a project, or None if none exists yet. Lets the
    memo screen reload a previously generated memo instead of losing it when the tab unmounts."""
    report = db.scalars(
        select(Report)
        .where(Report.project_id == project_id)
        # generated_at is the real ordering: in prod each report is its own transaction with a
        # distinct transaction_timestamp, so this returns the newest. id only breaks a tie into
        # a stable (not flickering) result — ties are impossible in prod, and the id is a random
        # suffix, so it can't stand in for insertion order if two ever share a timestamp.
        .order_by(Report.generated_at.desc(), Report.id.desc())
        .limit(1)
    ).first()
    return ReportOut.model_validate(report) if report is not None else None
