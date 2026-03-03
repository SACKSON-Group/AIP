"""AIP Platform - FastAPI Application Entry Point."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.core.config import settings
from app.core.database import Base, engine
from app.routers import (
    auth_router,
    users_router,
    organizations_router,
    projects_router,
    documents_router,
    verifications_router,
    investors_router,
    dealrooms_router,
    events_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler for startup/shutdown events."""
    Base.metadata.create_all(bind=engine)
    yield


app = FastAPI(
    title=settings.APP_NAME,
    description="African Infrastructure Projects Platform - Connecting projects with investors",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth_router)
app.include_router(users_router)
app.include_router(organizations_router)
app.include_router(projects_router)
app.include_router(documents_router)
app.include_router(verifications_router)
app.include_router(investors_router)
app.include_router(dealrooms_router)
app.include_router(events_router)


@app.get("/")
def root():
    """Root endpoint - health check."""
    return {
        "name": settings.APP_NAME,
        "version": "1.0.0",
        "status": "healthy",
        "environment": settings.ENVIRONMENT,
    }


@app.get("/health")
def health_check():
    """Health check endpoint."""
    return {"status": "healthy"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("app.main:app", host="0.0.0.0", port=8000)
