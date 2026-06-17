"""
Test suite for High School Management System FastAPI application.

Uses AAA (Arrange-Act-Assert) pattern for test structure:
- Arrange: Set up test data and initial conditions
- Act: Execute the API endpoint being tested
- Assert: Verify response status/body and database state changes
"""

import pytest
from src.app import activities


# ============================================================================
# GET /activities Tests
# ============================================================================

class TestGetActivities:
    """Tests for retrieving all activities"""
    
    def test_get_activities_returns_all_activities(self, client, reset_activities):
        """
        Test successful retrieval of all activities.
        
        Arrange: Prepare client and endpoint
        Act: Make GET request to /activities
        Assert: Verify 200 status and all activities present in response
        """
        # Arrange
        expected_activities_count = len(activities)
        
        # Act
        response = client.get("/activities")
        
        # Assert
        assert response.status_code == 200
        data = response.json()
        assert len(data) == expected_activities_count
        assert "Chess Club" in data
        assert "Programming Class" in data
    
    def test_activity_has_required_fields(self, client, reset_activities):
        """
        Test that each activity has all required fields.
        
        Arrange: Define expected fields
        Act: Get all activities and check structure
        Assert: Verify all required fields present in each activity
        """
        # Arrange
        required_fields = {"description", "schedule", "max_participants", "participants"}
        
        # Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            for field in required_fields:
                assert field in activity_data, f"Missing field '{field}' in {activity_name}"
                
            # Verify participants is a list
            assert isinstance(activity_data["participants"], list)
    
    def test_activity_participants_format(self, client, reset_activities):
        """
        Test that participants are stored as email strings in a list.
        
        Arrange: Get activities
        Act: Check participants structure
        Assert: Verify participants is list of strings
        """
        # Arrange & Act
        response = client.get("/activities")
        data = response.json()
        
        # Assert
        for activity_name, activity_data in data.items():
            assert isinstance(activity_data["participants"], list)
            for participant in activity_data["participants"]:
                assert isinstance(participant, str)
                assert "@" in participant  # Basic email format check


# ============================================================================
# POST /signup Tests - Happy Path
# ============================================================================

class TestSignupHappyPath:
    """Tests for successful signup operations"""
    
    def test_signup_adds_participant(self, client, reset_activities):
        """
        Test that a new participant is successfully added to an activity.
        
        Arrange: Prepare email and activity name
        Act: Send POST signup request
        Assert: Verify 200 status, participant in activity, and response message
        """
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Chess Club"
        original_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Signed up {email} for {activity_name}"
        assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == original_count + 1
    
    def test_signup_multiple_participants(self, client, reset_activities):
        """
        Test that multiple different participants can sign up for same activity.
        
        Arrange: Prepare multiple emails
        Act: Sign up each participant sequentially
        Assert: Verify all participants added and counts correct
        """
        # Arrange
        emails = [
            "student1@mergington.edu",
            "student2@mergington.edu",
            "student3@mergington.edu"
        ]
        activity_name = "Programming Class"
        original_count = len(activities[activity_name]["participants"])
        
        # Act
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Assert
        for email in emails:
            assert email in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == original_count + 3
    
    def test_signup_does_not_affect_other_activities(self, client, reset_activities):
        """
        Test that signing up for one activity doesn't affect other activities.
        
        Arrange: Capture participant counts for all activities
        Act: Sign up for one activity
        Assert: Verify only that activity's count changed
        """
        # Arrange
        email = "student@mergington.edu"
        activity_name = "Art Studio"
        original_counts = {name: len(data["participants"]) for name, data in activities.items()}
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        for name, original_count in original_counts.items():
            if name == activity_name:
                assert len(activities[name]["participants"]) == original_count + 1
            else:
                assert len(activities[name]["participants"]) == original_count


# ============================================================================
# POST /signup Tests - Error Cases
# ============================================================================

class TestSignupErrors:
    """Tests for signup error handling"""
    
    def test_signup_activity_not_found(self, client, reset_activities):
        """
        Test 404 error when activity doesn't exist.
        
        Arrange: Prepare non-existent activity name
        Act: Send signup request
        Assert: Verify 404 status and error detail
        """
        # Arrange
        email = "student@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_duplicate_email(self, client, reset_activities):
        """
        Test 400 error when student already signed up.
        
        Arrange: Student already in activity participants
        Act: Try to signup same student again
        Assert: Verify 400 status and error detail
        """
        # Arrange
        activity_name = "Chess Club"
        existing_email = activities[activity_name]["participants"][0]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": existing_email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"
    
    def test_signup_duplicate_consecutive_attempts(self, client, reset_activities):
        """
        Test that duplicate signup attempts fail consistently.
        
        Arrange: Prepare email
        Act: Sign up once, then try again
        Assert: First succeeds (200), second fails (400)
        """
        # Arrange
        email = "newstudent@mergington.edu"
        activity_name = "Swimming Club"
        
        # Act - First signup
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Act - Second signup (duplicate)
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 400
        assert response2.json()["detail"] == "Student already signed up for this activity"


# ============================================================================
# POST /signup Tests - Edge Cases
# ============================================================================

class TestSignupEdgeCases:
    """Tests for signup edge cases and special scenarios"""
    
    def test_signup_with_url_encoded_activity_name(self, client, reset_activities):
        """
        Test signup with activity names containing special characters (URL encoding).
        
        Arrange: Prepare activity name that needs URL encoding
        Act: Sign up with URL-encoded activity name
        Assert: Verify signup succeeds
        """
        # Arrange
        email = "student@mergington.edu"
        activity_name = "Programming Class"  # Contains space, will be encoded
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email in activities[activity_name]["participants"]
    
    def test_signup_with_various_email_formats(self, client, reset_activities):
        """
        Test signup with different valid email format variations.
        
        Arrange: Prepare various email formats
        Act: Sign up with each email
        Assert: All signups succeed
        """
        # Arrange
        emails = [
            "simple@example.com",
            "user.name@example.co.uk",
            "user+tag@example.org"
        ]
        activity_name = "Drama Club"
        
        # Act & Assert
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
            assert email in activities[activity_name]["participants"]
    
    def test_signup_when_activity_at_capacity(self, client, reset_activities):
        """
        Test signup succeeds even when activity reaches max_participants.
        (Note: current implementation doesn't enforce capacity limit)
        
        Arrange: Fill activity to capacity
        Act: Add one more participant
        Assert: Participant is added (no capacity enforcement)
        """
        # Arrange
        activity_name = "Art Studio"
        max_participants = activities[activity_name]["max_participants"]
        current_participants = len(activities[activity_name]["participants"])
        
        # Add participants until at capacity
        for i in range(max_participants - current_participants):
            email = f"filler{i}@mergington.edu"
            activities[activity_name]["participants"].append(email)
        
        # Now try to add beyond capacity
        new_email = "beyond_capacity@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": new_email}
        )
        
        # Assert - signup succeeds (no capacity enforcement)
        assert response.status_code == 200
        assert new_email in activities[activity_name]["participants"]
    
    def test_signup_email_case_sensitivity(self, client, reset_activities):
        """
        Test that email comparison is case-sensitive (different cases = different emails).
        
        Arrange: Sign up with lowercase email
        Act: Try to sign up with uppercase version
        Assert: Signup succeeds (treated as different email due to case difference)
        """
        # Arrange
        activity_name = "Debate Team"
        email_lower = "student@mergington.edu"
        email_upper = "STUDENT@MERGINGTON.EDU"
        
        # Act - Sign up with lowercase
        response1 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_lower}
        )
        
        # Act - Try to sign up with uppercase
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email_upper}
        )
        
        # Assert - Both succeed (case-sensitive, treated as different)
        assert response1.status_code == 200
        assert response2.status_code == 200  # Different case = different email
        assert email_lower in activities[activity_name]["participants"]
        assert email_upper in activities[activity_name]["participants"]


# ============================================================================
# POST /unregister Tests - Happy Path
# ============================================================================

class TestUnregisterHappyPath:
    """Tests for successful unregister operations"""
    
    def test_unregister_removes_participant(self, client, reset_activities):
        """
        Test that unregister successfully removes a participant.
        
        Arrange: Get existing participant from activity
        Act: Send POST unregister request
        Assert: Verify 200 status, participant removed, and response message
        """
        # Arrange
        activity_name = "Chess Club"
        email = activities[activity_name]["participants"][0]
        original_count = len(activities[activity_name]["participants"])
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert response.json()["message"] == f"Unregistered {email} from {activity_name}"
        assert email not in activities[activity_name]["participants"]
        assert len(activities[activity_name]["participants"]) == original_count - 1
    
    def test_unregister_multiple_participants(self, client, reset_activities):
        """
        Test that multiple participants can be unregistered sequentially.
        
        Arrange: Prepare activity with participants
        Act: Unregister each participant
        Assert: Verify all removed and count decreases correctly
        """
        # Arrange
        activity_name = "Programming Class"
        participants_to_remove = activities[activity_name]["participants"].copy()
        original_count = len(activities[activity_name]["participants"])
        
        # Act
        for idx, email in enumerate(participants_to_remove):
            response = client.post(
                f"/activities/{activity_name}/unregister",
                params={"email": email}
            )
            assert response.status_code == 200
            # Assert after each removal
            assert email not in activities[activity_name]["participants"]
            assert len(activities[activity_name]["participants"]) == original_count - (idx + 1)
    
    def test_unregister_does_not_affect_other_activities(self, client, reset_activities):
        """
        Test that unregistering from one activity doesn't affect other activities.
        
        Arrange: Capture participant counts for all activities
        Act: Unregister from one activity
        Assert: Verify only that activity's count changed
        """
        # Arrange
        activity_name = "Swimming Club"
        email = activities[activity_name]["participants"][0]
        original_counts = {name: len(data["participants"]) for name, data in activities.items()}
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        for name, original_count in original_counts.items():
            if name == activity_name:
                assert len(activities[name]["participants"]) == original_count - 1
            else:
                assert len(activities[name]["participants"]) == original_count
    
    def test_unregister_and_reregister_same_student(self, client, reset_activities):
        """
        Test that a student can be unregistered and then re-registered.
        
        Arrange: Get participant from activity
        Act: Unregister, then sign up again
        Assert: Both operations succeed
        """
        # Arrange
        activity_name = "Art Studio"
        email = activities[activity_name]["participants"][0]
        
        # Act - Unregister
        response1 = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        assert response1.status_code == 200
        assert email not in activities[activity_name]["participants"]
        
        # Act - Re-register
        response2 = client.post(
            f"/activities/{activity_name}/signup",
            params={"email": email}
        )
        
        # Assert
        assert response2.status_code == 200
        assert email in activities[activity_name]["participants"]


# ============================================================================
# POST /unregister Tests - Error Cases
# ============================================================================

class TestUnregisterErrors:
    """Tests for unregister error handling"""
    
    def test_unregister_activity_not_found(self, client, reset_activities):
        """
        Test 404 error when activity doesn't exist.
        
        Arrange: Prepare non-existent activity name
        Act: Send unregister request
        Assert: Verify 404 status and error detail
        """
        # Arrange
        email = "student@mergington.edu"
        activity_name = "Nonexistent Activity"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_participant_not_found(self, client, reset_activities):
        """
        Test 400 error when participant not signed up for activity.
        
        Arrange: Prepare email not in participants list
        Act: Send unregister request
        Assert: Verify 400 status and error detail
        """
        # Arrange
        activity_name = "Gym Class"
        email = "notstudent@mergington.edu"
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 400
        assert response.json()["detail"] == "Student not signed up for this activity"
    
    def test_unregister_participant_twice(self, client, reset_activities):
        """
        Test that unregistering same participant twice fails on second attempt.
        
        Arrange: Get participant
        Act: Unregister once, then try again
        Assert: First succeeds (200), second fails (400)
        """
        # Arrange
        activity_name = "Basketball Team"
        email = activities[activity_name]["participants"][0]
        
        # Act - First unregister
        response1 = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Act - Second unregister (duplicate)
        response2 = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response1.status_code == 200
        assert response2.status_code == 400
        assert response2.json()["detail"] == "Student not signed up for this activity"


# ============================================================================
# POST /unregister Tests - Edge Cases
# ============================================================================

class TestUnregisterEdgeCases:
    """Tests for unregister edge cases and special scenarios"""
    
    def test_unregister_with_url_encoded_activity_name(self, client, reset_activities):
        """
        Test unregister with activity names containing special characters.
        
        Arrange: Prepare activity with spaces in name
        Act: Unregister from activity
        Assert: Verify unregister succeeds
        """
        # Arrange
        activity_name = "Programming Class"
        email = activities[activity_name]["participants"][0]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": email}
        )
        
        # Assert
        assert response.status_code == 200
        assert email not in activities[activity_name]["participants"]
    
    def test_unregister_with_various_email_formats(self, client, reset_activities):
        """
        Test unregister with different email format variations.
        
        Arrange: Add custom email formats, then unregister
        Act: Sign up and unregister with special email formats
        Assert: All operations succeed
        """
        # Arrange
        emails = [
            "user.name@example.com",
            "user+tag@example.org"
        ]
        activity_name = "Debate Team"
        
        # First sign them up
        for email in emails:
            client.post(
                f"/activities/{activity_name}/signup",
                params={"email": email}
            )
        
        # Act - Unregister
        for email in emails:
            response = client.post(
                f"/activities/{activity_name}/unregister",
                params={"email": email}
            )
            
            # Assert
            assert response.status_code == 200
            assert email not in activities[activity_name]["participants"]
    
    def test_unregister_last_participant(self, client, reset_activities):
        """
        Test unregistering the last participant from an activity.
        
        Arrange: Remove all but one participant
        Act: Unregister the last participant
        Assert: Participant list becomes empty
        """
        # Arrange
        activity_name = "Science Lab"
        # Remove all but one
        participants = activities[activity_name]["participants"].copy()
        while len(activities[activity_name]["participants"]) > 1:
            email = activities[activity_name]["participants"][0]
            client.post(
                f"/activities/{activity_name}/unregister",
                params={"email": email}
            )
        
        last_email = activities[activity_name]["participants"][0]
        
        # Act
        response = client.post(
            f"/activities/{activity_name}/unregister",
            params={"email": last_email}
        )
        
        # Assert
        assert response.status_code == 200
        assert len(activities[activity_name]["participants"]) == 0
        assert last_email not in activities[activity_name]["participants"]
