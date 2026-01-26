# routers/playbooks.py
"""
Playbooks router for SIRA Platform.
Handles incident response playbooks.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.schemas import PlaybookCreate, PlaybookUpdate, PlaybookResponse
from backend.crud import (
    create_playbook, get_playbook, list_playbooks,
    update_playbook, delete_playbook
)
from backend.database import get_db
from backend.auth import get_current_user
from backend.models import User

router = APIRouter(prefix="/playbooks", tags=["playbooks"])

# Roles allowed for playbook operations
PLAYBOOK_WRITE_ROLES = ["security_lead", "admin"]
PLAYBOOK_READ_ROLES = ["operator", "supervisor", "admin", "security_lead", "viewer"]


def require_write_access(current_user: User = Depends(get_current_user)) -> User:
    """Require write access for playbook operations."""
    if current_user.role not in PLAYBOOK_WRITE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to modify playbooks"
        )
    return current_user


def require_read_access(current_user: User = Depends(get_current_user)) -> User:
    """Require read access for playbook operations."""
    if current_user.role not in PLAYBOOK_READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view playbooks"
        )
    return current_user


@router.post("/", response_model=PlaybookResponse, status_code=status.HTTP_201_CREATED)
def create(
    playbook: PlaybookCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access)
):
    """Create a new playbook."""
    return create_playbook(db, playbook)


@router.get("/", response_model=List[PlaybookResponse])
def list_all(
    incident_type: Optional[str] = Query(None, description="Filter by incident type"),
    domain: Optional[str] = Query(None, description="Filter by domain"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """List all playbooks with optional filtering."""
    return list_playbooks(
        db,
        incident_type=incident_type,
        domain=domain,
        skip=skip,
        limit=limit
    )


@router.get("/{playbook_id}", response_model=PlaybookResponse)
def read(
    playbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """Get a playbook by ID."""
    db_playbook = get_playbook(db, playbook_id)
    if db_playbook is None:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return db_playbook


@router.put("/{playbook_id}", response_model=PlaybookResponse)
def update(
    playbook_id: int,
    playbook: PlaybookUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access)
):
    """Update a playbook."""
    db_playbook = update_playbook(db, playbook_id, playbook)
    if db_playbook is None:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return db_playbook


@router.delete("/{playbook_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete(
    playbook_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_write_access)
):
    """Delete a playbook."""
    success = delete_playbook(db, playbook_id)
    if not success:
        raise HTTPException(status_code=404, detail="Playbook not found")
    return None
