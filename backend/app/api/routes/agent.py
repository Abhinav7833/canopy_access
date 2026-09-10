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


@router.get("/projects/{project_id}/reports/latest", response_model=ReportOut | None)
def latest_report(project_id: str, db: Session = Depends(get_db)):
    """The most recent memo for a project, or null if none has been generated. The memo screen
    loads this on mount so a generated memo survives navigating away and back."""
    return svc.get_latest_report(db, project_id)


@router.get("/reports/{report_id}", response_model=ReportOut)
def get_report(report_id: str, db: Session = Depends(get_db)):
    return svc.get_report(db, report_id)
