# routers/data_rooms.py
import json
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List
from backend.schemas import DataRoom, DataRoomCreate
from backend.database import get_db
from backend import models

router = APIRouter(prefix="/data-rooms", tags=["data_rooms"])


def _serialize_data_room(room: DataRoomCreate) -> dict:
    """Convert Pydantic model to dict with serialized complex types."""
    data = room.model_dump()
    # Convert lists/dicts to strings for database storage
    data["access_users"] = ",".join(str(u) for u in room.access_users) if room.access_users else None
    data["documents"] = json.dumps(room.documents) if room.documents else None
    return data


def _deserialize_data_room(db_room: models.DataRoom) -> DataRoom:
    """Convert database model to Pydantic model."""
    access_users = [int(u) for u in db_room.access_users.split(",")] if db_room.access_users else []
    documents = json.loads(db_room.documents) if db_room.documents else {}
    return DataRoom(
        id=db_room.id,
        project_id=db_room.project_id,
        nda_required=db_room.nda_required,
        access_users=access_users,
        documents=documents,
        created_at=db_room.created_at
    )


@router.post("/", response_model=DataRoom)
def create(room: DataRoomCreate, db: Session = Depends(get_db)):
    """Create a new data room."""
    data = _serialize_data_room(room)
    db_room = models.DataRoom(**data)
    db.add(db_room)
    db.commit()
    db.refresh(db_room)
    return _deserialize_data_room(db_room)


@router.get("/{room_id}", response_model=DataRoom)
def read(room_id: int, db: Session = Depends(get_db)):
    """Get a data room by ID."""
    db_room = db.query(models.DataRoom).filter(models.DataRoom.id == room_id).first()
    if db_room is None:
        raise HTTPException(status_code=404, detail="Data room not found")
    return _deserialize_data_room(db_room)
