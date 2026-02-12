"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app

client = TestClient(app)


class TestActivitiesEndpoint:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_200(self):
        """Test that GET /activities returns 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_dict(self):
        """Test that GET /activities returns a dictionary"""
        response = client.get("/activities")
        data = response.json()
        assert isinstance(data, dict)

    def test_activities_have_required_fields(self):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        
        for activity_name, activity_details in data.items():
            assert isinstance(activity_name, str)
            assert "description" in activity_details
            assert "schedule" in activity_details
            assert "max_participants" in activity_details
            assert "participants" in activity_details
            assert isinstance(activity_details["participants"], list)

    def test_chess_club_exists(self):
        """Test that Chess Club activity exists"""
        response = client.get("/activities")
        data = response.json()
        assert "Chess Club" in data


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_valid_activity_and_email(self):
        """Test signing up for a valid activity with valid email"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]

    def test_signup_nonexistent_activity(self):
        """Test signing up for non-existent activity returns 404"""
        response = client.post(
            "/activities/Fake Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_duplicate_registration(self):
        """Test that duplicate registrations are rejected"""
        email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response1.status_code == 200
        
        # Second signup with same email should fail
        response2 = client.post(
            "/activities/Programming Class/signup",
            params={"email": email}
        )
        assert response2.status_code == 400
        assert "already signed up" in response2.json()["detail"].lower()

    def test_signup_adds_participant_to_list(self):
        """Test that signup actually adds the participant to the activity"""
        email = "verify@mergington.edu"
        activity = "Basketball"
        
        # Get initial participant count
        response_before = client.get("/activities")
        initial_count = len(response_before.json()[activity]["participants"])
        
        # Sign up
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Verify participant was added
        response_after = client.get("/activities")
        final_count = len(response_after.json()[activity]["participants"])
        
        assert final_count == initial_count + 1
        assert email in response_after.json()[activity]["participants"]


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_valid_participant(self):
        """Test unregistering an existing participant"""
        activity = "Tennis Club"
        
        # First, sign up a participant
        email = "tounregister@mergington.edu"
        client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        
        # Verify they're signed up
        response = client.get("/activities")
        assert email in response.json()[activity]["participants"]
        
        # Now unregister them
        response_delete = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert response_delete.status_code == 200
        assert "Unregistered" in response_delete.json()["message"]
        
        # Verify they're removed
        response_after = client.get("/activities")
        assert email not in response_after.json()[activity]["participants"]

    def test_unregister_nonexistent_activity(self):
        """Test unregistering from non-existent activity returns 404"""
        response = client.delete(
            "/activities/Fake Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404

    def test_unregister_not_signed_up(self):
        """Test unregistering someone not signed up returns 400"""
        response = client.delete(
            "/activities/Art Studio/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()


class TestRootEndpoint:
    """Tests for root endpoint"""

    def test_root_redirects_to_static(self):
        """Test that GET / redirects to /static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"
