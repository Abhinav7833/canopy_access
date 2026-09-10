from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.db import get_db
from app.schemas.project import Dossier, Imagery, ProjectDetail, ProjectSummary
from app.services import projects as svc

router = APIRouter(prefix="/projects", tags=["projects"])


@router.get("", response_model=list[ProjectSummary])
def list_projects(db: Session = Depends(get_db)):
    return svc.list_projects(db)


@router.get("/{project_id}", response_model=ProjectDetail)
def get_project(project_id: str, db: Session = Depends(get_db)):
    return svc.get_project_detail(db, project_id)


@router.get("/{project_id}/boundary")
def get_boundary(project_id: str, db: Session = Depends(get_db)) -> dict:
    return svc.get_boundary_geojson(db, project_id)


@router.get("/{project_id}/imagery", response_model=Imagery)
def get_imagery(project_id: str, db: Session = Depends(get_db)):
    return svc.get_imagery(db, project_id)


@router.get("/{project_id}/dossier", response_model=Dossier)
def get_dossier(project_id: str, db: Session = Depends(get_db)):
    return svc.get_dossier(db, project_id)
