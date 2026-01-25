# routers/events.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.schemas import Event, EventCreate
from backend.database import get_db
from backend import models

router = APIRouter(prefix="/events", tags=["events"])


def _serialize_event(event: EventCreate) -> dict:
    """Convert Pydantic model to dict with serialized complex types."""
    data = event.model_dump()
    # Convert list to comma-separated string for database storage
    data["projects_involved"] = ",".join(str(p) for p in event.projects_involved) if event.projects_involved else None
    return data


def _deserialize_event(db_event: models.Event) -> Event:
    """Convert database model to Pydantic model."""
    projects_involved = [int(p) for p in db_event.projects_involved.split(",")] if db_event.projects_involved else []
    return Event(
        id=db_event.id,
        name=db_event.name,
        description=db_event.description,
        event_date=db_event.event_date,
        type=db_event.type,
        projects_involved=projects_involved
    )


@router.post("/", response_model=Event)
def create(event: EventCreate, db: Session = Depends(get_db)):
    """Create a new event."""
    data = _serialize_event(event)
    db_event = models.Event(**data)
    db.add(db_event)
    db.commit()
    db.refresh(db_event)
    return _deserialize_event(db_event)


@router.get("/{event_id}", response_model=Event)
def read(event_id: int, db: Session = Depends(get_db)):
    """Get an event by ID."""
    db_event = db.query(models.Event).filter(models.Event.id == event_id).first()
    if db_event is None:
        raise HTTPException(status_code=404, detail="Event not found")
    return _deserialize_event(db_event)


@router.get("/", response_model=List[Event])
def list_events(
    skip: int = 0,
    limit: int = 100,
    event_type: str = None,
    db: Session = Depends(get_db)
):
    """List events with optional filtering."""
    query = db.query(models.Event)
    if event_type:
        query = query.filter(models.Event.type == event_type)
    db_events = query.offset(skip).limit(limit).all()
    return [_deserialize_event(e) for e in db_events]
