from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models import EvidenceItem


def evidence_for_project(db: Session, project_id: str) -> list[EvidenceItem]:
    return list(db.scalars(select(EvidenceItem).where(EvidenceItem.project_id == project_id)))
