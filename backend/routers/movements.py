# routers/movements.py
"""
Movements router for SIRA Platform.
Handles shipping movement tracking with RBAC.
"""
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from backend.schemas import (
    MovementCreate, MovementUpdate, MovementResponse,
    ShipmentEventCreate, ShipmentEventResponse
)
from backend.crud import (
    create_movement, get_movement, list_movements,
    update_movement, delete_movement,
    create_shipment_event, get_shipment_event, list_shipment_events
)
from backend.database import get_db
from backend.auth import get_current_user
from backend.models import User

router = APIRouter(prefix="/movements", tags=["movements"])

# Roles allowed to create/update movements
MOVEMENT_WRITE_ROLES = ["operator", "supervisor", "admin"]
MOVEMENT_READ_ROLES = ["operator", "supervisor", "admin", "security_lead", "viewer"]


def require_write_access(current_user: User = Depends(get_current_user)) -> User:
    """Require write access for movement operations."""
    if current_user.role not in MOVEMENT_WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to modify movements"
        )
    return current_user


def require_read_access(current_user: User = Depends(get_current_user)) -> User:
    """Require read access for movement operations."""
    if current_user.role not in MOVEMENT_READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view movements"
        )
    return current_user


@router.post("/", response_model=MovementResponse, status_code=status.HTTP_201_CREATED)
def create(
    movement: MovementCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access)
):
    """Create a new shipping movement."""
    return create_movement(db, movement)


@router.get("/", response_model=List[MovementResponse])
def list_all(
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """List all movements with pagination."""
    return list_movements(db, skip=skip, limit=limit)


@router.get("/{movement_id}", response_model=MovementResponse)
def read(
    movement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """Get a movement by ID."""
    db_movement = get_movement(db, movement_id)
    if db_movement is None:
        raise HTTPException(status_code=404, detail="Movement not found")
    return db_movement


@router.put("/{movement_id}", response_model=MovementResponse)
def update(
    movement_id: int,
    movement: MovementUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access)
):
    """Update a movement."""
    db_movement = update_movement(db, movement_id, movement)
    if db_movement is None:
        raise HTTPException(status_code=404, detail="Movement not found")
    return db_movement


@router.delete("/{movement_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    movement_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access)
):
    """Delete a movement."""
    success = delete_movement(db, movement_id)
    if not success:
        raise HTTPException(status_code=404, detail="Movement not found")
    return None


# Shipment Events endpoints (nested under movements)
@router.post("/{movement_id}/events", response_model=ShipmentEventResponse, status_code=status.HTTP_201_CREATED)
def create_event(
    movement_id: int,
    event: ShipmentEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access)
):
    """Create a new event for a movement."""
    # Verify movement exists
    db_movement = get_movement(db, movement_id)
    if db_movement is None:
        raise HTTPException(status_code=404, detail="Movement not found")

    # Ensure event is linked to the correct movement
    event_data = event.model_dump()
    event_data["movement_id"] = movement_id

    return create_shipment_event(db, event_data)


@router.get("/{movement_id}/events", response_model=List[ShipmentEventResponse])
def list_events(
    movement_id: int,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """List all events for a movement."""
    # Verify movement exists
    db_movement = get_movement(db, movement_id)
    if db_movement is None:
        raise HTTPException(status_code=404, detail="Movement not found")

    return list_shipment_events(db, movement_id=movement_id, skip=skip, limit=limit)


@router.get("/{movement_id}/events/{event_id}", response_model=ShipmentEventResponse)
def read_event(
    movement_id: int,
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """Get a specific event for a movement."""
    db_event = get_shipment_event(db, event_id)
    if db_event is None or db_event.movement_id != movement_id:
        raise HTTPException(status_code=404, detail="Event not found")
    return db_event
