# routers/cases.py
"""
Cases router for SIRA Platform.
Handles incident case files with close functionality and export.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.schemas import (
    CaseCreate, CaseUpdate, CaseResponse, CaseClose, ExportPackResponse
)
from backend.crud import (
    create_case, get_case, list_cases, update_case, close_case,
    list_evidence
)
from backend.database import get_db
from backend.auth import get_current_user
from backend.models import User, CaseStatus

router = APIRouter(prefix="/cases", tags=["cases"])

# Roles allowed for case operations
CASE_CREATE_ROLES = ["security_lead", "admin", "operator"]
CASE_UPDATE_ROLES = ["security_lead", "admin", "operator"]
CASE_CLOSE_ROLES = ["security_lead", "admin"]
CASE_READ_ROLES = ["operator", "supervisor", "admin", "security_lead", "viewer"]


def require_create_access(current_user: User = Depends(get_current_user)) -> User:
    """Require create access for case operations."""
    if current_user.role not in CASE_CREATE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create cases"
        )
    return current_user


def require_update_access(current_user: User = Depends(get_current_user)) -> User:
    """Require update access for case operations."""
    if current_user.role not in CASE_UPDATE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update cases"
        )
    return current_user


def require_close_access(current_user: User = Depends(get_current_user)) -> User:
    """Require close access for case operations."""
    if current_user.role not in CASE_CLOSE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to close cases"
        )
    return current_user


def require_read_access(current_user: User = Depends(get_current_user)) -> User:
    """Require read access for case operations."""
    if current_user.role not in CASE_READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view cases"
        )
    return current_user


@router.post("/", response_model=CaseResponse, status_code=status.HTTP_201_CREATED)
def create(
    case: CaseCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_create_access)
):
    """Create a new incident case."""
    return create_case(db, case)


@router.get("/", response_model=List[CaseResponse])
def list_all(
    case_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """List all cases with optional filtering."""
    return list_cases(db, status=case_status, skip=skip, limit=limit)


@router.get("/{case_id}", response_model=CaseResponse)
def read(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """Get a case by ID."""
    db_case = get_case(db, case_id)
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")
    return db_case


@router.put("/{case_id}", response_model=CaseResponse)
def update(
    case_id: int,
    case: CaseUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_update_access)
):
    """Update a case."""
    db_case = get_case(db, case_id)
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    # Prevent updating closed cases
    if db_case.status == CaseStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot update a closed case"
        )

    return update_case(db, case_id, case)


@router.put("/{case_id}/close", response_model=CaseResponse)
def close(
    case_id: int,
    close_data: CaseClose,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_close_access)
):
    """Close a case with a closure code."""
    db_case = get_case(db, case_id)
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    if db_case.status == CaseStatus.CLOSED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Case is already closed"
        )

    return close_case(db, case_id, close_data.closure_code)


@router.get("/{case_id}/export", response_model=ExportPackResponse)
def export_pack(
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """
    Export case compliance pack.
    Returns case summary with evidence count.
    Note: In production, this would generate a PDF/ZIP file.
    """
    db_case = get_case(db, case_id)
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    # Count evidence items for this case
    evidence_items = list_evidence(db, case_id=case_id)
    evidence_count = len(evidence_items)

    return ExportPackResponse(
        message="Export pack generated successfully",
        case_id=case_id,
        case_overview=db_case.overview or "",
        case_status=db_case.status.value if db_case.status else "unknown",
        evidence_count=evidence_count
    )
