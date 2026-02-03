# schemas.py
from datetime import date, datetime
from pydantic import BaseModel, Field
from typing import List, Optional, Dict


class ProjectBase(BaseModel):
    name: str = Field(..., description="Project name")
    sector: str  # Accept string values like "Energy", "Mining", etc.
    country: str
    region: Optional[str] = None
    gps_location: Optional[str] = None
    stage: str  # Accept string values like "Concept", "Feasibility", etc.
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
    level: str  # Accept string values like "V0: Submitted"
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
    instruments: List[str]  # Accept string values like ["Equity", "Debt"]
    target_irr: Optional[float] = None
    country_focus: List[str]
    sector_focus: List[str]  # Accept string values like ["Energy", "Mining"]
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
    sector: Optional[str] = None  # Accept string values like "Energy"
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


# Email-based user schemas
class UserRegister(BaseModel):
    email: str
    password: str
    full_name: str
    phone: Optional[str] = None


class UserResponse(BaseModel):
    id: int
    email: str
    full_name: Optional[str] = None

    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str
