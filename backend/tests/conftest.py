# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import httpx
from starlette.testclient import TestClient

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

    # Use httpx with ASGITransport for newer httpx versions
    try:
        transport = httpx.ASGITransport(app=app)
        test_client = httpx.Client(transport=transport, base_url="http://test")
    except (AttributeError, TypeError):
        # Fallback for older versions
        test_client = TestClient(app)

    yield test_client

    if hasattr(test_client, 'close'):
        test_client.close()
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
