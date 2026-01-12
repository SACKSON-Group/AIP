from pydantic import BaseModel
from typing import Optional
from datetime import date, datetime

class ProjectCreate(BaseModel):
    name: str
    sector: Optional[str] = None
    # ... add all optional PRD fields as per previous

class Project(ProjectCreate):
    id: int
    last_verified: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True