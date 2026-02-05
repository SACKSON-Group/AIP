# routers/deal_rooms.py
"""
Deal Room API endpoints for project negotiations, video calls, and document collaboration
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel
import json

from backend.database import get_db
from backend import models

router = APIRouter(prefix="/deal-rooms", tags=["deal-rooms"])


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class DealRoomCreate(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    deal_value: Optional[float] = None
    deal_currency: str = "USD"
    target_close_date: Optional[str] = None
    is_video_enabled: bool = True
    is_chat_enabled: bool = True
    require_nda: bool = True


class DealRoomUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    status: Optional[str] = None
    deal_value: Optional[float] = None
    target_close_date: Optional[str] = None


class DealRoomResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    status: str
    deal_value: Optional[float]
    deal_currency: str
    target_close_date: Optional[str]
    is_video_enabled: bool
    is_chat_enabled: bool
    require_nda: bool
    created_by_id: int
    created_at: datetime
    member_count: Optional[int] = 0
    document_count: Optional[int] = 0

    class Config:
        from_attributes = True


class MemberInvite(BaseModel):
    email: str
    role: str = "member"
    can_upload: bool = True
    can_delete: bool = False
    can_invite: bool = False


class MemberResponse(BaseModel):
    id: int
    user_id: int
    role: str
    invitation_status: str
    nda_signed: bool
    joined_at: datetime
    user_email: Optional[str] = None
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


class DocumentUpload(BaseModel):
    title: str
    description: Optional[str] = None
    document_type: str = "other"
    file_name: str
    file_url: str
    file_size: Optional[int] = None
    mime_type: Optional[str] = None
    requires_signature: bool = False


class DocumentResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    document_type: str
    file_name: str
    file_url: str
    version: int
    signature_status: str
    uploaded_by_id: int
    uploaded_at: datetime

    class Config:
        from_attributes = True


class MeetingCreate(BaseModel):
    title: str
    description: Optional[str] = None
    agenda: Optional[str] = None
    scheduled_at: str
    duration_minutes: int = 60
    timezone: str = "UTC"


class MeetingResponse(BaseModel):
    id: int
    title: str
    description: Optional[str]
    scheduled_at: datetime
    duration_minutes: int
    meeting_url: Optional[str]
    status: str
    is_recorded: bool
    recording_url: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class MessageCreate(BaseModel):
    message: str
    message_type: str = "text"
    parent_id: Optional[int] = None


class MessageResponse(BaseModel):
    id: int
    user_id: int
    message: str
    message_type: str
    parent_id: Optional[int]
    is_edited: bool
    created_at: datetime
    user_name: Optional[str] = None

    class Config:
        from_attributes = True


# ============================================================================
# DEAL ROOM CRUD ENDPOINTS
# ============================================================================

@router.get("", response_model=List[DealRoomResponse])
def list_deal_rooms(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, le=100),
    status: Optional[str] = None,
    project_id: Optional[int] = None,
    db: Session = Depends(get_db)
):
    """List all deal rooms (optionally filtered)"""
    query = db.query(models.DealRoom)

    if status:
        query = query.filter(models.DealRoom.status == status)
    if project_id:
        query = query.filter(models.DealRoom.project_id == project_id)

    deal_rooms = query.offset(skip).limit(limit).all()

    # Add counts
    result = []
    for dr in deal_rooms:
        dr_dict = {
            "id": dr.id,
            "project_id": dr.project_id,
            "name": dr.name,
            "description": dr.description,
            "status": dr.status.value if hasattr(dr.status, 'value') else str(dr.status),
            "deal_value": dr.deal_value,
            "deal_currency": dr.deal_currency,
            "target_close_date": str(dr.target_close_date) if dr.target_close_date else None,
            "is_video_enabled": dr.is_video_enabled,
            "is_chat_enabled": dr.is_chat_enabled,
            "require_nda": dr.require_nda,
            "created_by_id": dr.created_by_id,
            "created_at": dr.created_at,
            "member_count": len(dr.members) if dr.members else 0,
            "document_count": len(dr.documents) if dr.documents else 0,
        }
        result.append(dr_dict)

    return result


@router.post("", response_model=DealRoomResponse, status_code=status.HTTP_201_CREATED)
def create_deal_room(
    deal_room_in: DealRoomCreate,
    db: Session = Depends(get_db)
):
    """Create a new deal room for a project"""
    # For now, use a default user ID (in production, get from auth)
    created_by_id = 1

    deal_room = models.DealRoom(
        project_id=deal_room_in.project_id,
        name=deal_room_in.name,
        description=deal_room_in.description,
        deal_value=deal_room_in.deal_value,
        deal_currency=deal_room_in.deal_currency,
        target_close_date=datetime.strptime(deal_room_in.target_close_date, "%Y-%m-%d").date() if deal_room_in.target_close_date else None,
        is_video_enabled=deal_room_in.is_video_enabled,
        is_chat_enabled=deal_room_in.is_chat_enabled,
        require_nda=deal_room_in.require_nda,
        created_by_id=created_by_id,
    )
    db.add(deal_room)
    db.commit()
    db.refresh(deal_room)

    # Add creator as owner
    member = models.DealRoomMember(
        deal_room_id=deal_room.id,
        user_id=created_by_id,
        role=models.DealRoomMemberRole.OWNER,
        invitation_status="accepted",
        can_upload=True,
        can_delete=True,
        can_invite=True,
        nda_signed=True,
    )
    db.add(member)
    db.commit()

    return {
        "id": deal_room.id,
        "project_id": deal_room.project_id,
        "name": deal_room.name,
        "description": deal_room.description,
        "status": deal_room.status.value if hasattr(deal_room.status, 'value') else str(deal_room.status),
        "deal_value": deal_room.deal_value,
        "deal_currency": deal_room.deal_currency,
        "target_close_date": str(deal_room.target_close_date) if deal_room.target_close_date else None,
        "is_video_enabled": deal_room.is_video_enabled,
        "is_chat_enabled": deal_room.is_chat_enabled,
        "require_nda": deal_room.require_nda,
        "created_by_id": deal_room.created_by_id,
        "created_at": deal_room.created_at,
        "member_count": 1,
        "document_count": 0,
    }


@router.get("/{deal_room_id}", response_model=DealRoomResponse)
def get_deal_room(deal_room_id: int, db: Session = Depends(get_db)):
    """Get a specific deal room by ID"""
    deal_room = db.query(models.DealRoom).filter(models.DealRoom.id == deal_room_id).first()
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    return {
        "id": deal_room.id,
        "project_id": deal_room.project_id,
        "name": deal_room.name,
        "description": deal_room.description,
        "status": deal_room.status.value if hasattr(deal_room.status, 'value') else str(deal_room.status),
        "deal_value": deal_room.deal_value,
        "deal_currency": deal_room.deal_currency,
        "target_close_date": str(deal_room.target_close_date) if deal_room.target_close_date else None,
        "is_video_enabled": deal_room.is_video_enabled,
        "is_chat_enabled": deal_room.is_chat_enabled,
        "require_nda": deal_room.require_nda,
        "created_by_id": deal_room.created_by_id,
        "created_at": deal_room.created_at,
        "member_count": len(deal_room.members) if deal_room.members else 0,
        "document_count": len(deal_room.documents) if deal_room.documents else 0,
    }


@router.put("/{deal_room_id}", response_model=DealRoomResponse)
def update_deal_room(
    deal_room_id: int,
    deal_room_update: DealRoomUpdate,
    db: Session = Depends(get_db)
):
    """Update a deal room"""
    deal_room = db.query(models.DealRoom).filter(models.DealRoom.id == deal_room_id).first()
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    update_data = deal_room_update.dict(exclude_unset=True)
    for field, value in update_data.items():
        if field == "target_close_date" and value:
            value = datetime.strptime(value, "%Y-%m-%d").date()
        setattr(deal_room, field, value)

    db.commit()
    db.refresh(deal_room)

    return {
        "id": deal_room.id,
        "project_id": deal_room.project_id,
        "name": deal_room.name,
        "description": deal_room.description,
        "status": deal_room.status.value if hasattr(deal_room.status, 'value') else str(deal_room.status),
        "deal_value": deal_room.deal_value,
        "deal_currency": deal_room.deal_currency,
        "target_close_date": str(deal_room.target_close_date) if deal_room.target_close_date else None,
        "is_video_enabled": deal_room.is_video_enabled,
        "is_chat_enabled": deal_room.is_chat_enabled,
        "require_nda": deal_room.require_nda,
        "created_by_id": deal_room.created_by_id,
        "created_at": deal_room.created_at,
        "member_count": len(deal_room.members) if deal_room.members else 0,
        "document_count": len(deal_room.documents) if deal_room.documents else 0,
    }


# ============================================================================
# MEMBER MANAGEMENT ENDPOINTS
# ============================================================================

@router.get("/{deal_room_id}/members", response_model=List[MemberResponse])
def list_members(deal_room_id: int, db: Session = Depends(get_db)):
    """List all members in a deal room"""
    members = db.query(models.DealRoomMember).filter(
        models.DealRoomMember.deal_room_id == deal_room_id
    ).all()

    result = []
    for member in members:
        user = db.query(models.User).filter(models.User.id == member.user_id).first()
        result.append({
            "id": member.id,
            "user_id": member.user_id,
            "role": member.role.value if hasattr(member.role, 'value') else str(member.role),
            "invitation_status": member.invitation_status,
            "nda_signed": member.nda_signed,
            "joined_at": member.joined_at,
            "user_email": user.email if user else None,
            "user_name": user.full_name if user else None,
        })

    return result


@router.post("/{deal_room_id}/members", response_model=MemberResponse, status_code=status.HTTP_201_CREATED)
def invite_member(
    deal_room_id: int,
    member_in: MemberInvite,
    db: Session = Depends(get_db)
):
    """Invite a new member to the deal room"""
    deal_room = db.query(models.DealRoom).filter(models.DealRoom.id == deal_room_id).first()
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    # Find user by email
    user = db.query(models.User).filter(models.User.email == member_in.email).first()

    if user:
        # Check if already a member
        existing = db.query(models.DealRoomMember).filter(
            models.DealRoomMember.deal_room_id == deal_room_id,
            models.DealRoomMember.user_id == user.id
        ).first()
        if existing:
            raise HTTPException(status_code=400, detail="User is already a member")

    member = models.DealRoomMember(
        deal_room_id=deal_room_id,
        user_id=user.id if user else 0,
        role=models.DealRoomMemberRole(member_in.role),
        invited_email=member_in.email,
        invitation_status="pending" if not user else "accepted",
        can_upload=member_in.can_upload,
        can_delete=member_in.can_delete,
        can_invite=member_in.can_invite,
    )
    db.add(member)
    db.commit()
    db.refresh(member)

    return {
        "id": member.id,
        "user_id": member.user_id,
        "role": member.role.value if hasattr(member.role, 'value') else str(member.role),
        "invitation_status": member.invitation_status,
        "nda_signed": member.nda_signed,
        "joined_at": member.joined_at,
        "user_email": user.email if user else member_in.email,
        "user_name": user.full_name if user else None,
    }


@router.delete("/{deal_room_id}/members/{member_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_member(deal_room_id: int, member_id: int, db: Session = Depends(get_db)):
    """Remove a member from the deal room"""
    member = db.query(models.DealRoomMember).filter(
        models.DealRoomMember.id == member_id,
        models.DealRoomMember.deal_room_id == deal_room_id
    ).first()

    if not member:
        raise HTTPException(status_code=404, detail="Member not found")

    if member.role == models.DealRoomMemberRole.OWNER:
        raise HTTPException(status_code=400, detail="Cannot remove the owner")

    db.delete(member)
    db.commit()


# ============================================================================
# DOCUMENT ENDPOINTS
# ============================================================================

@router.get("/{deal_room_id}/documents", response_model=List[DocumentResponse])
def list_documents(
    deal_room_id: int,
    document_type: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all documents in a deal room"""
    query = db.query(models.DealRoomDocument).filter(
        models.DealRoomDocument.deal_room_id == deal_room_id,
        models.DealRoomDocument.is_latest == True
    )

    if document_type:
        query = query.filter(models.DealRoomDocument.document_type == document_type)

    documents = query.order_by(models.DealRoomDocument.uploaded_at.desc()).all()

    return [{
        "id": doc.id,
        "title": doc.title,
        "description": doc.description,
        "document_type": doc.document_type.value if hasattr(doc.document_type, 'value') else str(doc.document_type),
        "file_name": doc.file_name,
        "file_url": doc.file_url,
        "version": doc.version,
        "signature_status": doc.signature_status,
        "uploaded_by_id": doc.uploaded_by_id,
        "uploaded_at": doc.uploaded_at,
    } for doc in documents]


@router.post("/{deal_room_id}/documents", response_model=DocumentResponse, status_code=status.HTTP_201_CREATED)
def upload_document(
    deal_room_id: int,
    document_in: DocumentUpload,
    db: Session = Depends(get_db)
):
    """Upload a document to the deal room"""
    deal_room = db.query(models.DealRoom).filter(models.DealRoom.id == deal_room_id).first()
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    # For now, use default user ID
    uploaded_by_id = 1

    document = models.DealRoomDocument(
        deal_room_id=deal_room_id,
        title=document_in.title,
        description=document_in.description,
        document_type=models.DocumentType(document_in.document_type),
        file_name=document_in.file_name,
        file_url=document_in.file_url,
        file_size=document_in.file_size,
        mime_type=document_in.mime_type,
        requires_signature=document_in.requires_signature,
        uploaded_by_id=uploaded_by_id,
    )
    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "id": document.id,
        "title": document.title,
        "description": document.description,
        "document_type": document.document_type.value if hasattr(document.document_type, 'value') else str(document.document_type),
        "file_name": document.file_name,
        "file_url": document.file_url,
        "version": document.version,
        "signature_status": document.signature_status,
        "uploaded_by_id": document.uploaded_by_id,
        "uploaded_at": document.uploaded_at,
    }


@router.delete("/{deal_room_id}/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_document(deal_room_id: int, document_id: int, db: Session = Depends(get_db)):
    """Delete a document from the deal room"""
    document = db.query(models.DealRoomDocument).filter(
        models.DealRoomDocument.id == document_id,
        models.DealRoomDocument.deal_room_id == deal_room_id
    ).first()

    if not document:
        raise HTTPException(status_code=404, detail="Document not found")

    db.delete(document)
    db.commit()


# ============================================================================
# MEETING ENDPOINTS
# ============================================================================

@router.get("/{deal_room_id}/meetings", response_model=List[MeetingResponse])
def list_meetings(
    deal_room_id: int,
    status: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """List all meetings in a deal room"""
    query = db.query(models.DealRoomMeeting).filter(
        models.DealRoomMeeting.deal_room_id == deal_room_id
    )

    if status:
        query = query.filter(models.DealRoomMeeting.status == status)

    meetings = query.order_by(models.DealRoomMeeting.scheduled_at.desc()).all()

    return [{
        "id": meeting.id,
        "title": meeting.title,
        "description": meeting.description,
        "scheduled_at": meeting.scheduled_at,
        "duration_minutes": meeting.duration_minutes,
        "meeting_url": meeting.meeting_url,
        "status": meeting.status.value if hasattr(meeting.status, 'value') else str(meeting.status),
        "is_recorded": meeting.is_recorded,
        "recording_url": meeting.recording_url,
        "created_at": meeting.created_at,
    } for meeting in meetings]


@router.post("/{deal_room_id}/meetings", response_model=MeetingResponse, status_code=status.HTTP_201_CREATED)
def create_meeting(
    deal_room_id: int,
    meeting_in: MeetingCreate,
    db: Session = Depends(get_db)
):
    """Schedule a new video meeting"""
    deal_room = db.query(models.DealRoom).filter(models.DealRoom.id == deal_room_id).first()
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    if not deal_room.is_video_enabled:
        raise HTTPException(status_code=400, detail="Video is not enabled for this deal room")

    # Generate a meeting URL (in production, integrate with Daily.co/Zoom)
    meeting_id = f"aip-{deal_room_id}-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    meeting_url = f"https://meet.aipplatform.com/{meeting_id}"

    meeting = models.DealRoomMeeting(
        deal_room_id=deal_room_id,
        title=meeting_in.title,
        description=meeting_in.description,
        agenda=meeting_in.agenda,
        scheduled_at=datetime.strptime(meeting_in.scheduled_at, "%Y-%m-%dT%H:%M:%S"),
        duration_minutes=meeting_in.duration_minutes,
        timezone=meeting_in.timezone,
        meeting_url=meeting_url,
        meeting_id=meeting_id,
        created_by_id=1,  # Default user for now
    )
    db.add(meeting)
    db.commit()
    db.refresh(meeting)

    return {
        "id": meeting.id,
        "title": meeting.title,
        "description": meeting.description,
        "scheduled_at": meeting.scheduled_at,
        "duration_minutes": meeting.duration_minutes,
        "meeting_url": meeting.meeting_url,
        "status": meeting.status.value if hasattr(meeting.status, 'value') else str(meeting.status),
        "is_recorded": meeting.is_recorded,
        "recording_url": meeting.recording_url,
        "created_at": meeting.created_at,
    }


# ============================================================================
# MESSAGE/CHAT ENDPOINTS
# ============================================================================

@router.get("/{deal_room_id}/messages", response_model=List[MessageResponse])
def list_messages(
    deal_room_id: int,
    skip: int = Query(0, ge=0),
    limit: int = Query(50, le=100),
    db: Session = Depends(get_db)
):
    """List messages in a deal room (chat history)"""
    messages = db.query(models.DealRoomMessage).filter(
        models.DealRoomMessage.deal_room_id == deal_room_id,
        models.DealRoomMessage.is_deleted == False
    ).order_by(models.DealRoomMessage.created_at.desc()).offset(skip).limit(limit).all()

    result = []
    for msg in messages:
        user = db.query(models.User).filter(models.User.id == msg.user_id).first()
        result.append({
            "id": msg.id,
            "user_id": msg.user_id,
            "message": msg.message,
            "message_type": msg.message_type,
            "parent_id": msg.parent_id,
            "is_edited": msg.is_edited,
            "created_at": msg.created_at,
            "user_name": user.full_name if user else None,
        })

    return result


@router.post("/{deal_room_id}/messages", response_model=MessageResponse, status_code=status.HTTP_201_CREATED)
def send_message(
    deal_room_id: int,
    message_in: MessageCreate,
    db: Session = Depends(get_db)
):
    """Send a message in the deal room chat"""
    deal_room = db.query(models.DealRoom).filter(models.DealRoom.id == deal_room_id).first()
    if not deal_room:
        raise HTTPException(status_code=404, detail="Deal room not found")

    if not deal_room.is_chat_enabled:
        raise HTTPException(status_code=400, detail="Chat is not enabled for this deal room")

    # Default user for now
    user_id = 1
    user = db.query(models.User).filter(models.User.id == user_id).first()

    message = models.DealRoomMessage(
        deal_room_id=deal_room_id,
        user_id=user_id,
        message=message_in.message,
        message_type=message_in.message_type,
        parent_id=message_in.parent_id,
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return {
        "id": message.id,
        "user_id": message.user_id,
        "message": message.message,
        "message_type": message.message_type,
        "parent_id": message.parent_id,
        "is_edited": message.is_edited,
        "created_at": message.created_at,
        "user_name": user.full_name if user else None,
    }
