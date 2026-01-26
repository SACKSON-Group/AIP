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
    user_model = _get_model("User")
    return db.query(user_model).filter(user_model.username == username).first()


def authenticate_user(db: Session, username: str, password: str):
    user = get_user_by_username(db, username)
    if not user:
        return None

    # Prefer Passlib hash verification if available
    try:
        from passlib.context import CryptContext
        pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
        ok = pwd_context.verify(password, user.hashed_password)
    except Exception:
        # Fallback for early dev (NOT for production)
        ok = password == getattr(user, "hashed_password", "")

    return user if ok else None


# -------- SIRA: Movements --------
def create_movement(db: Session, movement_in: Any):
    return _create(db, "Movement", movement_in)


def get_movement(db: Session, movement_id: int):
    return _get(db, "Movement", movement_id)


def list_movements(db: Session, skip: int = 0, limit: int = 100):
    model = _get_model("Movement")
    return db.query(model).offset(skip).limit(limit).all()


def update_movement(db: Session, movement_id: int, movement_in: Any):
    model = _get_model("Movement")
    obj = db.query(model).filter(model.id == movement_id).first()
    if obj is None:
        return None
    update_data = _to_dict(movement_in)
    for key, value in update_data.items():
        if value is not None:
            setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_movement(db: Session, movement_id: int) -> bool:
    model = _get_model("Movement")
    obj = db.query(model).filter(model.id == movement_id).first()
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True


# -------- SIRA: ShipmentEvents --------
def create_shipment_event(db: Session, event_in: Any):
    return _create(db, "ShipmentEvent", event_in)


def get_shipment_event(db: Session, event_id: int):
    return _get(db, "ShipmentEvent", event_id)


def list_shipment_events(db: Session, movement_id: Optional[int] = None, skip: int = 0, limit: int = 100):
    model = _get_model("ShipmentEvent")
    query = db.query(model)
    if movement_id:
        query = query.filter(model.movement_id == movement_id)
    return query.offset(skip).limit(limit).all()


# -------- SIRA: Alerts --------
def create_alert(db: Session, alert_in: Any):
    return _create(db, "Alert", alert_in)


def get_alert(db: Session, alert_id: int):
    return _get(db, "Alert", alert_id)


def list_alerts(
    db: Session,
    domain: Optional[str] = None,
    status: Optional[str] = None,
    severity: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    model = _get_model("Alert")
    query = db.query(model)
    if domain:
        query = query.filter(model.domain == domain)
    if status:
        query = query.filter(model.status == status)
    if severity:
        query = query.filter(model.severity == severity)
    return query.offset(skip).limit(limit).all()


def update_alert(db: Session, alert_id: int, alert_in: Any):
    model = _get_model("Alert")
    obj = db.query(model).filter(model.id == alert_id).first()
    if obj is None:
        return None
    update_data = _to_dict(alert_in)
    for key, value in update_data.items():
        if value is not None:
            setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


# -------- SIRA: Cases --------
def create_case(db: Session, case_in: Any):
    return _create(db, "Case", case_in)


def get_case(db: Session, case_id: int):
    return _get(db, "Case", case_id)


def list_cases(db: Session, status: Optional[str] = None, skip: int = 0, limit: int = 100):
    model = _get_model("Case")
    query = db.query(model)
    if status:
        query = query.filter(model.status == status)
    return query.offset(skip).limit(limit).all()


def update_case(db: Session, case_id: int, case_in: Any):
    model = _get_model("Case")
    obj = db.query(model).filter(model.id == case_id).first()
    if obj is None:
        return None
    update_data = _to_dict(case_in)
    for key, value in update_data.items():
        if value is not None:
            setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def close_case(db: Session, case_id: int, closure_code: str):
    model = _get_model("Case")
    case_status = _get_model("CaseStatus")
    obj = db.query(model).filter(model.id == case_id).first()
    if obj is None:
        return None
    obj.status = case_status.CLOSED
    obj.closure_code = closure_code
    db.commit()
    db.refresh(obj)
    return obj


# -------- SIRA: Playbooks --------
def create_playbook(db: Session, playbook_in: Any):
    return _create(db, "Playbook", playbook_in)


def get_playbook(db: Session, playbook_id: int):
    return _get(db, "Playbook", playbook_id)


def list_playbooks(
    db: Session,
    incident_type: Optional[str] = None,
    domain: Optional[str] = None,
    skip: int = 0,
    limit: int = 100
):
    model = _get_model("Playbook")
    query = db.query(model)
    if incident_type:
        query = query.filter(model.incident_type == incident_type)
    if domain:
        query = query.filter(model.domain == domain)
    return query.offset(skip).limit(limit).all()


def update_playbook(db: Session, playbook_id: int, playbook_in: Any):
    model = _get_model("Playbook")
    obj = db.query(model).filter(model.id == playbook_id).first()
    if obj is None:
        return None
    update_data = _to_dict(playbook_in)
    for key, value in update_data.items():
        if value is not None:
            setattr(obj, key, value)
    db.commit()
    db.refresh(obj)
    return obj


def delete_playbook(db: Session, playbook_id: int) -> bool:
    model = _get_model("Playbook")
    obj = db.query(model).filter(model.id == playbook_id).first()
    if obj is None:
        return False
    db.delete(obj)
    db.commit()
    return True


# -------- SIRA: Evidence --------
def create_evidence(db: Session, evidence_in: Any, file_hash: str):
    model = _get_model("Evidence")
    data = _to_dict(evidence_in)
    data["file_hash"] = file_hash
    obj = model(**data)
    db.add(obj)
    db.commit()
    db.refresh(obj)
    return obj


def get_evidence(db: Session, evidence_id: int):
    return _get(db, "Evidence", evidence_id)


def list_evidence(db: Session, case_id: Optional[int] = None, skip: int = 0, limit: int = 100):
    model = _get_model("Evidence")
    query = db.query(model)
    if case_id:
        query = query.filter(model.case_id == case_id)
    return query.offset(skip).limit(limit).all()


def verify_evidence(db: Session, evidence_id: int, status: str):
    model = _get_model("Evidence")
    verification_status = _get_model("VerificationStatus")
    obj = db.query(model).filter(model.id == evidence_id).first()
    if obj is None:
        return None
    obj.verification_status = getattr(verification_status, status.upper())
    db.commit()
    db.refresh(obj)
    return obj
