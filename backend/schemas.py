Pydantic schemas for API IO.
"""

from __future__ import annotations

from datetime import date, datetime
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProjectBase(BaseModel):
    name: Optional[str] = None
    sector: Optional[str] = None
    country: Optional[str] = None
    gps_location: Optional[str] = None
    stage: Optional[str] = None

    capex: Optional[float] = None
    funding_gap: Optional[float] = None

    timeline_fid: Optional[date] = None
    timeline_cod: Optional[date] = None

    revenue_model: Optional[str] = None
    offtaker: Optional[str] = None
    tariff: Optional[str] = None

    concession_length: Optional[int] = None
    fx_exposure: Optional[str] = None
    political_risk: Optional[str] = None
    sovereign_support: Optional[str] = None

    technology: Optional[str] = None
    epc_status: Optional[str] = None
    land_acquisition_status: Optional[str] = None
    esg_category: Optional[str] = None
    permits_status: Optional[str] = None

    teaser_url: Optional[str] = None
    feasibility_study_url: Optional[str] = None
    financial_model_url: Optional[str] = None
    concession_summary_url: Optional[str] = None


class ProjectCreate(ProjectBase):
    name: str = Field(..., min_length=1)


class Project(ProjectBase):
    id: int
    verification_level: int = 0
    bankability_score: float = 0.0
    last_verified: Optional[datetime] = None
    created_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)
PY
