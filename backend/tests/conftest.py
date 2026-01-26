# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from fastapi.testclient import TestClient

from backend.database import Base, get_db
from backend.main import app


# Use in-memory SQLite for tests
SQLALCHEMY_DATABASE_URL = "sqlite:///:memory:"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database session for each test."""
    Base.metadata.create_all(bind=engine)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with overridden database dependency."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture
def sample_investor_data():
    """Sample investor data for testing."""
    return {
        "fund_name": "Africa Growth Fund",
        "aum": 500000000.0,
        "ticket_size_min": 1000000.0,
        "ticket_size_max": 50000000.0,
        "instruments": ["Equity", "Debt"],
        "target_irr": 15.0,
        "country_focus": ["Nigeria", "Kenya", "South Africa"],
        "sector_focus": ["Energy", "Transport"],
        "esg_constraints": "No coal projects"
    }


@pytest.fixture
def sample_project_data():
    """Sample project data for testing."""
    return {
        "name": "Lagos Solar Farm",
        "sector": "Energy",
        "country": "Nigeria",
        "region": "Lagos",
        "stage": "Feasibility",
        "estimated_capex": 50000000.0,
        "funding_gap": 30000000.0,
        "revenue_model": "PPA with government"
    }


@pytest.fixture
def sample_user_data():
    """Sample user data for testing."""
    return {
        "username": "testuser",
        "password": "securepassword123",
        "role": "investor"
    }


@pytest.fixture
def created_investor(client, sample_investor_data):
    """Create and return an investor."""
    response = client.post("/investors/", json=sample_investor_data)
    return response.json()


# SIRA Platform test fixtures

@pytest.fixture
def sample_movement_data():
    """Sample movement data for testing."""
    return {
        "cargo": "Crude Oil - 50,000 barrels",
        "route": "Lagos Port to Rotterdam",
        "assets": "Tanker MV Ocean Star",
        "stakeholders": "Shell Nigeria, EP Trading",
        "laycan_start": "2026-02-01T00:00:00",
        "laycan_end": "2026-02-05T00:00:00"
    }


@pytest.fixture
def sample_alert_data():
    """Sample alert data for testing."""
    return {
        "severity": "High",
        "confidence": 0.85,
        "sla_timer": 60,
        "domain": "Maritime Security",
        "site_zone": "Gulf of Guinea"
    }


@pytest.fixture
def sample_case_data():
    """Sample case data for testing."""
    return {
        "overview": "Suspected piracy attempt near Port Harcourt",
        "timeline": '{"events": []}',
        "actions": '{"actions": []}',
        "costs": 0.0,
        "parties": "Local authorities, Navy patrol"
    }


@pytest.fixture
def sample_playbook_data():
    """Sample playbook data for testing."""
    return {
        "incident_type": "Piracy Attempt",
        "domain": "Maritime Security",
        "steps": '[{"step": 1, "action": "Alert nearby vessels"}, {"step": 2, "action": "Contact navy"}]'
    }


@pytest.fixture
def sample_evidence_data():
    """Sample evidence data for testing (requires case_id)."""
    return {
        "evidence_type": "photo",
        "file_ref": "/uploads/evidence/incident_photo_001.jpg",
        "metadata_json": '{"uploader": "field_agent", "timestamp": "2026-01-26T10:30:00"}'
    }


@pytest.fixture
def auth_headers(client, db_session):
    """Create an authenticated user and return auth headers."""
    from backend.models import User
    from backend.auth import get_password_hash, create_access_token
    from datetime import timedelta

    # Create a test user directly in the database
    test_user = User(
        username="testoperator",
        hashed_password=get_password_hash("testpass123"),
        role="operator"
    )
    db_session.add(test_user)
    db_session.commit()

    # Create access token
    token = create_access_token(
        data={"sub": test_user.username},
        expires_delta=timedelta(minutes=30)
    )

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def admin_auth_headers(client, db_session):
    """Create an admin user and return auth headers."""
    from backend.models import User
    from backend.auth import get_password_hash, create_access_token
    from datetime import timedelta

    test_user = User(
        username="testadmin",
        hashed_password=get_password_hash("adminpass123"),
        role="admin"
    )
    db_session.add(test_user)
    db_session.commit()

    token = create_access_token(
        data={"sub": test_user.username},
        expires_delta=timedelta(minutes=30)
    )

    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def security_lead_auth_headers(client, db_session):
    """Create a security lead user and return auth headers."""
    from backend.models import User
    from backend.auth import get_password_hash, create_access_token
    from datetime import timedelta

    test_user = User(
        username="testsecuritylead",
        hashed_password=get_password_hash("secpass123"),
        role="security_lead"
    )
    db_session.add(test_user)
    db_session.commit()

    token = create_access_token(
        data={"sub": test_user.username},
        expires_delta=timedelta(minutes=30)
    )

    return {"Authorization": f"Bearer {token}"}
