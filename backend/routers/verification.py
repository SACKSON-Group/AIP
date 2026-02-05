"""
Verification System Router - V0-V3 Verification Levels with FP/LP Workflows
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
import json

from backend.database import get_db
from backend.models import (
    VerificationRequest, VerificationDocument, VerificationHistory,
    VerificationLevel, VerificationStatus, VerifierType, User, Project,
    BlockchainCertificate
)
from backend.auth import get_current_user
from backend.services.blockchain import blockchain_service
from backend.services.ai_service import ai_service, DocumentAnalysisType
from pydantic import BaseModel


router = APIRouter(prefix="/verifications", tags=["verifications"])


# ============================================================================
# SCHEMAS
# ============================================================================

class VerificationRequestCreate(BaseModel):
    project_id: int
    requested_level: str  # V0, V1, V2, V3
    notes: Optional[str] = None


class VerificationRequestUpdate(BaseModel):
    status: Optional[str] = None
    fp_review_status: Optional[str] = None
    fp_review_notes: Optional[str] = None
    lp_review_status: Optional[str] = None
    lp_review_notes: Optional[str] = None
    technical_score: Optional[int] = None
    financial_score: Optional[int] = None
    legal_score: Optional[int] = None
    esg_score: Optional[int] = None
    risk_flags: Optional[List[str]] = None


class DocumentUpload(BaseModel):
    document_name: str
    document_type: str
    description: Optional[str] = None
    file_url: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None


class ReviewSubmission(BaseModel):
    review_status: str  # approved, rejected, needs_revision
    notes: Optional[str] = None
    scores: Optional[dict] = None  # For V3 bankability screening


class VerificationRequestResponse(BaseModel):
    id: int
    project_id: int
    requested_level: str
    current_level: Optional[str]
    status: str
    fund_preparer_id: Optional[int]
    lead_partner_id: Optional[int]
    fp_review_status: Optional[str]
    lp_review_status: Optional[str]
    technical_score: Optional[int]
    financial_score: Optional[int]
    legal_score: Optional[int]
    esg_score: Optional[int]
    overall_score: Optional[float]
    risk_level: Optional[str]
    blockchain_hash: Optional[str]
    blockchain_tx: Optional[str]
    created_at: datetime
    updated_at: datetime
    completed_at: Optional[datetime]

    class Config:
        from_attributes = True


# ============================================================================
# VERIFICATION REQUEST ENDPOINTS
# ============================================================================

@router.post("/", response_model=VerificationRequestResponse)
async def create_verification_request(
    data: VerificationRequestCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Create a new verification request for a project"""

    # Verify project exists
    project = db.query(Project).filter(Project.id == data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    # Map level string to enum
    level_map = {
        "V0": VerificationLevel.V0_SUBMITTED,
        "V1": VerificationLevel.V1_SPONSOR_VERIFIED,
        "V2": VerificationLevel.V2_DOCUMENTS_VERIFIED,
        "V3": VerificationLevel.V3_BANKABILITY_SCREENED
    }

    requested_level = level_map.get(data.requested_level)
    if not requested_level:
        raise HTTPException(status_code=400, detail="Invalid verification level")

    # Define required documents per level
    required_docs = {
        VerificationLevel.V0_SUBMITTED: ["project_summary"],
        VerificationLevel.V1_SPONSOR_VERIFIED: [
            "sponsor_identity", "company_registration", "director_ids"
        ],
        VerificationLevel.V2_DOCUMENTS_VERIFIED: [
            "financial_statements", "legal_agreements", "permits", "technical_docs"
        ],
        VerificationLevel.V3_BANKABILITY_SCREENED: [
            "financial_model", "feasibility_study", "risk_assessment",
            "market_analysis", "management_cv"
        ]
    }

    verification = VerificationRequest(
        project_id=data.project_id,
        requested_level=requested_level,
        status=VerificationStatus.PENDING,
        required_documents=json.dumps(required_docs.get(requested_level, [])),
        requested_by_id=current_user.id
    )

    db.add(verification)
    db.commit()
    db.refresh(verification)

    # Create history entry
    history = VerificationHistory(
        verification_request_id=verification.id,
        action="created",
        action_by_id=current_user.id,
        new_status=VerificationStatus.PENDING.value,
        notes=f"Verification request created for level {data.requested_level}"
    )
    db.add(history)
    db.commit()

    return verification


@router.get("/", response_model=List[VerificationRequestResponse])
async def list_verification_requests(
    project_id: Optional[int] = None,
    status: Optional[str] = None,
    level: Optional[str] = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List verification requests with optional filters"""

    query = db.query(VerificationRequest)

    if project_id:
        query = query.filter(VerificationRequest.project_id == project_id)
    if status:
        query = query.filter(VerificationRequest.status == status)

    return query.order_by(VerificationRequest.created_at.desc()).all()


@router.get("/{verification_id}", response_model=VerificationRequestResponse)
async def get_verification_request(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get a specific verification request"""

    verification = db.query(VerificationRequest).filter(
        VerificationRequest.id == verification_id
    ).first()

    if not verification:
        raise HTTPException(status_code=404, detail="Verification request not found")

    return verification


# ============================================================================
# DOCUMENT ENDPOINTS
# ============================================================================

@router.post("/{verification_id}/documents")
async def upload_verification_document(
    verification_id: int,
    data: DocumentUpload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Upload a document for verification"""

    verification = db.query(VerificationRequest).filter(
        VerificationRequest.id == verification_id
    ).first()

    if not verification:
        raise HTTPException(status_code=404, detail="Verification request not found")

    # Generate document hash (simulated - would hash actual file content)
    import hashlib
    doc_hash = hashlib.sha256(
        f"{data.file_url}{datetime.utcnow().isoformat()}".encode()
    ).hexdigest()

    document = VerificationDocument(
        verification_request_id=verification_id,
        document_name=data.document_name,
        document_type=data.document_type,
        description=data.description,
        file_url=data.file_url,
        file_size=data.file_size,
        mime_type=data.mime_type,
        document_hash=doc_hash,
        uploaded_by_id=current_user.id
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    # Update submitted documents in verification request
    submitted = json.loads(verification.submitted_documents or "[]")
    submitted.append(document.id)
    verification.submitted_documents = json.dumps(submitted)
    db.commit()

    return {
        "id": document.id,
        "document_name": document.document_name,
        "document_type": document.document_type,
        "document_hash": document.document_hash,
        "uploaded_at": document.uploaded_at
    }


@router.get("/{verification_id}/documents")
async def list_verification_documents(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all documents for a verification request"""

    documents = db.query(VerificationDocument).filter(
        VerificationDocument.verification_request_id == verification_id
    ).all()

    return [
        {
            "id": doc.id,
            "document_name": doc.document_name,
            "document_type": doc.document_type,
            "description": doc.description,
            "file_url": doc.file_url,
            "status": doc.status,
            "document_hash": doc.document_hash,
            "blockchain_verified": doc.blockchain_verified,
            "uploaded_at": doc.uploaded_at
        }
        for doc in documents
    ]


# ============================================================================
# FP/LP WORKFLOW ENDPOINTS
# ============================================================================

@router.post("/{verification_id}/assign-fp")
async def assign_fund_preparer(
    verification_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a Fund Preparer (FP) to a verification request"""

    verification = db.query(VerificationRequest).filter(
        VerificationRequest.id == verification_id
    ).first()

    if not verification:
        raise HTTPException(status_code=404, detail="Verification request not found")

    # Verify user exists
    fp_user = db.query(User).filter(User.id == user_id).first()
    if not fp_user:
        raise HTTPException(status_code=404, detail="User not found")

    verification.fund_preparer_id = user_id
    verification.status = VerificationStatus.IN_PROGRESS

    # Create history entry
    history = VerificationHistory(
        verification_request_id=verification_id,
        action="fp_assigned",
        action_by_id=current_user.id,
        action_by_type=VerifierType.SYSTEM,
        notes=f"Fund Preparer assigned: User {user_id}"
    )
    db.add(history)
    db.commit()

    return {"message": "Fund Preparer assigned successfully"}


@router.post("/{verification_id}/assign-lp")
async def assign_lead_partner(
    verification_id: int,
    user_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Assign a Lead Partner (LP) to a verification request"""

    verification = db.query(VerificationRequest).filter(
        VerificationRequest.id == verification_id
    ).first()

    if not verification:
        raise HTTPException(status_code=404, detail="Verification request not found")

    verification.lead_partner_id = user_id

    # Create history entry
    history = VerificationHistory(
        verification_request_id=verification_id,
        action="lp_assigned",
        action_by_id=current_user.id,
        action_by_type=VerifierType.SYSTEM,
        notes=f"Lead Partner assigned: User {user_id}"
    )
    db.add(history)
    db.commit()

    return {"message": "Lead Partner assigned successfully"}


@router.post("/{verification_id}/fp-review")
async def submit_fp_review(
    verification_id: int,
    review: ReviewSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Fund Preparer submits their review"""

    verification = db.query(VerificationRequest).filter(
        VerificationRequest.id == verification_id
    ).first()

    if not verification:
        raise HTTPException(status_code=404, detail="Verification request not found")

    if verification.fund_preparer_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only assigned Fund Preparer can submit review"
        )

    verification.fp_review_status = review.review_status
    verification.fp_review_date = datetime.utcnow()
    verification.fp_review_notes = review.notes

    # If FP approved, update status to await LP review
    if review.review_status == "approved":
        verification.status = VerificationStatus.IN_PROGRESS

    # Create history entry
    history = VerificationHistory(
        verification_request_id=verification_id,
        action="fp_review_submitted",
        action_by_id=current_user.id,
        action_by_type=VerifierType.FUND_PREPARER,
        new_status=review.review_status,
        notes=review.notes
    )
    db.add(history)
    db.commit()

    return {"message": "FP review submitted successfully"}


@router.post("/{verification_id}/lp-review")
async def submit_lp_review(
    verification_id: int,
    review: ReviewSubmission,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Lead Partner submits their review (final approval)"""

    verification = db.query(VerificationRequest).filter(
        VerificationRequest.id == verification_id
    ).first()

    if not verification:
        raise HTTPException(status_code=404, detail="Verification request not found")

    if verification.lead_partner_id != current_user.id:
        raise HTTPException(
            status_code=403,
            detail="Only assigned Lead Partner can submit review"
        )

    # Check FP has already approved
    if verification.fp_review_status != "approved":
        raise HTTPException(
            status_code=400,
            detail="Fund Preparer must approve before Lead Partner review"
        )

    verification.lp_review_status = review.review_status
    verification.lp_review_date = datetime.utcnow()
    verification.lp_review_notes = review.notes

    # Handle scores for V3 bankability screening
    if review.scores:
        verification.technical_score = review.scores.get("technical")
        verification.financial_score = review.scores.get("financial")
        verification.legal_score = review.scores.get("legal")
        verification.esg_score = review.scores.get("esg")

        # Calculate overall score
        scores = [s for s in [
            verification.technical_score,
            verification.financial_score,
            verification.legal_score,
            verification.esg_score
        ] if s is not None]

        if scores:
            verification.overall_score = sum(scores) / len(scores)

            # Set risk level based on score
            if verification.overall_score >= 80:
                verification.risk_level = "low"
            elif verification.overall_score >= 60:
                verification.risk_level = "medium"
            elif verification.overall_score >= 40:
                verification.risk_level = "high"
            else:
                verification.risk_level = "critical"

    # Update final status
    if review.review_status == "approved":
        verification.status = VerificationStatus.APPROVED
        verification.current_level = verification.requested_level
        verification.completed_at = datetime.utcnow()

        # Register on blockchain
        try:
            metadata = blockchain_service.create_document_metadata(
                document_id=verification.id,
                document_name=f"Verification-{verification.id}",
                document_hash=f"verification_{verification.id}_{datetime.utcnow().timestamp()}",
                owner_id=verification.requested_by_id,
                verification_level=verification.requested_level.value,
                additional_data={
                    "project_id": verification.project_id,
                    "overall_score": verification.overall_score,
                    "risk_level": verification.risk_level
                }
            )

            import hashlib
            doc_hash = hashlib.sha256(
                str(metadata).encode()
            ).hexdigest()

            certificate = await blockchain_service.register_document_hash(
                doc_hash, metadata
            )

            if certificate:
                verification.blockchain_hash = certificate.document_hash
                verification.blockchain_tx = certificate.transaction_hash
                verification.blockchain_verified_at = datetime.utcnow()

                # Store certificate
                bc_cert = BlockchainCertificate(
                    certificate_id=certificate.certificate_id,
                    certificate_type="verification",
                    document_type="verification_request",
                    document_id=verification.id,
                    document_hash=certificate.document_hash,
                    network=certificate.network,
                    transaction_hash=certificate.transaction_hash,
                    block_number=certificate.block_number,
                    explorer_url=certificate.verification_url,
                    cert_metadata=json.dumps(metadata),
                    issued_to_id=verification.requested_by_id,
                    issued_by_id=current_user.id
                )
                db.add(bc_cert)

        except Exception as e:
            print(f"Blockchain registration failed: {e}")

    elif review.review_status == "rejected":
        verification.status = VerificationStatus.REJECTED
        verification.completed_at = datetime.utcnow()
    else:
        verification.status = VerificationStatus.NEEDS_REVISION

    # Create history entry
    history = VerificationHistory(
        verification_request_id=verification_id,
        action="lp_review_submitted",
        action_by_id=current_user.id,
        action_by_type=VerifierType.LEAD_PARTNER,
        previous_status=verification.status.value if verification.status else None,
        new_status=review.review_status,
        notes=review.notes
    )
    db.add(history)
    db.commit()

    return {
        "message": "LP review submitted successfully",
        "status": verification.status.value,
        "blockchain_tx": verification.blockchain_tx
    }


# ============================================================================
# HISTORY ENDPOINTS
# ============================================================================

@router.get("/{verification_id}/history")
async def get_verification_history(
    verification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get audit trail for a verification request"""

    history = db.query(VerificationHistory).filter(
        VerificationHistory.verification_request_id == verification_id
    ).order_by(VerificationHistory.created_at.desc()).all()

    return [
        {
            "id": h.id,
            "action": h.action,
            "action_by_id": h.action_by_id,
            "action_by_type": h.action_by_type.value if h.action_by_type else None,
            "previous_status": h.previous_status,
            "new_status": h.new_status,
            "notes": h.notes,
            "created_at": h.created_at
        }
        for h in history
    ]


# ============================================================================
# AI ANALYSIS ENDPOINTS
# ============================================================================

@router.post("/{verification_id}/documents/{document_id}/analyze")
async def analyze_document(
    verification_id: int,
    document_id: int,
    analysis_type: str = "summary",
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Run AI analysis on a verification document"""

    document = db.query(VerificationDocument).filter(
        VerificationDocument.id == document_id,
        VerificationDocument.verification_request_id == verification_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    # Map analysis type
    type_map = {
        "summary": DocumentAnalysisType.SUMMARY,
        "risk": DocumentAnalysisType.RISK_ANALYSIS,
        "compliance": DocumentAnalysisType.COMPLIANCE_CHECK,
        "due_diligence": DocumentAnalysisType.DUE_DILIGENCE,
        "key_terms": DocumentAnalysisType.KEY_TERMS
    }

    analysis_enum = type_map.get(analysis_type, DocumentAnalysisType.SUMMARY)

    # Simulated document text (in production, would fetch and extract)
    document_text = f"Document: {document.document_name}\nType: {document.document_type}"

    result = await ai_service.analyze_document(
        document_text,
        analysis_enum
    )

    # Store analysis result
    document.ai_analysis = json.dumps(result.content)
    document.ai_risk_score = result.confidence_score
    db.commit()

    return {
        "document_id": document_id,
        "analysis_type": analysis_type,
        "result": result.content,
        "confidence_score": result.confidence_score,
        "provider": result.provider,
        "model": result.model
    }
