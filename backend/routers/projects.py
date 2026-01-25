# routers/projects.py
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.schemas import Project, ProjectCreate
from backend.database import get_db
from backend import models

router = APIRouter(prefix="/projects", tags=["projects"])


def _serialize_project(project: ProjectCreate) -> dict:
    """Convert Pydantic model to dict with serialized complex types."""
    data = project.model_dump()
    # Convert enum to value string
    data["sector"] = project.sector.value if hasattr(project.sector, 'value') else project.sector
    data["stage"] = project.stage.value if hasattr(project.stage, 'value') else project.stage
    # Convert dict to JSON string
    data["attachments"] = json.dumps(project.attachments) if project.attachments else None
    return data


def _deserialize_project(db_project: models.Project) -> Project:
    """Convert database model to Pydantic model."""
    attachments = json.loads(db_project.attachments) if db_project.attachments else None
    return Project(
        id=db_project.id,
        name=db_project.name,
        sector=db_project.sector,
        country=db_project.country,
        region=db_project.region,
        gps_location=db_project.gps_location,
        stage=db_project.stage,
        estimated_capex=db_project.estimated_capex,
        funding_gap=db_project.funding_gap,
        timeline_fid=db_project.timeline_fid,
        timeline_cod=db_project.timeline_cod,
        revenue_model=db_project.revenue_model,
        offtaker=db_project.offtaker,
        tariff_mechanism=db_project.tariff_mechanism,
        concession_length=db_project.concession_length,
        fx_exposure=db_project.fx_exposure,
        political_risk_mitigation=db_project.political_risk_mitigation,
        sovereign_support=db_project.sovereign_support,
        technology=db_project.technology,
        epc_status=db_project.epc_status,
        land_acquisition_status=db_project.land_acquisition_status,
        esg_category=db_project.esg_category,
        permits_status=db_project.permits_status,
        attachments=attachments,
        created_at=db_project.created_at,
        updated_at=db_project.updated_at
    )


@router.post("/", response_model=Project)
def create(project: ProjectCreate, db: Session = Depends(get_db)):
    """Create a new project."""
    data = _serialize_project(project)
    db_project = models.Project(**data)
    db.add(db_project)
    db.commit()
    db.refresh(db_project)
    return _deserialize_project(db_project)


@router.get("/{project_id}", response_model=Project)
def read(project_id: int, db: Session = Depends(get_db)):
    """Get a project by ID."""
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")
    return _deserialize_project(db_project)


@router.get("/", response_model=List[Project])
def list_projects(
    skip: int = 0,
    limit: int = 100,
    sector: str = None,
    country: str = None,
    stage: str = None,
    db: Session = Depends(get_db)
):
    """List projects with optional filtering."""
    query = db.query(models.Project)

    if sector:
        query = query.filter(models.Project.sector == sector)
    if country:
        query = query.filter(models.Project.country == country)
    if stage:
        query = query.filter(models.Project.stage == stage)

    db_projects = query.offset(skip).limit(limit).all()
    return [_deserialize_project(p) for p in db_projects]
