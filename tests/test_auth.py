"""
Tests for authentication endpoints
"""
import pytest
from tests.conftest import create_test_user, login_test_user

class TestAuth:
    
    def test_register_user_success(self, client, test_user_data):
        """Test successful user registration"""
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == test_user_data["name"]
        assert data["email"] == test_user_data["email"]
        assert data["role"] == test_user_data["role"]
        assert "id" in data
        assert "password" not in data  # Password should not be returned

    def test_register_user_duplicate_email(self, client, test_user_data):
        """Test registration with duplicate email"""
        # Create first user
        client.post("/auth/register", json=test_user_data)
        
        # Try to create second user with same email
        response = client.post("/auth/register", json=test_user_data)
        
        assert response.status_code == 409
        data = response.json()
        assert data["error"] is True
        assert "already exists" in data["message"]

    def test_register_user_validation_errors(self, client):
        """Test registration with validation errors"""
        invalid_data = {
            "name": "J",  # Too short
            "email": "invalid-email",  # Invalid email
            "password": "weak",  # Too weak
            "role": "invalid_role"  # Invalid role
        }
        
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert "Validation failed" in data["message"]

    def test_register_empty_name(self, client):
        """Test registration with empty name"""
        invalid_data = {
            "name": "",
            "email": "test@example.com",
            "password": "ValidPass123!",
            "role": "attendee"
        }
        
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422

    def test_register_weak_password(self, client):
        """Test registration with weak password"""
        invalid_data = {
            "name": "John Doe",
            "email": "test@example.com",
            "password": "password",  # No uppercase, numbers, or special chars
            "role": "attendee"
        }
        
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422
        data = response.json()
        assert "uppercase" in str(data["details"]).lower()

    def test_login_success(self, client, test_user_data):
        """Test successful login"""
        # Register user first
        client.post("/auth/register", json=test_user_data)
        
        # Login
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_credentials(self, client, test_user_data):
        """Test login with invalid credentials"""
        # Register user first
        client.post("/auth/register", json=test_user_data)
        
        # Try login with wrong password
        login_data = {
            "email": test_user_data["email"],
            "password": "wrongpassword"
        }
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "Invalid credentials" in data["message"]

    def test_login_nonexistent_user(self, client):
        """Test login with non-existent user"""
        login_data = {
            "email": "nonexistent@example.com",
            "password": "SomePassword123!"
        }
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "Invalid credentials" in data["message"]

    def test_login_validation_errors(self, client):
        """Test login with validation errors"""
        login_data = {
            "email": "invalid-email",
            "password": ""
        }
        response = client.post("/auth/login", json=login_data)
        
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert "Validation failed" in data["message"]

    def test_protected_endpoint_without_token(self, client):
        """Test accessing protected endpoint without token"""
        response = client.get("/events/my")
        assert response.status_code == 401

    def test_protected_endpoint_with_invalid_token(self, client):
        """Test accessing protected endpoint with invalid token"""
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/events/my", headers=headers)
        assert response.status_code == 401

    def test_protected_endpoint_with_valid_token(self, client, test_user_data):
        """Test accessing protected endpoint with valid token"""
        # Register and login
        client.post("/auth/register", json=test_user_data)
        token = login_test_user(client, test_user_data["email"], test_user_data["password"])
        
        headers = {"Authorization": f"Bearer {token}"}
        response = client.get("/events/my", headers=headers)
        assert response.status_code == 200
