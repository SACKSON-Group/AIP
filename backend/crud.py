"""
backend.crud

CRUD (Create, Read, Update, Delete) helpers for the AFCARE platform.

Design:
- Avoid importing Pydantic schemas at import-time (prevents circular imports).
- Load SQLAlchemy models lazily from backend.models by class name.
"""
from __future__ import annotations

import json
from typing import Any, Optional, List
from sqlalchemy.orm import Session


def _get_model(model_name: str):
    """Lazily load a SQLAlchemy model by name."""
    try:
        import backend.models as models
    except Exception as e:
        raise RuntimeError("Cannot import backend.models") from e

    model = getattr(models, model_name, None)
    if model is None:
        raise RuntimeError(f"Model {model_name!r} not found in backend.models")
    return model


def _to_dict(payload: Any) -> dict:
    """Convert a Pydantic model or dict-like object to a dictionary."""
    if payload is None:
        return {}
    if hasattr(payload, "model_dump"):  # Pydantic v2
        return payload.model_dump(exclude_unset=True)
    if hasattr(payload, "dict"):  # Pydantic v1
        return payload.dict(exclude_unset=True)
    return dict(payload)


def _serialize_for_db(data: dict) -> dict:
    """
    Serialize complex types (lists, dicts) to strings for database storage.
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, list):
            # Convert list of enums to their values if needed
            str_values = []
            for item in value:
                if hasattr(item, 'value'):
                    str_values.append(item.value)
                else:
                    str_values.append(str(item))
            result[key] = ",".join(str_values)
        elif isinstance(value, dict):
            result[key] = json.dumps(value)
        elif hasattr(value, 'value'):  # Enum
            result[key] = value
        else:
            result[key] = value
    return result


def _create(db: Session, model_name: str, payload: Any):
    """Generic create operation."""
    model = _get_model(model_name)
    data = _serialize_for_db(_to_dict(payload))
    obj = model(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def _get(db: Session, model_name: str, obj_id: int) -> Optional[Any]:
    """Generic get by ID operation."""
    model = _get_model(model_name)
    return db.query(model).filter(model.id == obj_id).first()


def _get_all(
    db: Session,
    model_name: str,
    skip: int = 0,
    limit: int = 100
) -> List[Any]:
    """Generic list operation with pagination."""
    model = _get_model(model_name)
    return db.query(model).offset(skip).limit(limit).all()


def _update(
    db: Session,
    model_name: str,
    obj_id: int,
    payload: Any
) -> Optional[Any]:
    """Generic update operation."""
    model = _get_model(model_name)
    obj = db.query(model).filter(model.id == obj_id).first()
    if obj is None:
        return None
    data = _serialize_for_db(_to_dict(payload))
    for key, value in data.items():
        if hasattr(obj, key):
            setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def _delete(db: Session, model_name: str, obj_id: int) -> bool:
    """Generic delete operation."""
    model = _get_model(model_name)
    obj = db.query(model).filter(model.id == obj_id).first()
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True


# -------- Projects --------
def create_project(db: Session, project_in: Any):
    return _create(db, "Project", project_in)


def get_project(db: Session, project_id: int):
    return _get(db, "Project", project_id)


def get_projects(db: Session, skip: int = 0, limit: int = 100):
    return _get_all(db, "Project", skip, limit)


def update_project(db: Session, project_id: int, project_in: Any):
    return _update(db, "Project", project_id, project_in)


def delete_project(db: Session, project_id: int):
    return _delete(db, "Project", project_id)


# -------- Investors --------
def create_investor(db: Session, investor_in: Any):
    return _create(db, "Investor", investor_in)


def get_investor(db: Session, investor_id: int):
    return _get(db, "Investor", investor_id)


def get_investors(db: Session, skip: int = 0, limit: int = 100):
    return _get_all(db, "Investor", skip, limit)


def update_investor(db: Session, investor_id: int, investor_in: Any):
    return _update(db, "Investor", investor_id, investor_in)


def delete_investor(db: Session, investor_id: int):
    return _delete(db, "Investor", investor_id)


# -------- Introductions --------
def create_introduction(db: Session, introduction_in: Any):
    return _create(db, "Introduction", introduction_in)


def get_introduction(db: Session, introduction_id: int):
    return _get(db, "Introduction", introduction_id)


def get_introductions(db: Session, skip: int = 0, limit: int = 100):
    return _get_all(db, "Introduction", skip, limit)


def update_introduction(db: Session, introduction_id: int, introduction_in: Any):
    return _update(db, "Introduction", introduction_id, introduction_in)


def delete_introduction(db: Session, introduction_id: int):
    return _delete(db, "Introduction", introduction_id)


# -------- Verifications --------
def create_verification(db: Session, verification_in: Any):
    return _create(db, "Verification", verification_in)


def get_verification(db: Session, verification_id: int):
    return _get(db, "Verification", verification_id)


def get_verifications(db: Session, skip: int = 0, limit: int = 100):
    return _get_all(db, "Verification", skip, limit)


# -------- Data Rooms --------
def create_data_room(db: Session, data_room_in: Any):
    return _create(db, "DataRoom", data_room_in)


def get_data_room(db: Session, data_room_id: int):
    return _get(db, "DataRoom", data_room_id)


def get_data_rooms(db: Session, skip: int = 0, limit: int = 100):
    return _get_all(db, "DataRoom", skip, limit)


# -------- Analytic Reports --------
def create_analytic_report(db: Session, report_in: Any):
    return _create(db, "AnalyticReport", report_in)


def get_analytic_report(db: Session, report_id: int):
    return _get(db, "AnalyticReport", report_id)


def get_analytic_reports(db: Session, skip: int = 0, limit: int = 100):
    return _get_all(db, "AnalyticReport", skip, limit)


# -------- Events --------
def create_event(db: Session, event_in: Any):
    return _create(db, "Event", event_in)


def get_event(db: Session, event_id: int):
    return _get(db, "Event", event_id)


def get_events(db: Session, skip: int = 0, limit: int = 100):
    return _get_all(db, "Event", skip, limit)


# -------- Users --------
def create_user(db: Session, user_in: Any):
    """Create a new user with hashed password."""
    from backend.security import get_password_hash

    data = _to_dict(user_in)
    # Hash password if present
    if "password" in data:
        data["hashed_password"] = get_password_hash(data.pop("password"))

    model = _get_model("User")
    obj = model(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_user(db: Session, user_id: int):
    return _get(db, "User", user_id)


def get_user_by_username(db: Session, username: str):
    """Get a user by username."""
    user_model = _get_model("User")
    return db.query(user_model).filter(user_model.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    """
    Authenticate a user by username and password.
    Returns the user if authentication succeeds, None otherwise.
    """
    from backend.security import verify_password

    user = get_user_by_username(db, username)
    if not user:
        return None
    if not verify_password(password, user.hashed_password):
        return None
    return user
