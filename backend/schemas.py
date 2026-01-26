# schemas.py
"""
Pydantic schemas for request/response validation in the AFCARE platform.
"""
from datetime import date, datetime
from typing import List, Optional, Dict
from enum import Enum

from pydantic import BaseModel, Field, field_validator, ConfigDict

from backend.models import Sector, ProjectStage, VerificationLevel, Instrument


# -------- User Schemas --------

class UserRole(str, Enum):
    """Valid user roles in the system."""
    ADMIN = "admin"
    INVESTOR = "investor"
    SPONSOR = "sponsor"
    ANALYST = "analyst"


class UserBase(BaseModel):
    """Base user schema."""
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Unique username"
    )
    role: str = Field(
        default="investor",
        description="User role (admin, investor, sponsor, analyst)"
    )

    @field_validator("role")
    @classmethod
    def validate_role(cls, v: str) -> str:
        valid_roles = {"admin", "investor", "sponsor", "analyst"}
        if v.lower() not in valid_roles:
            raise ValueError(f"Role must be one of: {', '.join(valid_roles)}")
        return v.lower()


class UserCreate(UserBase):
    """Schema for creating a new user."""
    password: str = Field(
        ...,
        min_length=8,
        max_length=100,
        description="Password (min 8 characters)"
    )

    @field_validator("password")
    @classmethod
    def validate_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if not any(c.isupper() for c in v):
            raise ValueError("Password must contain at least one uppercase letter")
        if not any(c.islower() for c in v):
            raise ValueError("Password must contain at least one lowercase letter")
        if not any(c.isdigit() for c in v):
            raise ValueError("Password must contain at least one digit")
        return v


class User(UserBase):
    """Schema for user responses."""
    id: int

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    """JWT token response schema."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Token payload data."""
    username: Optional[str] = None
    role: Optional[str] = None


# -------- Project Schemas --------

class ProjectBase(BaseModel):
    """Base project schema."""
    name: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Project name"
    )
    sector: Sector = Field(..., description="Industry sector")
    country: str = Field(
        ...,
        min_length=2,
        max_length=100,
        description="Country where project is located"
    )
    region: Optional[str] = Field(
        None,
        max_length=100,
        description="Region/state within the country"
    )
    gps_location: Optional[str] = Field(
        None,
        max_length=100,
        description="GPS coordinates"
    )
    stage: ProjectStage = Field(..., description="Current project stage")
    estimated_capex: float = Field(
        ...,
        gt=0,
        description="Estimated capital expenditure (USD)"
    )
    funding_gap: Optional[float] = Field(
        None,
        ge=0,
        description="Remaining funding needed (USD)"
    )
    timeline_fid: Optional[date] = Field(
        None,
        description="Financial investment decision date"
    )
    timeline_cod: Optional[date] = Field(
        None,
        description="Commercial operation date"
    )
    revenue_model: str = Field(
        ...,
        min_length=3,
        max_length=500,
        description="Description of revenue generation model"
    )
    offtaker: Optional[str] = Field(
        None,
        max_length=200,
        description="Primary offtaker/customer"
    )
    tariff_mechanism: Optional[str] = Field(
        None,
        max_length=200,
        description="Tariff/pricing mechanism"
    )
    concession_length: Optional[int] = Field(
        None,
        ge=1,
        le=100,
        description="Concession length in years"
    )
    fx_exposure: Optional[str] = Field(
        None,
        max_length=200,
        description="Foreign exchange exposure details"
    )
    political_risk_mitigation: Optional[str] = Field(
        None,
        max_length=500,
        description="Political risk mitigation measures"
    )
    sovereign_support: Optional[str] = Field(
        None,
        max_length=500,
        description="Government/sovereign support details"
    )
    technology: Optional[str] = Field(
        None,
        max_length=200,
        description="Technology being used"
    )
    epc_status: Optional[str] = Field(
        None,
        max_length=200,
        description="EPC contractor status"
    )
    land_acquisition_status: Optional[str] = Field(
        None,
        max_length=200,
        description="Land acquisition status"
    )
    esg_category: Optional[str] = Field(
        None,
        max_length=50,
        description="ESG risk category"
    )
    permits_status: Optional[str] = Field(
        None,
        max_length=500,
        description="Permits and approvals status"
    )
    attachments: Optional[Dict[str, str]] = Field(
        None,
        description="Attachment URLs keyed by document name"
    )

    @field_validator("funding_gap")
    @classmethod
    def validate_funding_gap(cls, v, info):
        if v is not None and "estimated_capex" in info.data:
            if v > info.data.get("estimated_capex", float("inf")):
                raise ValueError("Funding gap cannot exceed estimated capex")
        return v


class ProjectCreate(ProjectBase):
    """Schema for creating a new project."""
    pass


class ProjectUpdate(BaseModel):
    """Schema for updating a project (all fields optional)."""
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    sector: Optional[Sector] = None
    country: Optional[str] = Field(None, min_length=2, max_length=100)
    region: Optional[str] = Field(None, max_length=100)
    stage: Optional[ProjectStage] = None
    estimated_capex: Optional[float] = Field(None, gt=0)
    funding_gap: Optional[float] = Field(None, ge=0)
    revenue_model: Optional[str] = Field(None, min_length=3, max_length=500)


class Project(ProjectBase):
    """Schema for project responses."""
    id: int
    created_at: date
    updated_at: date

    model_config = ConfigDict(from_attributes=True)


# -------- Verification Schemas --------

class BankabilityScore(BaseModel):
    """Bankability assessment scores."""
    technical_readiness: int = Field(
        ...,
        ge=0,
        le=100,
        description="Technical readiness score (0-100)"
    )
    financial_robustness: int = Field(
        ...,
        ge=0,
        le=100,
        description="Financial robustness score (0-100)"
    )
    legal_clarity: int = Field(
        ...,
        ge=0,
        le=100,
        description="Legal clarity score (0-100)"
    )
    esg_compliance: int = Field(
        ...,
        ge=0,
        le=100,
        description="ESG compliance score (0-100)"
    )
    overall_score: float = Field(
        ...,
        ge=0,
        le=100,
        description="Weighted overall score (0-100)"
    )
    risk_flags: List[str] = Field(
        default_factory=list,
        description="List of identified risk flags"
    )
    last_verified: date = Field(..., description="Date of last verification")


class VerificationBase(BaseModel):
    """Base verification schema."""
    level: VerificationLevel = Field(..., description="Verification level")
    bankability: Optional[BankabilityScore] = Field(
        None,
        description="Bankability scores (required for V3)"
    )

    @field_validator("bankability")
    @classmethod
    def validate_bankability_for_v3(cls, v, info):
        level = info.data.get("level")
        if level == VerificationLevel.V3_BANKABILITY_SCREENED and v is None:
            raise ValueError("Bankability score is required for V3 verification")
        return v


class VerificationCreate(VerificationBase):
    """Schema for creating a verification record."""
    project_id: int = Field(..., gt=0, description="Project ID")


class Verification(VerificationBase):
    """Schema for verification responses."""
    id: int
    project_id: int

    model_config = ConfigDict(from_attributes=True)


# -------- Investor Schemas --------

class InvestorBase(BaseModel):
    """Base investor schema."""
    fund_name: str = Field(
        ...,
        min_length=2,
        max_length=200,
        description="Fund/investor name"
    )
    aum: Optional[float] = Field(
        None,
        ge=0,
        description="Assets under management (USD)"
    )
    ticket_size_min: float = Field(
        ...,
        gt=0,
        description="Minimum investment ticket size (USD)"
    )
    ticket_size_max: float = Field(
        ...,
        gt=0,
        description="Maximum investment ticket size (USD)"
    )
    instruments: List[Instrument] = Field(
        ...,
        min_length=1,
        description="Investment instruments (Equity, Debt, Mezzanine)"
    )
    target_irr: Optional[float] = Field(
        None,
        ge=0,
        le=100,
        description="Target IRR percentage"
    )
    country_focus: List[str] = Field(
        ...,
        min_length=1,
        description="Target countries"
    )
    sector_focus: List[Sector] = Field(
        ...,
        min_length=1,
        description="Target sectors"
    )
    esg_constraints: Optional[str] = Field(
        None,
        max_length=500,
        description="ESG investment constraints"
    )

    @field_validator("ticket_size_max")
    @classmethod
    def validate_ticket_range(cls, v, info):
        min_val = info.data.get("ticket_size_min")
        if min_val is not None and v < min_val:
            raise ValueError("ticket_size_max must be >= ticket_size_min")
        return v


class InvestorCreate(InvestorBase):
    """Schema for creating an investor."""
    pass


class Investor(InvestorBase):
    """Schema for investor responses."""
    id: int

    model_config = ConfigDict(from_attributes=True)


# -------- Introduction Schemas --------

class IntroductionStatus(str, Enum):
    """Valid introduction statuses."""
    PENDING = "Pending"
    APPROVED = "Approved"
    REJECTED = "Rejected"
    IN_PROGRESS = "In Progress"
    COMPLETED = "Completed"


class IntroductionBase(BaseModel):
    """Base introduction schema."""
    message: Optional[str] = Field(
        None,
        max_length=1000,
        description="Introduction message"
    )
    nda_executed: bool = Field(
        default=False,
        description="Whether NDA has been executed"
    )
    sponsor_approved: bool = Field(
        default=False,
        description="Whether sponsor has approved"
    )
    status: str = Field(
        default="Pending",
        description="Introduction status"
    )


class IntroductionCreate(IntroductionBase):
    """Schema for creating an introduction."""
    investor_id: int = Field(..., gt=0, description="Investor ID")
    project_id: int = Field(..., gt=0, description="Project ID")


class Introduction(IntroductionBase):
    """Schema for introduction responses."""
    id: int
    investor_id: int
    project_id: int

    model_config = ConfigDict(from_attributes=True)


# -------- Data Room Schemas --------

class DataRoomBase(BaseModel):
    """Base data room schema."""
    project_id: int = Field(..., gt=0, description="Associated project ID")
    nda_required: bool = Field(
        default=True,
        description="Whether NDA is required for access"
    )
    access_users: Optional[List[int]] = Field(
        None,
        description="User IDs with access"
    )
    documents: Optional[Dict[str, str]] = Field(
        None,
        description="Document URLs keyed by document name"
    )


class DataRoomCreate(DataRoomBase):
    """Schema for creating a data room."""
    pass


class DataRoom(DataRoomBase):
    """Schema for data room responses."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------- Analytics Schemas --------

class AnalyticReportBase(BaseModel):
    """Base analytic report schema."""
    title: str = Field(
        ...,
        min_length=5,
        max_length=200,
        description="Report title"
    )
    sector: Optional[Sector] = Field(None, description="Sector focus")
    country: Optional[str] = Field(
        None,
        max_length=100,
        description="Country focus"
    )
    content: str = Field(
        ...,
        min_length=10,
        description="Report content"
    )


class AnalyticReportCreate(AnalyticReportBase):
    """Schema for creating an analytic report."""
    pass


class AnalyticReport(AnalyticReportBase):
    """Schema for analytic report responses."""
    id: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# -------- Event Schemas --------

class EventType(str, Enum):
    """Valid event types."""
    MILESTONE = "milestone"
    MEETING = "meeting"
    DEADLINE = "deadline"
    ANNOUNCEMENT = "announcement"
    OTHER = "other"


class EventBase(BaseModel):
    """Base event schema."""
    name: str = Field(
        ...,
        min_length=3,
        max_length=200,
        description="Event name"
    )
    description: str = Field(
        ...,
        min_length=10,
        max_length=1000,
        description="Event description"
    )
    event_date: date = Field(..., description="Event date")
    type: str = Field(..., description="Event type")
    projects_involved: Optional[List[int]] = Field(
        None,
        description="Related project IDs"
    )


class EventCreate(EventBase):
    """Schema for creating an event."""
    pass


class Event(EventBase):
    """Schema for event responses."""
    id: int

    model_config = ConfigDict(from_attributes=True)
