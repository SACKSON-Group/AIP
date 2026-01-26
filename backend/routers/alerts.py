# routers/alerts.py
"""
Alerts router for SIRA Platform.
Handles security alerts with filtering and RBAC.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from backend.schemas import AlertCreate, AlertUpdate, AlertResponse
from backend.crud import create_alert, get_alert, list_alerts, update_alert
from backend.database import get_db
from backend.auth import get_current_user
from backend.models import User, AlertStatus, AlertSeverity

router = APIRouter(prefix="/alerts", tags=["alerts"])

# Roles allowed to create/update alerts
ALERT_CREATE_ROLES = ["security_lead", "admin"]
ALERT_UPDATE_ROLES = ["security_lead", "admin", "operator"]
ALERT_READ_ROLES = ["operator", "supervisor", "admin", "security_lead", "viewer"]


def require_create_access(current_user: User = Depends(get_current_user)) -> User:
    """Require create access for alert operations."""
    if current_user.role not in ALERT_CREATE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to create alerts"
        )
    return current_user


def require_update_access(current_user: User = Depends(get_current_user)) -> User:
    """Require update access for alert operations."""
    if current_user.role not in ALERT_UPDATE_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to update alerts"
        )
    return current_user


def require_read_access(current_user: User = Depends(get_current_user)) -> User:
    """Require read access for alert operations."""
    if current_user.role not in ALERT_READ_ROLES:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Insufficient permissions to view alerts"
        )
    return current_user


@router.post("/", response_model=AlertResponse, status_code=status.HTTP_201_CREATED)
def create(
    alert: AlertCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_create_access)
):
    """Create a new security alert."""
    return create_alert(db, alert)


@router.get("/", response_model=List[AlertResponse])
def list_all(
    domain: Optional[str] = Query(None, description="Filter by domain"),
    alert_status: Optional[str] = Query(None, alias="status", description="Filter by status"),
    severity: Optional[str] = Query(None, description="Filter by severity"),
    skip: int = Query(0, ge=0, description="Number of records to skip"),
    limit: int = Query(100, ge=1, le=1000, description="Maximum number of records to return"),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """List all alerts with optional filtering."""
    return list_alerts(
        db,
        domain=domain,
        status=alert_status,
        severity=severity,
        skip=skip,
        limit=limit
    )


@router.get("/{alert_id}", response_model=AlertResponse)
def read(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_read_access)
):
    """Get an alert by ID."""
    db_alert = get_alert(db, alert_id)
    if db_alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return db_alert


@router.put("/{alert_id}", response_model=AlertResponse)
def update(
    alert_id: int,
    alert: AlertUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_update_access)
):
    """Update an alert."""
    db_alert = update_alert(db, alert_id, alert)
    if db_alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")
    return db_alert


@router.post("/{alert_id}/acknowledge", response_model=AlertResponse)
def acknowledge(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_update_access)
):
    """Acknowledge an alert."""
    db_alert = get_alert(db, alert_id)
    if db_alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    if db_alert.status != AlertStatus.OPEN:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only open alerts can be acknowledged"
        )

    update_data = AlertUpdate(status=AlertStatus.ACKNOWLEDGED)
    return update_alert(db, alert_id, update_data)


@router.post("/{alert_id}/assign", response_model=AlertResponse)
def assign_to_case(
    alert_id: int,
    case_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_update_access)
):
    """Assign an alert to a case."""
    db_alert = get_alert(db, alert_id)
    if db_alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    # Verify case exists
    from backend.crud import get_case
    db_case = get_case(db, case_id)
    if db_case is None:
        raise HTTPException(status_code=404, detail="Case not found")

    update_data = AlertUpdate(case_id=case_id, status=AlertStatus.ASSIGNED)
    return update_alert(db, alert_id, update_data)


@router.post("/{alert_id}/close", response_model=AlertResponse)
def close(
    alert_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_update_access)
):
    """Close an alert."""
    db_alert = get_alert(db, alert_id)
    if db_alert is None:
        raise HTTPException(status_code=404, detail="Alert not found")

    update_data = AlertUpdate(status=AlertStatus.CLOSED)
    return update_alert(db, alert_id, update_data)
