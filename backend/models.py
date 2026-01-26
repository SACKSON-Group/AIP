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
    username = Column(String, unique=True, index=True)
    hashed_password = Column(String)
    role = Column(String)


# SIRA Platform Models (Shipping Intelligence & Risk Analytics)
class AlertSeverity(PyEnum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


class AlertStatus(PyEnum):
    OPEN = "open"
    ACKNOWLEDGED = "acknowledged"
    ASSIGNED = "assigned"
    CLOSED = "closed"


class CaseStatus(PyEnum):
    OPEN = "open"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class EvidenceType(PyEnum):
    IOT = "IoT"
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    SENSOR_DATA = "sensor_data"
    GPS_LOG = "gps_log"


class VerificationStatus(PyEnum):
    PENDING = "pending"
    VERIFIED = "verified"
    REJECTED = "rejected"


class ShipmentEventType(PyEnum):
    PLANNED = "planned"
    ACTUAL = "actual"


class Movement(Base):
    """Shipping movement tracking for SIRA platform."""
    __tablename__ = "movements"

    id = Column(Integer, primary_key=True, index=True)
    cargo = Column(String, nullable=False)
    route = Column(String, nullable=False)
    assets = Column(String)
    stakeholders = Column(String)
    laycan_start = Column(DateTime)
    laycan_end = Column(DateTime)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    shipment_events = relationship("ShipmentEvent", back_populates="movement", cascade="all, delete-orphan")
    alerts = relationship("Alert", back_populates="movement")


class ShipmentEvent(Base):
    """Events in the unified timeline for shipment tracking."""
    __tablename__ = "shipment_events"

    id = Column(Integer, primary_key=True, index=True)
    movement_id = Column(Integer, ForeignKey("movements.id", ondelete="CASCADE"), nullable=False)
    timestamp = Column(DateTime, default=datetime.datetime.now)
    location = Column(String)
    actor = Column(String)
    evidence_ref = Column(String)
    event_type = Column(SQLEnum(ShipmentEventType), default=ShipmentEventType.ACTUAL)

    movement = relationship("Movement", back_populates="shipment_events")


class Case(Base):
    """Incident case file for security incidents."""
    __tablename__ = "cases"

    id = Column(Integer, primary_key=True, index=True)
    overview = Column(String)
    timeline = Column(String)
    actions = Column(String)
    evidence_refs = Column(String)
    costs = Column(Float, default=0.0)
    parties = Column(String)
    audit_log = Column(String)
    status = Column(SQLEnum(CaseStatus), default=CaseStatus.OPEN)
    closure_code = Column(String, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    alerts = relationship("Alert", back_populates="case")
    evidence_items = relationship("Evidence", back_populates="case", cascade="all, delete-orphan")


class Alert(Base):
    """Security alerts for SIRA platform."""
    __tablename__ = "alerts"

    id = Column(Integer, primary_key=True, index=True)
    severity = Column(SQLEnum(AlertSeverity), nullable=False)
    confidence = Column(Float)
    sla_timer = Column(Integer)
    domain = Column(String)
    site_zone = Column(String)
    movement_id = Column(Integer, ForeignKey("movements.id", ondelete="SET NULL"), nullable=True)
    status = Column(SQLEnum(AlertStatus), default=AlertStatus.OPEN)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="SET NULL"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)

    movement = relationship("Movement", back_populates="alerts")
    case = relationship("Case", back_populates="alerts")


class Playbook(Base):
    """Incident response playbooks."""
    __tablename__ = "playbooks"

    id = Column(Integer, primary_key=True, index=True)
    incident_type = Column(String, nullable=False)
    domain = Column(String)
    steps = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)
    updated_at = Column(DateTime, default=datetime.datetime.now, onupdate=datetime.datetime.now)


class Evidence(Base):
    """Evidence storage with integrity verification."""
    __tablename__ = "evidence"

    id = Column(Integer, primary_key=True, index=True)
    case_id = Column(Integer, ForeignKey("cases.id", ondelete="CASCADE"), nullable=False)
    evidence_type = Column(SQLEnum(EvidenceType), nullable=False)
    file_ref = Column(String, nullable=False)
    metadata_json = Column(String)
    verification_status = Column(SQLEnum(VerificationStatus), default=VerificationStatus.PENDING)
    file_hash = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.now)

    case = relationship("Case", back_populates="evidence_items")
