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


@router.get("/", response_model=list[Investor])
def list_all(db: Session = Depends(get_db)):
    """Get all investors."""
    db_investors = db.query(models.Investor).all()
    return [_deserialize_investor(inv) for inv in db_investors]


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


@router.get("/{investor_id}/match")
def match_investor(investor_id: int, db: Session = Depends(get_db)):
    """Match an investor with compatible projects based on sector and ticket size."""
    db_inv = db.query(models.Investor).filter(models.Investor.id == investor_id).first()
    if db_inv is None:
        raise HTTPException(status_code=404, detail="Investor not found")

    investor = _deserialize_investor(db_inv)
    all_projects = db.query(models.Project).all()

    matched = []
    for project in all_projects:
        score = 0
        reasons = []

        # Sector match
        project_sector = project.sector.value if hasattr(project.sector, 'value') else str(project.sector)
        if project_sector in investor.sector_focus:
            score += 40
            reasons.append(f"Sector match: {project_sector}")

        # Country match
        if project.country in investor.country_focus:
            score += 30
            reasons.append(f"Country match: {project.country}")

        # Ticket size match
        if project.estimated_capex:
            if investor.ticket_size_min <= project.estimated_capex <= investor.ticket_size_max:
                score += 30
                reasons.append(f"CAPEX within ticket range")

        if score > 0:
            matched.append({
                "project_id": project.id,
                "project_name": project.name,
                "country": project.country,
                "sector": project_sector,
                "estimated_capex": project.estimated_capex,
                "match_score": score,
                "match_reasons": reasons
            })

    matched.sort(key=lambda x: x["match_score"], reverse=True)
    return {"investor_id": investor_id, "matches": matched}
