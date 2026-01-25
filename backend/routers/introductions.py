# routers/introductions.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.schemas import Introduction, IntroductionCreate
from backend.database import get_db
from backend import models

router = APIRouter(prefix="/introductions", tags=["introductions"])


def _serialize_introduction(intro: IntroductionCreate) -> dict:
    """Convert Pydantic model to dict with proper types for database."""
    data = intro.model_dump()
    # Convert booleans to integers for SQLite compatibility
    data["nda_executed"] = 1 if data.get("nda_executed") else 0
    data["sponsor_approved"] = 1 if data.get("sponsor_approved") else 0
    return data


def _deserialize_introduction(db_intro: models.Introduction) -> Introduction:
    """Convert database model to Pydantic model."""
    return Introduction(
        id=db_intro.id,
        investor_id=db_intro.investor_id,
        project_id=db_intro.project_id,
        message=db_intro.message,
        nda_executed=bool(db_intro.nda_executed),
        sponsor_approved=bool(db_intro.sponsor_approved),
        status=db_intro.status
    )


@router.post("/", response_model=Introduction)
def create(intro: IntroductionCreate, db: Session = Depends(get_db)):
    """Create a new introduction."""
    data = _serialize_introduction(intro)
    db_intro = models.Introduction(**data)
    db.add(db_intro)
    db.commit()
    db.refresh(db_intro)
    return _deserialize_introduction(db_intro)


@router.get("/{intro_id}", response_model=Introduction)
def read(intro_id: int, db: Session = Depends(get_db)):
    """Get an introduction by ID."""
    db_intro = db.query(models.Introduction).filter(models.Introduction.id == intro_id).first()
    if db_intro is None:
        raise HTTPException(status_code=404, detail="Introduction not found")
    return _deserialize_introduction(db_intro)
