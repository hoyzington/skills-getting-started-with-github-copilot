"""
Tests for validation and error handling
Tests edge cases, validation errors, and error responses
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


class TestSignupValidation:
    """Tests for validation in POST /activities/{activity_name}/signup"""

    def test_signup_activity_not_found(self):
        """Test that signup fails with 404 when activity doesn't exist"""
        client = TestClient(app)
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "Activity not found" in result["detail"]

    def test_signup_already_signed_up(self):
        """Test that signup fails with 400 when student already signed up"""
        client = TestClient(app)
        
        # Get an existing participant
        response = client.get("/activities")
        activities = response.json()
        existing_participant = activities["Chess Club"]["participants"][0]
        
        # Try to signup the same participant again
        response = client.post(
            f"/activities/Chess Club/signup?email={existing_participant}"
        )
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "already signed up" in result["detail"].lower()

    def test_signup_multiple_times_rejected(self):
        """Test that multiple signup attempts are rejected after first success"""
        client = TestClient(app)
        test_email = "duplicate@mergington.edu"
        
        # First signup should succeed
        response1 = client.post(
            f"/activities/Tennis Club/signup?email={test_email}"
        )
        assert response1.status_code == 200
        
        # Second signup should fail
        response2 = client.post(
            f"/activities/Tennis Club/signup?email={test_email}"
        )
        assert response2.status_code == 400

    def test_signup_to_different_activities_allowed(self):
        """Test that same student can signup to multiple different activities"""
        client = TestClient(app)
        test_email = "multiactivity@mergington.edu"
        
        # Signup to first activity
        response1 = client.post(
            f"/activities/Chess Club/signup?email={test_email}"
        )
        assert response1.status_code == 200
        
        # Signup to second activity
        response2 = client.post(
            f"/activities/Basketball/signup?email={test_email}"
        )
        assert response2.status_code == 200
        
        # Verify both signups
        response = client.get("/activities")
        activities = response.json()
        assert test_email in activities["Chess Club"]["participants"]
        assert test_email in activities["Basketball"]["participants"]


class TestUnregisterValidation:
    """Tests for validation in DELETE /activities/{activity_name}/unregister"""

    def test_unregister_activity_not_found(self):
        """Test that unregister fails with 404 when activity doesn't exist"""
        client = TestClient(app)
        response = client.delete(
            "/activities/Nonexistent Activity/unregister?email=test@mergington.edu"
        )
        assert response.status_code == 404
        result = response.json()
        assert "detail" in result
        assert "Activity not found" in result["detail"]

    def test_unregister_not_signed_up(self):
        """Test that unregister fails with 400 when student not signed up"""
        client = TestClient(app)
        response = client.delete(
            "/activities/Chess Club/unregister?email=notsigneddup@mergington.edu"
        )
        assert response.status_code == 400
        result = response.json()
        assert "detail" in result
        assert "not signed up" in result["detail"].lower()

    def test_unregister_nonexistent_participant(self):
        """Test that unregister fails when email never signed up"""
        client = TestClient(app)
        response = client.delete(
            "/activities/Gym Class/unregister?email=fake@example.com"
        )
        assert response.status_code == 400

    def test_unregister_already_unregistered(self):
        """Test that second unregister of same participant fails with 400"""
        client = TestClient(app)
        
        # Get an existing participant
        response = client.get("/activities")
        activities = response.json()
        participant = activities["Chess Club"]["participants"][0]
        
        # First unregister should succeed
        response1 = client.delete(
            f"/activities/Chess Club/unregister?email={participant}"
        )
        assert response1.status_code == 200
        
        # Second unregister should fail
        response2 = client.delete(
            f"/activities/Chess Club/unregister?email={participant}"
        )
        assert response2.status_code == 400


class TestDataIsolation:
    """Tests for data isolation and state management across requests"""

    def test_activities_list_not_modified_by_get(self):
        """Test that GET /activities doesn't modify the data"""
        client = TestClient(app)
        
        # Get activities twice
        response1 = client.get("/activities")
        activities1 = response1.json()
        response2 = client.get("/activities")
        activities2 = response2.json()
        
        # Should be identical
        assert activities1 == activities2

    def test_signup_and_unregister_roundtrip(self):
        """Test that signup followed by unregister returns to original state"""
        client = TestClient(app)
        test_email = "roundtrip@mergington.edu"
        
        # Get original state
        response = client.get("/activities")
        original_participants = response.json()["Basketball"]["participants"].copy()
        original_count = len(original_participants)
        
        # Signup
        client.post(
            f"/activities/Basketball/signup?email={test_email}"
        )
        
        # Verify signup
        response = client.get("/activities")
        assert len(response.json()["Basketball"]["participants"]) == original_count + 1
        
        # Unregister
        client.delete(
            f"/activities/Basketball/unregister?email={test_email}"
        )
        
        # Verify back to original
        response = client.get("/activities")
        assert len(response.json()["Basketball"]["participants"]) == original_count
        assert test_email not in response.json()["Basketball"]["participants"]

    def test_signup_persistence_across_requests(self):
        """Test that signup persists across multiple GET requests"""
        client = TestClient(app)
        test_email = "persistence@mergington.edu"
        
        # Signup
        client.post(
            f"/activities/Programming Class/signup?email={test_email}"
        )
        
        # Get activities multiple times
        for _ in range(3):
            response = client.get("/activities")
            activities = response.json()
            assert test_email in activities["Programming Class"]["participants"]


class TestErrorMessages:
    """Tests for appropriate error messages"""

    def test_activity_not_found_error_message(self):
        """Test that activity not found error has clear message"""
        client = TestClient(app)
        response = client.get("/activities")
        activities = response.json()
        original_count = len(activities)
        
        response = client.post(
            "/activities/Fake Activity Name/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_already_signed_up_error_message(self):
        """Test that already signed up error has clear message"""
        client = TestClient(app)
        response = client.get("/activities")
        activities = response.json()
        participant = activities["Theater Club"]["participants"][0]
        
        response = client.post(
            f"/activities/Theater Club/signup?email={participant}"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_not_signed_up_error_message(self):
        """Test that not signed up error has clear message"""
        client = TestClient(app)
        response = client.delete(
            "/activities/Science Club/unregister?email=notamember@mergington.edu"
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()
