# routers/verifications.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.schemas import Verification, VerificationCreate
from backend.database import get_db
from backend import models

router = APIRouter(prefix="/verifications", tags=["verifications"])


def _get_level_enum(level_str: str) -> models.VerificationLevel:
    """Convert verification level string to enum."""
    for lvl in models.VerificationLevel:
        if lvl.value == level_str:
            return lvl
    try:
        return models.VerificationLevel[level_str.upper().replace(" ", "_").replace(":", "")]
    except KeyError:
        raise HTTPException(status_code=422, detail=f"Invalid verification level: {level_str}")


def _deserialize_verification(db_v: models.Verification) -> Verification:
    """Convert database model to Pydantic model."""
    level_val = db_v.level.value if hasattr(db_v.level, 'value') else str(db_v.level)
    return Verification(
        id=db_v.id,
        project_id=db_v.project_id,
        level=level_val,
        bankability=None  # Simplified - could reconstruct from individual fields
    )


@router.get("/ping")
def ping():
    """Health check for verifications service."""
    return {"ok": True}


@router.post("/", response_model=Verification)
def create(verification: VerificationCreate, db: Session = Depends(get_db)):
    """Create a new verification record for a project."""
    # Check if project exists
    project = db.query(models.Project).filter(models.Project.id == verification.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Convert level string to enum
    level_enum = _get_level_enum(verification.level)

    # Create verification record
    db_verification = models.Verification(
        project_id=verification.project_id,
        level=level_enum,
        technical_readiness=verification.bankability.technical_readiness if verification.bankability else None,
        financial_robustness=verification.bankability.financial_robustness if verification.bankability else None,
        legal_clarity=verification.bankability.legal_clarity if verification.bankability else None,
        esg_compliance=verification.bankability.esg_compliance if verification.bankability else None,
        overall_score=verification.bankability.overall_score if verification.bankability else None,
        risk_flags=",".join(verification.bankability.risk_flags) if verification.bankability and verification.bankability.risk_flags else None,
        last_verified=verification.bankability.last_verified if verification.bankability else None
    )
    db.add(db_verification)
    db.commit()
    db.refresh(db_verification)
    return _deserialize_verification(db_verification)


@router.get("/{verification_id}", response_model=Verification)
def read(verification_id: int, db: Session = Depends(get_db)):
    """Get a verification record by ID."""
    db_verification = db.query(models.Verification).filter(
        models.Verification.id == verification_id
    ).first()
    if db_verification is None:
        raise HTTPException(status_code=404, detail="Verification not found")
    return _deserialize_verification(db_verification)


@router.get("/project/{project_id}", response_model=List[Verification])
def list_by_project(project_id: int, db: Session = Depends(get_db)):
    """Get all verification records for a project."""
    # Check if project exists
    project = db.query(models.Project).filter(models.Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    db_verifications = db.query(models.Verification).filter(
        models.Verification.project_id == project_id
    ).all()
    return [_deserialize_verification(v) for v in db_verifications]


@router.get("/project/{project_id}/latest", response_model=Verification)
def get_latest(project_id: int, db: Session = Depends(get_db)):
    """Get the latest verification record for a project."""
    verification = db.query(models.Verification).filter(
        models.Verification.project_id == project_id
    ).order_by(models.Verification.id.desc()).first()

    if verification is None:
        raise HTTPException(status_code=404, detail="No verification found for project")
    return _deserialize_verification(verification)
