# routers/analytics.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.schemas import AnalyticReport, AnalyticReportCreate
from backend.database import get_db
from backend import models

router = APIRouter(prefix="/analytics", tags=["analytics"])


def _get_sector_enum(sector_str: str) -> models.Sector:
    """Convert sector string to enum."""
    for s in models.Sector:
        if s.value == sector_str:
            return s
    try:
        return models.Sector[sector_str.upper()]
    except KeyError:
        raise HTTPException(status_code=422, detail=f"Invalid sector: {sector_str}")


def _serialize_report(report: AnalyticReportCreate) -> dict:
    """Convert Pydantic model to dict with proper enum types."""
    data = report.model_dump()
    if report.sector:
        data["sector"] = _get_sector_enum(report.sector)
    return data


def _deserialize_report(db_report: models.AnalyticReport) -> AnalyticReport:
    """Convert database model to Pydantic model."""
    sector_val = None
    if db_report.sector:
        sector_val = db_report.sector.value if hasattr(db_report.sector, 'value') else str(db_report.sector)
    return AnalyticReport(
        id=db_report.id,
        title=db_report.title,
        sector=sector_val,
        country=db_report.country,
        content=db_report.content,
        created_at=db_report.created_at
    )


@router.get("/", response_model=list[AnalyticReport])
def list_reports(db: Session = Depends(get_db)):
    """List all analytic reports."""
    db_reports = db.query(models.AnalyticReport).all()
    return [_deserialize_report(r) for r in db_reports]


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
