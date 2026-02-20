# routers/projects.py
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from backend.schemas import Project, ProjectCreate
from backend.database import get_db
from backend import models
from backend.auth import get_current_user
from pydantic import BaseModel

router = APIRouter(prefix="/projects", tags=["projects"])


def _get_sector_enum(sector_str: str) -> models.Sector:
    """Convert sector string to enum."""
    # Try matching by value first (e.g., "Energy")
    for s in models.Sector:
        if s.value == sector_str:
            return s
    # Try matching by name (e.g., "ENERGY")
    try:
        return models.Sector[sector_str.upper()]
    except KeyError:
        raise HTTPException(status_code=422, detail=f"Invalid sector: {sector_str}")


def _get_stage_enum(stage_str: str) -> models.ProjectStage:
    """Convert stage string to enum."""
    for s in models.ProjectStage:
        if s.value == stage_str:
            return s
    try:
        return models.ProjectStage[stage_str.upper()]
    except KeyError:
        raise HTTPException(status_code=422, detail=f"Invalid stage: {stage_str}")


def _serialize_project(project: ProjectCreate) -> dict:
    """Convert Pydantic model to dict with proper enum types."""
    data = project.model_dump()
    data["sector"] = _get_sector_enum(project.sector)
    data["stage"] = _get_stage_enum(project.stage)
    data["attachments"] = json.dumps(project.attachments) if project.attachments else None
    return data


def _deserialize_project(db_project: models.Project) -> Project:
    """Convert database model to Pydantic model."""
    attachments = json.loads(db_project.attachments) if db_project.attachments else None
    # Get string value from enum
    sector_val = db_project.sector.value if hasattr(db_project.sector, 'value') else str(db_project.sector)
    stage_val = db_project.stage.value if hasattr(db_project.stage, 'value') else str(db_project.stage)

    return Project(
        id=db_project.id,
        name=db_project.name,
        sector=sector_val,
        country=db_project.country,
        region=db_project.region,
        gps_location=db_project.gps_location,
        stage=stage_val,
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
        query = query.filter(models.Project.sector == _get_sector_enum(sector))
    if country:
        query = query.filter(models.Project.country == country)
    if stage:
        query = query.filter(models.Project.stage == _get_stage_enum(stage))

    db_projects = query.offset(skip).limit(limit).all()
    return [_deserialize_project(p) for p in db_projects]


class ProjectUpdate(BaseModel):
    """Schema for updating a project - all fields optional."""
    name: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    region: Optional[str] = None
    gps_location: Optional[str] = None
    stage: Optional[str] = None
    estimated_capex: Optional[float] = None
    funding_gap: Optional[float] = None
    timeline_fid: Optional[str] = None
    timeline_cod: Optional[str] = None
    revenue_model: Optional[str] = None
    offtaker: Optional[str] = None
    tariff_mechanism: Optional[str] = None
    concession_length: Optional[int] = None
    fx_exposure: Optional[str] = None
    political_risk_mitigation: Optional[str] = None
    sovereign_support: Optional[str] = None
    technology: Optional[str] = None
    epc_status: Optional[str] = None
    land_acquisition_status: Optional[str] = None
    esg_category: Optional[str] = None
    permits_status: Optional[str] = None


@router.put("/{project_id}", response_model=Project)
def update_project(
    project_id: int,
    project_update: ProjectUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Update a project (requires authentication)."""
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    # Update fields that are provided
    update_data = project_update.model_dump(exclude_unset=True)

    for field, value in update_data.items():
        if value is not None:
            if field == "sector":
                value = _get_sector_enum(value)
            elif field == "stage":
                value = _get_stage_enum(value)
            setattr(db_project, field, value)

    db.commit()
    db.refresh(db_project)
    return _deserialize_project(db_project)


@router.delete("/{project_id}")
def delete_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """Delete a project (requires authentication)."""
    db_project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if db_project is None:
        raise HTTPException(status_code=404, detail="Project not found")

    db.delete(db_project)
    db.commit()
    return {"message": "Project deleted successfully"}
