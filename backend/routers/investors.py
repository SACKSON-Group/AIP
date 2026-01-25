# routers/investors.py
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from backend.schemas import Investor, InvestorCreate
from backend.database import get_db
from backend import models

router = APIRouter(prefix="/investors", tags=["investors"])


def _serialize_investor(investor: InvestorCreate) -> dict:
    """Convert Pydantic model with lists to dict with comma-separated strings."""
    data = investor.model_dump()
    # Convert string lists to comma-separated strings
    data["instruments"] = ",".join(investor.instruments)
    data["country_focus"] = ",".join(investor.country_focus)
    data["sector_focus"] = ",".join(investor.sector_focus)
    return data


def _deserialize_investor(db_inv: models.Investor) -> Investor:
    """Convert database model with strings to Pydantic model with lists."""
    return Investor(
        id=db_inv.id,
        fund_name=db_inv.fund_name,
        aum=db_inv.aum,
        ticket_size_min=db_inv.ticket_size_min,
        ticket_size_max=db_inv.ticket_size_max,
        instruments=db_inv.instruments.split(",") if db_inv.instruments else [],
        target_irr=db_inv.target_irr,
        country_focus=db_inv.country_focus.split(",") if db_inv.country_focus else [],
        sector_focus=db_inv.sector_focus.split(",") if db_inv.sector_focus else [],
        esg_constraints=db_inv.esg_constraints
    )


@router.post("/", response_model=Investor)
def create(investor: InvestorCreate, db: Session = Depends(get_db)):
    """Create a new investor."""
    data = _serialize_investor(investor)
    db_investor = models.Investor(**data)
    db.add(db_investor)
    db.commit()
    db.refresh(db_investor)
    return _deserialize_investor(db_investor)


@router.get("/{investor_id}", response_model=Investor)
def read(investor_id: int, db: Session = Depends(get_db)):
    """Get an investor by ID."""
    db_inv = db.query(models.Investor).filter(models.Investor.id == investor_id).first()
    if db_inv is None:
        raise HTTPException(status_code=404, detail="Investor not found")
    return _deserialize_investor(db_inv)
