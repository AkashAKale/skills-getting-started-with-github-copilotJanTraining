"""
Tests for the Mergington High School Activities API
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    yield
    # Reset participants to initial state after test
    activities["Basketball"]["participants"] = ["alex@mergington.edu"]
    activities["Tennis Club"]["participants"] = ["jordan@mergington.edu"]
    activities["Art Studio"]["participants"] = ["isabella@mergington.edu"]
    activities["Drama Club"]["participants"] = ["lucas@mergington.edu", "ava@mergington.edu"]
    activities["Debate Team"]["participants"] = ["noah@mergington.edu"]
    activities["Robotics Club"]["participants"] = ["ethan@mergington.edu", "mia@mergington.edu"]
    activities["Chess Club"]["participants"] = ["michael@mergington.edu", "daniel@mergington.edu"]
    activities["Programming Class"]["participants"] = ["emma@mergington.edu", "sophia@mergington.edu"]
    activities["Gym Class"]["participants"] = ["john@mergington.edu", "olivia@mergington.edu"]


class TestGetActivities:
    """Tests for GET /activities endpoint"""

    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """Test that get activities returns all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        data = response.json()
        assert "Basketball" in data
        assert "Tennis Club" in data
        assert "Drama Club" in data

    def test_get_activities_has_required_fields(self, client, reset_activities):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        data = response.json()
        for activity_name, activity_data in data.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_get_activities_participants_count(self, client, reset_activities):
        """Test that participants are correctly listed"""
        response = client.get("/activities")
        data = response.json()
        assert "alex@mergington.edu" in data["Basketball"]["participants"]
        assert "lucas@mergington.edu" in data["Drama Club"]["participants"]
        assert "ava@mergington.edu" in data["Drama Club"]["participants"]


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""

    def test_signup_for_activity_success(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "newstudent@mergington.edu" in data["message"]

    def test_signup_adds_participant(self, client, reset_activities):
        """Test that signup adds participant to activity"""
        client.post(
            "/activities/Basketball/signup",
            params={"email": "newstudent@mergington.edu"}
        )
        response = client.get("/activities")
        data = response.json()
        assert "newstudent@mergington.edu" in data["Basketball"]["participants"]

    def test_signup_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that signup for nonexistent activity returns 404"""
        response = client.post(
            "/activities/NonexistentActivity/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    def test_signup_duplicate_returns_400(self, client, reset_activities):
        """Test that duplicate signup returns 400"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()

    def test_signup_with_special_characters_in_activity_name(self, client, reset_activities):
        """Test signup with activity names containing special characters"""
        response = client.post(
            "/activities/Programming%20Class/signup",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for POST /activities/{activity_name}/unregister endpoint"""

    def test_unregister_success(self, client, reset_activities):
        """Test successful unregister from an activity"""
        response = client.post(
            "/activities/Basketball/unregister",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "alex@mergington.edu" in data["message"]

    def test_unregister_removes_participant(self, client, reset_activities):
        """Test that unregister removes participant from activity"""
        client.post(
            "/activities/Basketball/unregister",
            params={"email": "alex@mergington.edu"}
        )
        response = client.get("/activities")
        data = response.json()
        assert "alex@mergington.edu" not in data["Basketball"]["participants"]

    def test_unregister_nonexistent_activity_returns_404(self, client, reset_activities):
        """Test that unregister from nonexistent activity returns 404"""
        response = client.post(
            "/activities/NonexistentActivity/unregister",
            params={"email": "student@mergington.edu"}
        )
        assert response.status_code == 404

    def test_unregister_not_registered_returns_400(self, client, reset_activities):
        """Test that unregister for non-registered student returns 400"""
        response = client.post(
            "/activities/Basketball/unregister",
            params={"email": "notstudent@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not registered" in response.json()["detail"].lower()

    def test_unregister_then_signup_again(self, client, reset_activities):
        """Test that student can signup after unregistering"""
        # First unregister
        client.post(
            "/activities/Basketball/unregister",
            params={"email": "alex@mergington.edu"}
        )
        # Then signup again
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "alex@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify participant is back
        activities_response = client.get("/activities")
        data = activities_response.json()
        assert "alex@mergington.edu" in data["Basketball"]["participants"]


class TestIntegration:
    """Integration tests for multiple operations"""

    def test_signup_and_unregister_multiple_students(self, client, reset_activities):
        """Test multiple students signing up and unregistering"""
        # Signup multiple students
        for i in range(3):
            email = f"student{i}@mergington.edu"
            response = client.post(
                "/activities/Tennis Club/signup",
                params={"email": email}
            )
            assert response.status_code == 200

        # Check all are registered
        response = client.get("/activities")
        data = response.json()
        assert len(data["Tennis Club"]["participants"]) == 4  # Original + 3 new

        # Unregister one
        response = client.post(
            "/activities/Tennis Club/unregister",
            params={"email": "student1@mergington.edu"}
        )
        assert response.status_code == 200

        # Check count decreased
        response = client.get("/activities")
        data = response.json()
        assert len(data["Tennis Club"]["participants"]) == 3

    def test_activity_capacity_tracking(self, client, reset_activities):
        """Test that activity capacity information is correctly maintained"""
        response = client.get("/activities")
        data = response.json()
        
        basketball = data["Basketball"]
        assert basketball["max_participants"] == 15
        assert len(basketball["participants"]) == 1

        # Signup new student
        client.post(
            "/activities/Basketball/signup",
            params={"email": "student@mergington.edu"}
        )

        response = client.get("/activities")
        data = response.json()
        assert len(data["Basketball"]["participants"]) == 2
