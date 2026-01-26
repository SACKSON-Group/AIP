# main.py
"""
AFCARE Digital Health Platform - Main Application Entry Point
"""
import sys
import os
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Ensure backend package is importable
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from backend.config import settings
from backend.database import engine, Base
from backend.routers import (
    auth as auth_router,
    projects as projects_router,
    verifications as verifications_router,
    investors as investors_router,
    introductions as introductions_router,
    data_rooms as data_rooms_router,
    analytics as analytics_router,
    events as events_router,
)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan context manager.
    Handles startup and shutdown events.
    """
    # Startup: Create database tables
    Base.metadata.create_all(bind=engine)
    yield
    # Shutdown: Add cleanup logic here if needed


# Create FastAPI application
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="AFCARE Digital Health Platform API - Connecting Healthcare in Africa",
    lifespan=lifespan,
)

# Configure CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=settings.cors_allow_credentials,
    allow_methods=settings.cors_allow_methods,
    allow_headers=settings.cors_allow_headers,
)


# Health check endpoint
@app.get("/health", tags=["Health"])
def health_check():
    """Check API health status."""
    return {
        "status": "healthy",
        "version": settings.app_version,
        "app": settings.app_name,
    }


@app.get("/", tags=["Root"])
def root():
    """Root endpoint with API information."""
    return {
        "message": "AFCARE Backend API - Connecting Healthcare in Africa",
        "version": settings.app_version,
        "docs": "/docs",
        "health": "/health",
    }


# Include routers
app.include_router(auth_router.router)
app.include_router(projects_router.router)
app.include_router(verifications_router.router)
app.include_router(investors_router.router)
app.include_router(introductions_router.router)
app.include_router(data_rooms_router.router)
app.include_router(analytics_router.router)
app.include_router(events_router.router)

# Mount static files if directory exists
_static_dir = Path(__file__).parent / "static"
if _static_dir.exists():
    app.mount(
        "/static",
        StaticFiles(directory=str(_static_dir), html=True),
        name="frontend"
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.debug,
    )
