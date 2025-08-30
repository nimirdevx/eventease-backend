"""
Tests for event endpoints
"""
import pytest
from datetime import datetime, timedelta
from tests.conftest import create_test_user, login_test_user, get_auth_headers

class TestEvents:
    
    def test_get_events_empty(self, client):
        """Test getting events when no events exist"""
        response = client.get("/events/")
        assert response.status_code == 200
        assert response.json() == []

    def test_create_event_success(self, client, test_organizer_data, test_event_data):
        """Test successful event creation"""
        # Register organizer and login
        client.post("/auth/register", json=test_organizer_data)
        token = login_test_user(client, test_organizer_data["email"], test_organizer_data["password"])
        headers = get_auth_headers(token)
        
        response = client.post("/events/", json=test_event_data, headers=headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == test_event_data["title"]
        assert data["description"] == test_event_data["description"]
        assert "id" in data
        assert "organizer_id" in data

    def test_create_event_unauthorized(self, client, test_event_data):
        """Test creating event without authentication"""
        response = client.post("/events/", json=test_event_data)
        assert response.status_code == 401

    def test_create_event_validation_errors(self, client, test_organizer_data):
        """Test creating event with validation errors"""
        # Register organizer and login
        client.post("/auth/register", json=test_organizer_data)
        token = login_test_user(client, test_organizer_data["email"], test_organizer_data["password"])
        headers = get_auth_headers(token)
        
        invalid_event_data = {
            "title": "AB",  # Too short
            "description": "Valid description",
            "date": "2020-01-01T00:00:00"  # Past date
        }
        
        response = client.post("/events/", json=invalid_event_data, headers=headers)
        assert response.status_code == 422
        data = response.json()
        assert data["error"] is True

    def test_create_event_past_date(self, client, test_organizer_data):
        """Test creating event with past date"""
        # Register organizer and login
        client.post("/auth/register", json=test_organizer_data)
        token = login_test_user(client, test_organizer_data["email"], test_organizer_data["password"])
        headers = get_auth_headers(token)
        
        past_date = datetime.now() - timedelta(days=1)
        invalid_event_data = {
            "title": "Valid Title",
            "description": "Valid description",
            "date": past_date.isoformat()
        }
        
        response = client.post("/events/", json=invalid_event_data, headers=headers)
        assert response.status_code == 422

    def test_get_event_by_id(self, client, test_organizer_data, test_event_data):
        """Test getting specific event by ID"""
        # Register organizer and create event
        client.post("/auth/register", json=test_organizer_data)
        token = login_test_user(client, test_organizer_data["email"], test_organizer_data["password"])
        headers = get_auth_headers(token)
        
        create_response = client.post("/events/", json=test_event_data, headers=headers)
        event_id = create_response.json()["id"]
        
        # Get event by ID
        response = client.get(f"/events/{event_id}")
        assert response.status_code == 200
        data = response.json()
        assert data["id"] == event_id
        assert data["title"] == test_event_data["title"]

    def test_get_nonexistent_event(self, client):
        """Test getting non-existent event"""
        response = client.get("/events/999")
        assert response.status_code == 404
        data = response.json()
        assert data["error"] is True
        assert "not found" in data["message"]

    def test_update_event_success(self, client, test_organizer_data, test_event_data):
        """Test successful event update"""
        # Register organizer and create event
        client.post("/auth/register", json=test_organizer_data)
        token = login_test_user(client, test_organizer_data["email"], test_organizer_data["password"])
        headers = get_auth_headers(token)
        
        create_response = client.post("/events/", json=test_event_data, headers=headers)
        event_id = create_response.json()["id"]
        
        # Update event
        updated_data = {
            "title": "Updated Event Title",
            "description": "Updated description",
            "date": "2025-12-31T23:59:59"
        }
        
        response = client.put(f"/events/{event_id}", json=updated_data, headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == updated_data["title"]
        assert data["description"] == updated_data["description"]

    def test_update_event_unauthorized(self, client, test_organizer_data, test_user_data, test_event_data):
        """Test updating event by non-organizer"""
        # Register organizer and create event
        client.post("/auth/register", json=test_organizer_data)
        organizer_token = login_test_user(client, test_organizer_data["email"], test_organizer_data["password"])
        organizer_headers = get_auth_headers(organizer_token)
        
        create_response = client.post("/events/", json=test_event_data, headers=organizer_headers)
        event_id = create_response.json()["id"]
        
        # Register different user and try to update event
        client.post("/auth/register", json=test_user_data)
        user_token = login_test_user(client, test_user_data["email"], test_user_data["password"])
        user_headers = get_auth_headers(user_token)
        
        updated_data = {
            "title": "Unauthorized Update",
            "description": "This should fail",
            "date": "2025-12-31T23:59:59"
        }
        
        response = client.put(f"/events/{event_id}", json=updated_data, headers=user_headers)
        assert response.status_code == 403

    def test_delete_event_success(self, client, test_organizer_data, test_event_data):
        """Test successful event deletion"""
        # Register organizer and create event
        client.post("/auth/register", json=test_organizer_data)
        token = login_test_user(client, test_organizer_data["email"], test_organizer_data["password"])
        headers = get_auth_headers(token)
        
        create_response = client.post("/events/", json=test_event_data, headers=headers)
        event_id = create_response.json()["id"]
        
        # Delete event
        response = client.delete(f"/events/{event_id}", headers=headers)
        assert response.status_code == 200
        
        # Verify event is deleted
        get_response = client.get(f"/events/{event_id}")
        assert get_response.status_code == 404

    def test_register_for_event_success(self, client, test_organizer_data, test_user_data, test_event_data):
        """Test successful event registration"""
        # Register organizer and create event
        client.post("/auth/register", json=test_organizer_data)
        organizer_token = login_test_user(client, test_organizer_data["email"], test_organizer_data["password"])
        organizer_headers = get_auth_headers(organizer_token)
        
        create_response = client.post("/events/", json=test_event_data, headers=organizer_headers)
        event_id = create_response.json()["id"]
        
        # Register user and register for event
        client.post("/auth/register", json=test_user_data)
        user_token = login_test_user(client, test_user_data["email"], test_user_data["password"])
        user_headers = get_auth_headers(user_token)
        
        response = client.post(f"/events/{event_id}/register", headers=user_headers)
        assert response.status_code == 200
        data = response.json()
        assert "Successfully registered" in data["message"]
        assert "ticket_code" in data

    def test_register_for_nonexistent_event(self, client, test_user_data):
        """Test registering for non-existent event"""
        client.post("/auth/register", json=test_user_data)
        token = login_test_user(client, test_user_data["email"], test_user_data["password"])
        headers = get_auth_headers(token)
        
        response = client.post("/events/999/register", headers=headers)
        assert response.status_code == 404

    def test_register_for_event_twice(self, client, test_organizer_data, test_user_data, test_event_data):
        """Test registering for same event twice"""
        # Register organizer and create event
        client.post("/auth/register", json=test_organizer_data)
        organizer_token = login_test_user(client, test_organizer_data["email"], test_organizer_data["password"])
        organizer_headers = get_auth_headers(organizer_token)
        
        create_response = client.post("/events/", json=test_event_data, headers=organizer_headers)
        event_id = create_response.json()["id"]
        
        # Register user and register for event
        client.post("/auth/register", json=test_user_data)
        user_token = login_test_user(client, test_user_data["email"], test_user_data["password"])
        user_headers = get_auth_headers(user_token)
        
        # First registration
        response1 = client.post(f"/events/{event_id}/register", headers=user_headers)
        assert response1.status_code == 200
        
        # Second registration (should fail)
        response2 = client.post(f"/events/{event_id}/register", headers=user_headers)
        assert response2.status_code == 409

    def test_cancel_registration_success(self, client, test_organizer_data, test_user_data, test_event_data):
        """Test successful registration cancellation"""
        # Register organizer and create event
        client.post("/auth/register", json=test_organizer_data)
        organizer_token = login_test_user(client, test_organizer_data["email"], test_organizer_data["password"])
        organizer_headers = get_auth_headers(organizer_token)
        
        create_response = client.post("/events/", json=test_event_data, headers=organizer_headers)
        event_id = create_response.json()["id"]
        
        # Register user and register for event
        client.post("/auth/register", json=test_user_data)
        user_token = login_test_user(client, test_user_data["email"], test_user_data["password"])
        user_headers = get_auth_headers(user_token)
        
        # Register for event
        client.post(f"/events/{event_id}/register", headers=user_headers)
        
        # Cancel registration
        response = client.delete(f"/events/{event_id}/register", headers=user_headers)
        assert response.status_code == 200

    def test_get_my_events(self, client, test_organizer_data, test_event_data):
        """Test getting user's created events"""
        # Register organizer and create event
        client.post("/auth/register", json=test_organizer_data)
        token = login_test_user(client, test_organizer_data["email"], test_organizer_data["password"])
        headers = get_auth_headers(token)
        
        client.post("/events/", json=test_event_data, headers=headers)
        
        response = client.get("/events/my", headers=headers)
        assert response.status_code == 200
        data = response.json()
        assert len(data) == 1
        assert data[0]["title"] == test_event_data["title"]
