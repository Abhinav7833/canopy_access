from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.evidence import EvidenceItemOut
from app.services import evidence as svc

router = APIRouter(prefix="/projects", tags=["evidence"])


@router.get("/{project_id}/evidence", response_model=list[EvidenceItemOut])
def evidence(project_id: str, db: Session = Depends(get_db)):
    return svc.evidence(db, project_id)
