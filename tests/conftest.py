"""
Test configuration and fixtures
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.main import app
from app.database import get_db, Base
from app import models

# Create test database
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

@pytest.fixture(scope="function")
def test_db():
    # Create tables
    Base.metadata.create_all(bind=engine)
    yield
    # Drop tables
    Base.metadata.drop_all(bind=engine)

@pytest.fixture(scope="function")
def client(test_db):
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()

@pytest.fixture
def test_user_data():
    return {
        "name": "John Doe",
        "email": "john@example.com",
        "password": "SecurePass123!",
        "role": "attendee"
    }

@pytest.fixture
def test_organizer_data():
    return {
        "name": "Jane Smith",
        "email": "jane@example.com",
        "password": "OrganizerPass456!",
        "role": "organizer"
    }

@pytest.fixture
def test_event_data():
    return {
        "title": "Test Event",
        "description": "This is a test event",
        "date": "2025-12-31T23:59:59"
    }

@pytest.fixture
def test_comment_data():
    return {
        "content": "This is a test comment"
    }

def create_test_user(client, user_data):
    """Helper function to create a test user"""
    response = client.post("/auth/register", json=user_data)
    return response

def login_test_user(client, email, password):
    """Helper function to login and get token"""
    response = client.post("/auth/login", json={
        "email": email,
        "password": password
    })
    if response.status_code == 200:
        return response.json()["access_token"]
    return None

def get_auth_headers(token):
    """Helper function to get authorization headers"""
    return {"Authorization": f"Bearer {token}"}
