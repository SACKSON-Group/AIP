"""
backend.crud

Small CRUD helpers used by routers.

Design:
- Avoid importing Pydantic schemas at import-time (prevents circular imports).
- Load SQLAlchemy models lazily from backend.models by class name.
"""
from __future__ import annotations

from typing import Any, Optional
from sqlalchemy.orm import Session


def _get_model(model_name: str):
    try:
        import backend.models as models
    except Exception as e:
        raise RuntimeError("Cannot import backend.models") from e

    model = getattr(models, model_name, None)
    if model is None:
        raise RuntimeError(f"Model {model_name!r} not found in backend.models")
    return model


def _to_dict(payload: Any) -> dict:
    if payload is None:
        return {}
    if hasattr(payload, "model_dump"):  # Pydantic v2
        return payload.model_dump(exclude_unset=True)
    if hasattr(payload, "dict"):  # Pydantic v1
        return payload.dict(exclude_unset=True)
    return dict(payload)


def _create(db: Session, model_name: str, payload: Any):
    model = _get_model(model_name)
    obj = model(**_to_dict(payload))
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _get(db: Session, model_name: str, obj_id: int) -> Optional[Any]:
    model = _get_model(model_name)
    return db.query(model).filter(model.id == obj_id).first()


# -------- Investors --------
def create_investor(db: Session, investor_in: Any):
    return _create(db, "Investor", investor_in)


def get_investor(db: Session, investor_id: int):
    return _get(db, "Investor", investor_id)


# -------- Introductions --------
def create_introduction(db: Session, introduction_in: Any):
    return _create(db, "Introduction", introduction_in)


def get_introduction(db: Session, introduction_id: int):
    return _get(db, "Introduction", introduction_id)


# -------- Projects --------
def create_project(db: Session, project_in: Any):
    return _create(db, "Project", project_in)


def get_project(db: Session, project_id: int):
    return _get(db, "Project", project_id)


# -------- Data Rooms --------
def create_data_room(db: Session, data_room_in: Any):
    return _create(db, "DataRoom", data_room_in)


def get_data_room(db: Session, data_room_id: int):
    return _get(db, "DataRoom", data_room_id)


# -------- Analytics --------
def create_analytics(db: Session, analytics_in: Any):
    return _create(db, "Analytics", analytics_in)


def get_analytics(db: Session, analytics_id: int):
    return _get(db, "Analytics", analytics_id)


# -------- Events --------
def create_event(db: Session, event_in: Any):
    return _create(db, "Event", event_in)


def get_event(db: Session, event_id: int):
    return _get(db, "Event", event_id)


# -------- Auth / Users --------
def create_user(db: Session, user_in: Any):
    return _create(db, "User", user_in)


def get_user(db: Session, user_id: int):
    return _get(db, "User", user_id)


# -------- Analytic Reports (aliases expected by routers) --------
def _create_any(db: Session, model_candidates: list[str], payload: Any):
    last_err: Exception | None = None
    for name in model_candidates:
        try:
            return _create(db, name, payload)
        except Exception as e:
            last_err = e
    raise RuntimeError(f"No matching model found for {model_candidates}") from last_err


def _get_any(db: Session, model_candidates: list[str], obj_id: int):
    last_err: Exception | None = None
    for name in model_candidates:
        try:
            return _get(db, name, obj_id)
        except Exception as e:
            last_err = e
    raise RuntimeError(f"No matching model found for {model_candidates}") from last_err


def create_analytic_report(db: Session, report_in: Any):
    # Tries common model names; adjust once you confirm your actual SQLAlchemy class name.
    return _create_any(db, ["AnalyticReport", "AnalyticsReport", "Analytics"], report_in)


def get_analytic_report(db: Session, report_id: int):
    return _get_any(db, ["AnalyticReport", "AnalyticsReport", "Analytics"], report_id)


# -------- Auth helpers --------
def get_user_by_username(db: Session, username: str):
    """Get user by email (username field contains email)."""
    user_model = _get_model("User")
    # Database uses 'email' column, not 'username'
    if hasattr(user_model, 'email'):
        return db.query(user_model).filter(user_model.email == username).first()
    return db.query(user_model).filter(user_model.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None

    # Truncate password to 72 bytes for bcrypt limit
    truncated_password = password[:72] if password else ""

    # Get the password hash - database may use 'password_hash' or 'hashed_password'
    stored_hash = getattr(user, 'password_hash', None) or getattr(user, 'hashed_password', '')

    # Prefer Passlib hash verification if available
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        ok = pwd_context.verify(truncated_password, stored_hash)
    except Exception:
        # Fallback for early dev (NOT for production)
        ok = truncated_password == stored_hash

    return user if ok else None
