# routers/__init__.py
"""
API Routers for the AFCARE Platform.
"""
from backend.routers import (
    auth,
    projects,
    verifications,
    investors,
    introductions,
    data_rooms,
    analytics,
    events,
)

__all__ = [
    "auth",
    "projects",
    "verifications",
    "investors",
    "introductions",
    "data_rooms",
    "analytics",
    "events",
]
