from sqlalchemy.orm import Session

from app.models import EvidenceItem
from app.services import queries
from app.services.projects import get_project


def evidence(db: Session, project_id: str) -> list[EvidenceItem]:
    get_project(db, project_id)  # 404 if the project is unknown
    return queries.evidence_for_project(db, project_id)
