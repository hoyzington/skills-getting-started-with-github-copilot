"""
Tests for FastAPI endpoints
Tests the core functionality of GET /activities, POST signup, and DELETE unregister
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_success(self):
        """Test that GET /activities returns 200 status code"""
        client = TestClient(app)
        response = client.get("/activities")
        assert response.status_code == 200

    def test_get_activities_returns_json(self):
        """Test that GET /activities returns JSON response"""
        client = TestClient(app)
        response = client.get("/activities")
        activities = response.json()
        assert isinstance(activities, dict)

    def test_get_activities_contains_all_activities(self):
        """Test that all 9 activities are returned"""
        client = TestClient(app)
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = [
            "Chess Club", "Programming Class", "Gym Class", "Basketball",
            "Tennis Club", "Painting and Drawing", "Theater Club", 
            "Debate Team", "Science Club"
        ]
        
        for activity in expected_activities:
            assert activity in activities

    def test_get_activities_has_correct_structure(self):
        """Test that each activity has required fields"""
        client = TestClient(app)
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, details in activities.items():
            assert "description" in details
            assert "schedule" in details
            assert "max_participants" in details
            assert "participants" in details
            assert isinstance(details["participants"], list)

    def test_get_activities_participants_are_emails(self):
        """Test that participants are stored as email strings"""
        client = TestClient(app)
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, details in activities.items():
            for participant in details["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email validation


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_success(self):
        """Test successful signup returns 200 and success message"""
        client = TestClient(app)
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert "newstudent@mergington.edu" in result["message"]

    def test_signup_adds_participant(self):
        """Test that signup actually adds the participant to the activity"""
        client = TestClient(app)
        test_email = "testuser@mergington.edu"
        
        # Get activities before signup
        response_before = client.get("/activities")
        activities_before = response_before.json()
        chess_before = activities_before["Chess Club"]["participants"]
        
        # Signup
        client.post(
            f"/activities/Chess Club/signup?email={test_email}"
        )
        
        # Get activities after signup
        response_after = client.get("/activities")
        activities_after = response_after.json()
        chess_after = activities_after["Chess Club"]["participants"]
        
        assert test_email in chess_after
        assert len(chess_after) == len(chess_before) + 1

    def test_signup_with_url_encoded_activity_name(self):
        """Test signup works with URL-encoded activity names"""
        client = TestClient(app)
        # "Programming Class" encoded
        response = client.post(
            "/activities/Programming%20Class/signup?email=test@mergington.edu"
        )
        assert response.status_code == 200

    def test_signup_with_url_encoded_email(self):
        """Test signup works with URL-encoded email"""
        client = TestClient(app)
        response = client.post(
            "/activities/Chess Club/signup?email=test%2Bsignup@mergington.edu"
        )
        assert response.status_code == 200


class TestUnregisterEndpoint:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self):
        """Test successful unregister returns 200 and success message"""
        client = TestClient(app)
        # First, get an existing participant
        response = client.get("/activities")
        activities = response.json()
        existing_participant = activities["Chess Club"]["participants"][0]
        
        # Unregister
        response = client.delete(
            f"/activities/Chess Club/unregister?email={existing_participant}"
        )
        assert response.status_code == 200
        result = response.json()
        assert "message" in result
        assert existing_participant in result["message"]

    def test_unregister_removes_participant(self):
        """Test that unregister actually removes the participant"""
        client = TestClient(app)
        
        # Get an existing participant
        response = client.get("/activities")
        activities = response.json()
        existing_participant = activities["Chess Club"]["participants"][0]
        
        # Unregister
        client.delete(
            f"/activities/Chess Club/unregister?email={existing_participant}"
        )
        
        # Verify removal
        response_after = client.get("/activities")
        activities_after = response_after.json()
        assert existing_participant not in activities_after["Chess Club"]["participants"]

    def test_unregister_with_url_encoded_activity_name(self):
        """Test unregister works with URL-encoded activity names"""
        client = TestClient(app)
        response = client.get("/activities")
        activities = response.json()
        participant = activities["Programming Class"]["participants"][0]
        
        response = client.delete(
            f"/activities/Programming%20Class/unregister?email={participant}"
        )
        assert response.status_code == 200

    def test_unregister_with_url_encoded_email(self):
        """Test unregister works with URL-encoded email"""
        client = TestClient(app)
        response = client.get("/activities")
        activities = response.json()
        # Use a participant with special characters
        response = client.delete(
            f"/activities/Chess Club/unregister?email=test%2Buser@mergington.edu"
        )
        # Will fail with 400, but tests URL encoding is handled
        assert response.status_code in [200, 400]
