# routers/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.schemas import AnalyticReport, AnalyticReportCreate
from backend.database import get_db
from backend import models

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _serialize_report(report: AnalyticReportCreate) -> dict:
    """Convert Pydantic model to dict with serialized complex types."""
    data = report.model_dump()
    # Convert enum to value string if present
    if report.sector:
        data["sector"] = report.sector.value if hasattr(report.sector, 'value') else report.sector
    return data


def _deserialize_report(db_report: models.AnalyticReport) -> AnalyticReport:
    """Convert database model to Pydantic model."""
    return AnalyticReport(
        id=db_report.id,
        title=db_report.title,
        sector=db_report.sector,
        country=db_report.country,
        content=db_report.content,
        created_at=db_report.created_at
    )


@router.post("/", response_model=AnalyticReport)
def create(report: AnalyticReportCreate, db: Session = Depends(get_db)):
    """Create a new analytic report."""
    data = _serialize_report(report)
    db_report = models.AnalyticReport(**data)
    db.add(db_report)
    db.commit()
    db.refresh(db_report)
    return _deserialize_report(db_report)


@router.get("/{report_id}", response_model=AnalyticReport)
def read(report_id: int, db: Session = Depends(get_db)):
    """Get an analytic report by ID."""
    db_report = db.query(models.AnalyticReport).filter(models.AnalyticReport.id == report_id).first()
    if db_report is None:
        raise HTTPException(status_code=404, detail="Analytic report not found")
    return _deserialize_report(db_report)
