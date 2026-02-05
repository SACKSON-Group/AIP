# models.py
from sqlalchemy import Column, Integer, String, Float, Date, Enum as SQLEnum, ForeignKey, Boolean, DateTime
from sqlalchemy.orm import relationship
from backend.database import Base
from enum import Enum as PyEnum
import datetime


class Sector(PyEnum):
    ENERGY = "Energy"
    MINING = "Mining"
    WATER = "Water"
    TRANSPORT = "Transport"
    PORTS = "Ports"
    RAIL = "Rail"
    ROADS = "Roads"
    AGRICULTURE = "Agriculture"
    HEALTH = "Health"


class ProjectStage(PyEnum):
    CONCEPT = "Concept"
    FEASIBILITY = "Feasibility"
    PROCUREMENT = "Procurement"
    CONSTRUCTION = "Construction"
    OPERATION = "Operation"


class VerificationLevel(PyEnum):
    V0_SUBMITTED = "V0: Submitted"
    V1_SPONSOR_VERIFIED = "V1: Sponsor Identity Verified"
    V2_DOCUMENTS_VERIFIED = "V2: Documents Verified"
    V3_BANKABILITY_SCREENED = "V3: Bankability Screened"


class Instrument(PyEnum):
    EQUITY = "Equity"
    DEBT = "Debt"
    MEZZANINE = "Mezzanine"


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True)
    name = Column(String, index=True)
    sector = Column(SQLEnum(Sector))
    country = Column(String)
    region = Column(String, nullable=True)
    gps_location = Column(String, nullable=True)
    stage = Column(SQLEnum(ProjectStage))
    estimated_capex = Column(Float)
    funding_gap = Column(Float, nullable=True)
    timeline_fid = Column(Date, nullable=True)
    timeline_cod = Column(Date, nullable=True)
    revenue_model = Column(String)
    offtaker = Column(String, nullable=True)
    tariff_mechanism = Column(String, nullable=True)
    concession_length = Column(Integer, nullable=True)
    fx_exposure = Column(String, nullable=True)
    political_risk_mitigation = Column(String, nullable=True)
    sovereign_support = Column(String, nullable=True)
    technology = Column(String, nullable=True)
    epc_status = Column(String, nullable=True)
    land_acquisition_status = Column(String, nullable=True)
    esg_category = Column(String, nullable=True)
    permits_status = Column(String, nullable=True)
    attachments = Column(String, nullable=True)
    created_at = Column(Date, default=datetime.date.today)
    updated_at = Column(Date, default=datetime.date.today)


class Verification(Base):
    __tablename__ = "verifications"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    level = Column(SQLEnum(VerificationLevel))
    technical_readiness = Column(Integer, nullable=True)
    financial_robustness = Column(Integer, nullable=True)
    legal_clarity = Column(Integer, nullable=True)
    esg_compliance = Column(Integer, nullable=True)
    overall_score = Column(Float, nullable=True)
    risk_flags = Column(String, nullable=True)
    last_verified = Column(Date)

    project = relationship("Project")


class Investor(Base):
    __tablename__ = "investors"

    id = Column(Integer, primary_key=True)
    fund_name = Column(String)
    aum = Column(Float, nullable=True)
    ticket_size_min = Column(Float)
    ticket_size_max = Column(Float)
    instruments = Column(String)
    target_irr = Column(Float, nullable=True)
    country_focus = Column(String)
    sector_focus = Column(String)
    esg_constraints = Column(String, nullable=True)


class Introduction(Base):
    __tablename__ = "introductions"

    id = Column(Integer, primary_key=True)
    investor_id = Column(Integer, ForeignKey("investors.id"))
    project_id = Column(Integer, ForeignKey("projects.id"))
    message = Column(String, nullable=True)
    nda_executed = Column(Integer, default=0)
    sponsor_approved = Column(Integer, default=0)
    status = Column(String, default="Pending")

    investor = relationship("Investor")
    project = relationship("Project")


class DataRoom(Base):
    __tablename__ = "data_rooms"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"))
    nda_required = Column(Boolean, default=True)
    access_users = Column(String, nullable=True)
    documents = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)

    project = relationship("Project")


class AnalyticReport(Base):
    __tablename__ = "analytic_reports"

    id = Column(Integer, primary_key=True)
    title = Column(String)
    sector = Column(SQLEnum(Sector), nullable=True)
    country = Column(String, nullable=True)
    content = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)


class Event(Base):
    __tablename__ = "events"

    id = Column(Integer, primary_key=True)
    name = Column(String)
    description = Column(String)
    event_date = Column(Date)
    type = Column(String)
    projects_involved = Column(String, nullable=True)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    uuid = Column(String(36), nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)
    is_email_verified = Column(Boolean, default=False, nullable=False)
    is_phone_verified = Column(Boolean, default=False, nullable=False)
    status = Column(String(50), default='active', nullable=False)
    last_login_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now, nullable=False)
    updated_at = Column(DateTime, default=datetime.datetime.now, nullable=False)


# ============================================================================
# DEAL ROOM MODELS
# ============================================================================

class DealRoomStatus(PyEnum):
    ACTIVE = "active"
    NEGOTIATING = "negotiating"
    CLOSED_WON = "closed_won"
    CLOSED_LOST = "closed_lost"
    ARCHIVED = "archived"


class DealRoomMemberRole(PyEnum):
    OWNER = "owner"
    ADMIN = "admin"
    MEMBER = "member"
    VIEWER = "viewer"


class DocumentType(PyEnum):
    MOU = "mou"
    TERM_SHEET = "term_sheet"
    CONTRACT = "contract"
    NDA = "nda"
    FINANCIAL = "financial"
    LEGAL = "legal"
    TECHNICAL = "technical"
    OTHER = "other"


class MeetingStatus(PyEnum):
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class DealRoom(Base):
    """Main Deal Room entity for project negotiations"""
    __tablename__ = "deal_rooms"

    id = Column(Integer, primary_key=True)
    project_id = Column(Integer, ForeignKey("projects.id"), nullable=False)
    name = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    status = Column(SQLEnum(DealRoomStatus), default=DealRoomStatus.ACTIVE)

    # Deal details
    deal_value = Column(Float, nullable=True)  # Expected deal value in USD
    deal_currency = Column(String(10), default="USD")
    target_close_date = Column(Date, nullable=True)

    # Settings
    is_video_enabled = Column(Boolean, default=True)
    is_chat_enabled = Column(Boolean, default=True)
    require_nda = Column(Boolean, default=True)

    # Ownership
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)
    closed_at = Column(DateTime, nullable=True)

    # Relationships
    project = relationship("Project")
    members = relationship("DealRoomMember", back_populates="deal_room")
    documents = relationship("DealRoomDocument", back_populates="deal_room")
    meetings = relationship("DealRoomMeeting", back_populates="deal_room")
    messages = relationship("DealRoomMessage", back_populates="deal_room")


class DealRoomMember(Base):
    """Members/Collaborators in a Deal Room"""
    __tablename__ = "deal_room_members"

    id = Column(Integer, primary_key=True)
    deal_room_id = Column(Integer, ForeignKey("deal_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    role = Column(SQLEnum(DealRoomMemberRole), default=DealRoomMemberRole.MEMBER)

    # Invitation details
    invited_by_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    invited_email = Column(String(255), nullable=True)  # For pending invitations
    invitation_status = Column(String(50), default="accepted")  # pending, accepted, declined

    # Access control
    can_upload = Column(Boolean, default=True)
    can_delete = Column(Boolean, default=False)
    can_invite = Column(Boolean, default=False)
    can_edit_documents = Column(Boolean, default=True)

    # NDA status
    nda_signed = Column(Boolean, default=False)
    nda_signed_at = Column(DateTime, nullable=True)

    # Activity tracking
    last_accessed_at = Column(DateTime, nullable=True)
    access_count = Column(Integer, default=0)

    # Timestamps
    joined_at = Column(DateTime, default=datetime.datetime.now)
    access_expires_at = Column(DateTime, nullable=True)

    # Relationships
    deal_room = relationship("DealRoom", back_populates="members")


class DealRoomDocument(Base):
    """Documents in a Deal Room (MoU, Term Sheets, Contracts, etc.)"""
    __tablename__ = "deal_room_documents"

    id = Column(Integer, primary_key=True)
    deal_room_id = Column(Integer, ForeignKey("deal_rooms.id"), nullable=False)

    # Document info
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    document_type = Column(SQLEnum(DocumentType), default=DocumentType.OTHER)

    # File details
    file_name = Column(String(255), nullable=False)
    file_url = Column(String(500), nullable=False)
    file_size = Column(Integer, nullable=True)  # in bytes
    mime_type = Column(String(100), nullable=True)

    # Versioning
    version = Column(Integer, default=1)
    parent_document_id = Column(Integer, ForeignKey("deal_room_documents.id"), nullable=True)
    is_latest = Column(Boolean, default=True)

    # Signature tracking
    requires_signature = Column(Boolean, default=False)
    signature_status = Column(String(50), default="none")  # none, pending, partial, completed
    signed_by = Column(String, nullable=True)  # JSON list of user IDs who signed

    # Metadata
    uploaded_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    uploaded_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # Relationships
    deal_room = relationship("DealRoom", back_populates="documents")


class DealRoomMeeting(Base):
    """Video meetings/calls in a Deal Room"""
    __tablename__ = "deal_room_meetings"

    id = Column(Integer, primary_key=True)
    deal_room_id = Column(Integer, ForeignKey("deal_rooms.id"), nullable=False)

    # Meeting info
    title = Column(String(255), nullable=False)
    description = Column(String, nullable=True)
    agenda = Column(String, nullable=True)

    # Scheduling
    scheduled_at = Column(DateTime, nullable=False)
    duration_minutes = Column(Integer, default=60)
    timezone = Column(String(50), default="UTC")

    # Video conference details
    meeting_url = Column(String(500), nullable=True)
    meeting_id = Column(String(100), nullable=True)  # External provider ID
    meeting_password = Column(String(50), nullable=True)
    provider = Column(String(50), default="daily")  # daily, zoom, teams

    # Recording
    is_recorded = Column(Boolean, default=False)
    recording_url = Column(String(500), nullable=True)
    recording_duration = Column(Integer, nullable=True)  # in seconds

    # Status
    status = Column(SQLEnum(MeetingStatus), default=MeetingStatus.SCHEDULED)

    # Participants
    invited_members = Column(String, nullable=True)  # JSON list of member IDs
    attended_members = Column(String, nullable=True)  # JSON list of member IDs who attended

    # Ownership
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.now)
    started_at = Column(DateTime, nullable=True)
    ended_at = Column(DateTime, nullable=True)

    # Relationships
    deal_room = relationship("DealRoom", back_populates="meetings")


class DealRoomMessage(Base):
    """Chat messages in a Deal Room"""
    __tablename__ = "deal_room_messages"

    id = Column(Integer, primary_key=True)
    deal_room_id = Column(Integer, ForeignKey("deal_rooms.id"), nullable=False)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Message content
    message = Column(String, nullable=False)
    message_type = Column(String(50), default="text")  # text, file, system

    # Threading
    parent_id = Column(Integer, ForeignKey("deal_room_messages.id"), nullable=True)

    # Attachments
    attachments = Column(String, nullable=True)  # JSON list of file URLs

    # Status
    is_edited = Column(Boolean, default=False)
    is_deleted = Column(Boolean, default=False)

    # Read receipts
    read_by = Column(String, nullable=True)  # JSON list of user IDs

    # Timestamps
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    # Relationships
    deal_room = relationship("DealRoom", back_populates="messages")
