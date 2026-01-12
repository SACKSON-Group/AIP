from sqlalchemy import Column, Integer, String, Numeric, Date, Float, DateTime, ForeignKey, JSON, Boolean, Text, func
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(100), unique=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    role = Column(String(20), nullable=False)

class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    sector = Column(String(50))
    country = Column(String(100))
    gps_location = Column(String(100))
    stage = Column(String(50))
    capex = Column(Numeric(15, 2))
    funding_gap = Column(Numeric(15, 2))
    timeline_fid = Column(Date)
    timeline_cod = Column(Date)
    revenue_model = Column(String(100))
    offtaker = Column(String(255))
    tariff = Column(Text)
    concession_length = Column(Integer)
    fx_exposure = Column(Text)
    political_risk = Column(Text)
    sovereign_support = Column(Text)
    technology = Column(String(100))
    epc_status = Column(String(50))
    land_acquisition_status = Column(Text)
    esg_category = Column(String(50))
    permits_status = Column(Text)
    teaser_url = Column(String(255))
    feasibility_study_url = Column(String(255))
    financial_model_url = Column(String(255))
    concession_summary_url = Column(String(255))
    verification_level = Column(Integer, default=0)
    bankability_score = Column(Float, default=0.0)
    last_verified = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=func.now())

# ... add other models like Investor, etc., if needed