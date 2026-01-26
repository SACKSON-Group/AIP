# routers/evidence.py
"""
Evidence router for SIRA Platform.
Handles evidence storage with integrity verification using SHA-256 hashing.
"""
import hashlib
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.schemas import EvidenceCreate, EvidenceResponse
from backend.crud import (
    create_evidence, get_evidence, list_evidence, verify_evidence, get_case
)
from backend.database import get_db
from backend.auth import get_current_user
from backend.models import User, VerificationStatus

router = APIRouter(prefix="/evidence", tags=["evidence"])

# Roles allowed for evidence operations
EVIDENCE_CREATE_ROLES = ["operator", "supervisor", "security_lead", "admin"]
EVIDENCE_VERIFY_ROLES = ["security_lead", "admin"]
EVIDENCE_READ_ROLES = ["operator", "supervisor", "admin", "security_lead", "viewer"]


def require_create_access(current_user: User = Depends(get_current_user)) -> User:
    """Require create access for evidence operations."""
    if current_user.role not in EVIDENCE_CREATE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to upload evidence"
        )
    return current_user


def require_verify_access(current_user: User = Depends(get_current_user)) -> User:
    """Require verify access for evidence operations."""
    if current_user.role not in EVIDENCE_VERIFY_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to verify evidence"
        )
    return current_user


def require_read_access(current_user: User = Depends(get_current_user)) -> User:
    """Require read access for evidence operations."""
    if current_user.role not in EVIDENCE_READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view evidence"
        )
    return current_user


def compute_file_hash(content: str) -> str:
    """
    Compute SHA-256 hash for integrity verification.
    In production, this would hash the actual file content.
    """
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


@router.post("/", response_model=EvidenceResponse, status_code=status.HTTP_201_CREATED)
def upload(
    evidence: EvidenceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_create_access)
):
    """
    Upload evidence with automatic hash computation for integrity verification.
    The file_ref should contain the file path or reference; hash is computed automatically.
    """
    # Verify case exists
    db_case = get_case(db, evidence.case_id)
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    # Compute hash for integrity verification
    # In production, this would hash the actual file content
    file_hash = compute_file_hash(evidence.file_ref)

    return create_evidence(db, evidence, file_hash)


@router.get("/", response_model=List[EvidenceResponse])
def list_all(
    case_id: Optional[int] = Query(None, description="Filter by case ID"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """List all evidence items with optional filtering by case."""
    return list_evidence(db, case_id=case_id, skip=skip, limit=limit)


@router.get("/{evidence_id}", response_model=EvidenceResponse)
def read(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """Get evidence by ID."""
    db_evidence = get_evidence(db, evidence_id)
    if db_evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")
    return db_evidence


@router.post("/{evidence_id}/verify", response_model=EvidenceResponse)
def mark_verified(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verify_access)
):
    """Mark evidence as verified."""
    db_evidence = get_evidence(db, evidence_id)
    if db_evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")

    if db_evidence.verification_status == VerificationStatus.VERIFIED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Evidence is already verified"
        )

    return verify_evidence(db, evidence_id, "VERIFIED")


@router.post("/{evidence_id}/reject", response_model=EvidenceResponse)
def mark_rejected(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_verify_access)
):
    """Reject evidence."""
    db_evidence = get_evidence(db, evidence_id)
    if db_evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")

    return verify_evidence(db, evidence_id, "REJECTED")


@router.get("/{evidence_id}/verify-integrity")
def verify_integrity(
    evidence_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """
    Verify evidence integrity by recomputing hash.
    In production, this would compare against the stored file hash.
    """
    db_evidence = get_evidence(db, evidence_id)
    if db_evidence is None:
        raise HTTPException(status_code=404, detail="Evidence not found")

    # Recompute hash and compare
    current_hash = compute_file_hash(db_evidence.file_ref)
    stored_hash = db_evidence.file_hash

    is_valid = current_hash == stored_hash

    return {
        "evidence_id": evidence_id,
        "integrity_valid": is_valid,
        "stored_hash": stored_hash,
        "computed_hash": current_hash,
        "message": "Integrity verified" if is_valid else "Integrity check failed - file may have been modified"
    }
