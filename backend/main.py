# main.py
from fastapi import FastAPI
from backend.models import Base
from backend.routers.projects import router as projects_router
from backend.routers.verifications import router as verifications_router
from backend.routers.investors import router as investors_router
from backend.routers.introductions import router as introductions_router
from backend.routers.data_rooms import router as data_rooms_router
from backend.routers.analytics import router as analytics_router
from backend.routers.events import router as events_router
from backend.routers.auth import router as auth_router
# SIRA Platform routers
from backend.routers.movements import router as movements_router
from backend.routers.alerts import router as alerts_router
from backend.routers.cases import router as cases_router
from backend.routers.playbooks import router as playbooks_router
from backend.routers.evidence import router as evidence_router
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from backend.database import engine
from pathlib import Path
from fastapi.staticfiles import StaticFiles

# Create FastAPI app first
app = FastAPI(
    title="AIP & SIRA Platform API",
    description="AIP Infrastructure Platform + SIRA (Shipping Intelligence & Risk Analytics) MVP",
    version="1.0"
)

@app.get("/health")
def health_check():
    return {"status": "healthy"}

@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)

# Mount static files after app is created
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(_static_dir), html=True), name="frontend")


app.include_router(projects_router)
app.include_router(verifications_router)
app.include_router(investors_router)
app.include_router(introductions_router)
app.include_router(data_rooms_router)
app.include_router(analytics_router)
app.include_router(events_router)
app.include_router(auth_router)

# SIRA Platform routers
app.include_router(movements_router)
app.include_router(alerts_router)
app.include_router(cases_router)
app.include_router(playbooks_router)
app.include_router(evidence_router)

# Rest of main.py (auth dependencies, etc.)
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
