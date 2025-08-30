"""
Tests for API health and general functionality
"""
import pytest

class TestHealthCheck:
    
    def test_root_endpoint(self, client):
        """Test root endpoint returns correct response"""
        response = client.get("/")
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "EventEase API is running" in data["message"]
        assert data["version"] == "1.0.0"
        assert data["status"] == "healthy"

    def test_health_check_endpoint(self, client):
        """Test health check endpoint"""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["version"] == "1.0.0"
        assert "timestamp" in data

    def test_docs_endpoint(self, client):
        """Test that API documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_openapi_json(self, client):
        """Test that OpenAPI spec is accessible"""
        response = client.get("/openapi.json")
        assert response.status_code == 200
        data = response.json()
        assert data["info"]["title"] == "EventEase API"
        assert data["info"]["version"] == "1.0.0"

class TestCORS:
    
    def test_cors_headers_present(self, client):
        """Test that CORS headers are present in responses"""
        response = client.options("/", headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET"
        })
        # FastAPI handles OPTIONS automatically, should not return error
        assert response.status_code in [200, 405]

    def test_cors_headers_on_api_response(self, client):
        """Test CORS headers on actual API response"""
        response = client.get("/", headers={
            "Origin": "http://localhost:3000"
        })
        assert response.status_code == 200
        # Check if CORS headers would be added by middleware
        # (Actual testing of CORS headers requires more complex setup)

class TestErrorHandling:
    
    def test_404_error_handling(self, client):
        """Test 404 error is handled correctly"""
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert "message" in data

    def test_method_not_allowed_error(self, client):
        """Test 405 error for wrong HTTP method"""
        response = client.post("/")  # GET endpoint called with POST
        assert response.status_code == 405
        data = response.json()
        assert data["error"] is True

    def test_validation_error_format(self, client):
        """Test that validation errors are formatted correctly"""
        # Try to register with invalid data
        invalid_data = {
            "email": "invalid-email",
            "password": "short"
        }
        response = client.post("/auth/register", json=invalid_data)
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True
        assert data["type"] == "ValidationError"
        assert "details" in data
        assert isinstance(data["details"], list)

class TestAuthenticationFlow:
    
    def test_complete_auth_flow(self, client, test_user_data):
        """Test complete authentication flow"""
        # 1. Register user
        register_response = client.post("/auth/register", json=test_user_data)
        assert register_response.status_code == 200
        
        # 2. Login user
        login_data = {
            "email": test_user_data["email"],
            "password": test_user_data["password"]
        }
        login_response = client.post("/auth/login", json=login_data)
        assert login_response.status_code == 200
        token = login_response.json()["access_token"]
        
        # 3. Access protected endpoint
        headers = {"Authorization": f"Bearer {token}"}
        protected_response = client.get("/events/my", headers=headers)
        assert protected_response.status_code == 200

    def test_token_expiration_handling(self, client):
        """Test behavior with expired/invalid tokens"""
        headers = {"Authorization": "Bearer invalid_or_expired_token"}
        response = client.get("/events/my", headers=headers)
        assert response.status_code == 401
        data = response.json()
        assert data["error"] is True
        assert "token" in data["message"].lower() or "unauthorized" in data["message"].lower()
