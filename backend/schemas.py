# schemas.py
from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from backend.models import (
    Sector, ProjectStage, VerificationLevel, Instrument,
    AlertSeverity, AlertStatus, CaseStatus, EvidenceType,
    VerificationStatus, ShipmentEventType
)


class ProjectBase(BaseModel):
    name: str = Field(..., description="Project name")
    sector: Sector
    country: str
    region: Optional[str] = None
    gps_location: Optional[str] = None
    stage: ProjectStage
    estimated_capex: float
    funding_gap: Optional[float] = None
    timeline_fid: Optional[date] = None
    timeline_cod: Optional[date] = None
    revenue_model: str
    offtaker: Optional[str] = None
    tariff_mechanism: Optional[str] = None
    concession_length: Optional[int] = None
    fx_exposure: Optional[str] = None
    political_risk_mitigation: Optional[str] = None
    sovereign_support: Optional[str] = None
    technology: Optional[str] = None
    epc_status: Optional[str] = None
    land_acquisition_status: Optional[str] = None
    esg_category: Optional[str] = None
    permits_status: Optional[str] = None
    attachments: Optional[Dict[str, str]] = None


class ProjectCreate(ProjectBase):
    pass


class Project(ProjectBase):
    id: int
    created_at: date
    updated_at: date

    class Config:
        from_attributes = True


class BankabilityScore(BaseModel):
    technical_readiness: int = Field(..., ge=0, le=100)
    financial_robustness: int = Field(..., ge=0, le=100)
    legal_clarity: int = Field(..., ge=0, le=100)
    esg_compliance: int = Field(..., ge=0, le=100)
    overall_score: float = Field(..., ge=0, le=100)
    risk_flags: List[str] = []
    last_verified: date


class VerificationBase(BaseModel):
    level: VerificationLevel
    bankability: Optional[BankabilityScore] = None


class VerificationCreate(VerificationBase):
    project_id: int


class Verification(VerificationBase):
    id: int
    project_id: int

    class Config:
        from_attributes = True


class InvestorBase(BaseModel):
    fund_name: str
    aum: Optional[float] = None
    ticket_size_min: float
    ticket_size_max: float
    instruments: List[Instrument]
    target_irr: Optional[float] = None
    country_focus: List[str]
    sector_focus: List[Sector]
    esg_constraints: Optional[str] = None


class InvestorCreate(InvestorBase):
    pass


class Investor(InvestorBase):
    id: int

    class Config:
        from_attributes = True


class IntroductionBase(BaseModel):
    message: Optional[str] = None
    nda_executed: bool = False
    sponsor_approved: bool = False
    status: str = "Pending"


class IntroductionCreate(IntroductionBase):
    investor_id: int
    project_id: int


class Introduction(IntroductionBase):
    id: int
    investor_id: int
    project_id: int

    class Config:
        from_attributes = True


class DataRoomBase(BaseModel):
    project_id: int
    nda_required: bool = True
    access_users: Optional[List[int]] = None
    documents: Optional[Dict[str, str]] = None


class DataRoomCreate(DataRoomBase):
    pass


class DataRoom(DataRoomBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class AnalyticReportBase(BaseModel):
    title: str
    sector: Optional[Sector] = None
    country: Optional[str] = None
    content: str


class AnalyticReportCreate(AnalyticReportBase):
    pass


class AnalyticReport(AnalyticReportBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True


class EventBase(BaseModel):
    name: str
    description: str
    event_date: date
    type: str
    projects_involved: Optional[List[int]] = None


class EventCreate(EventBase):
    pass


class Event(EventBase):
    id: int

    class Config:
        from_attributes = True


class UserBase(BaseModel):
    username: str
    role: str


class UserCreate(UserBase):
    password: str


class User(UserBase):
    id: int

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str


# SIRA Platform Schemas (Shipping Intelligence & Risk Analytics)

# Movement Schemas
class MovementBase(BaseModel):
    cargo: str = Field(..., min_length=1, max_length=500, description="Cargo description")
    route: str = Field(..., min_length=1, max_length=500, description="Route description")
    assets: Optional[str] = Field(None, max_length=1000, description="Assets involved")
    stakeholders: Optional[str] = Field(None, max_length=1000, description="Stakeholders list")
    laycan_start: Optional[datetime] = Field(None, description="Laycan window start")
    laycan_end: Optional[datetime] = Field(None, description="Laycan window end")


class MovementCreate(MovementBase):
    pass


class MovementUpdate(BaseModel):
    cargo: Optional[str] = Field(None, min_length=1, max_length=500)
    route: Optional[str] = Field(None, min_length=1, max_length=500)
    assets: Optional[str] = Field(None, max_length=1000)
    stakeholders: Optional[str] = Field(None, max_length=1000)
    laycan_start: Optional[datetime] = None
    laycan_end: Optional[datetime] = None


class MovementResponse(MovementBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ShipmentEvent Schemas
class ShipmentEventBase(BaseModel):
    movement_id: int = Field(..., gt=0, description="Movement ID")
    timestamp: Optional[datetime] = Field(None, description="Event timestamp")
    location: Optional[str] = Field(None, max_length=500, description="Event location")
    actor: Optional[str] = Field(None, max_length=200, description="Actor responsible")
    evidence_ref: Optional[str] = Field(None, max_length=500, description="Evidence reference")
    event_type: ShipmentEventType = Field(ShipmentEventType.ACTUAL, description="Event type")


class ShipmentEventCreate(ShipmentEventBase):
    pass


class ShipmentEventResponse(ShipmentEventBase):
    id: int

    class Config:
        from_attributes = True


# Alert Schemas
class AlertBase(BaseModel):
    severity: AlertSeverity = Field(..., description="Alert severity level")
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0, description="Confidence score 0-1")
    sla_timer: Optional[int] = Field(None, ge=0, description="SLA timer in minutes")
    domain: Optional[str] = Field(None, max_length=200, description="Security domain")
    site_zone: Optional[str] = Field(None, max_length=200, description="Site or zone")
    movement_id: Optional[int] = Field(None, gt=0, description="Related movement ID")


class AlertCreate(AlertBase):
    pass


class AlertUpdate(BaseModel):
    severity: Optional[AlertSeverity] = None
    confidence: Optional[float] = Field(None, ge=0.0, le=1.0)
    sla_timer: Optional[int] = Field(None, ge=0)
    domain: Optional[str] = Field(None, max_length=200)
    site_zone: Optional[str] = Field(None, max_length=200)
    status: Optional[AlertStatus] = None
    case_id: Optional[int] = Field(None, gt=0)


class AlertResponse(AlertBase):
    id: int
    status: AlertStatus
    case_id: Optional[int]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Case Schemas
class CaseBase(BaseModel):
    overview: str = Field(..., min_length=1, max_length=5000, description="Case overview")
    timeline: Optional[str] = Field(None, description="Timeline JSON")
    actions: Optional[str] = Field(None, description="Actions JSON")
    evidence_refs: Optional[str] = Field(None, description="Evidence references JSON")
    costs: Optional[float] = Field(0.0, ge=0.0, description="Incident costs")
    parties: Optional[str] = Field(None, max_length=1000, description="Parties involved")
    audit_log: Optional[str] = Field(None, description="Audit log JSON")


class CaseCreate(CaseBase):
    pass


class CaseUpdate(BaseModel):
    overview: Optional[str] = Field(None, min_length=1, max_length=5000)
    timeline: Optional[str] = None
    actions: Optional[str] = None
    evidence_refs: Optional[str] = None
    costs: Optional[float] = Field(None, ge=0.0)
    parties: Optional[str] = Field(None, max_length=1000)
    audit_log: Optional[str] = None
    status: Optional[CaseStatus] = None


class CaseClose(BaseModel):
    closure_code: str = Field(..., min_length=1, max_length=100, description="Closure code")


class CaseResponse(CaseBase):
    id: int
    status: CaseStatus
    closure_code: Optional[str]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Playbook Schemas
class PlaybookBase(BaseModel):
    incident_type: str = Field(..., min_length=1, max_length=200, description="Incident type")
    domain: Optional[str] = Field(None, max_length=200, description="Domain")
    steps: Optional[str] = Field(None, description="Steps JSON array")


class PlaybookCreate(PlaybookBase):
    pass


class PlaybookUpdate(BaseModel):
    incident_type: Optional[str] = Field(None, min_length=1, max_length=200)
    domain: Optional[str] = Field(None, max_length=200)
    steps: Optional[str] = None


class PlaybookResponse(PlaybookBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# Evidence Schemas
class EvidenceBase(BaseModel):
    case_id: int = Field(..., gt=0, description="Case ID")
    evidence_type: EvidenceType = Field(..., description="Type of evidence")
    file_ref: str = Field(..., min_length=1, max_length=1000, description="File reference/path")
    metadata_json: Optional[str] = Field(None, description="Metadata JSON")


class EvidenceCreate(EvidenceBase):
    pass


class EvidenceResponse(EvidenceBase):
    id: int
    verification_status: VerificationStatus
    file_hash: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# Export Pack Response
class ExportPackResponse(BaseModel):
    message: str
    case_id: int
    case_overview: str
    case_status: str
    evidence_count: int
