import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app

client = TestClient(app)

@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_activities))


def test_get_activities_returns_all_activities():
    # Arrange
    expected_activity_names = set(activities.keys())

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    result = response.json()
    assert set(result.keys()) == expected_activity_names

    for name, details in activities.items():
        assert result[name]["description"] == details["description"]
        assert result[name]["schedule"] == details["schedule"]
        assert result[name]["max_participants"] == details["max_participants"]
        assert result[name]["participants"] == details["participants"]


def test_signup_adds_new_participant():
    # Arrange
    activity_name = "Chess Club"
    new_email = "newstudent@mergington.edu"
    assert new_email not in activities[activity_name]["participants"]
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{encoded_activity}/signup",
        params={"email": new_email},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Signed up {new_email} for {activity_name}"
    assert new_email in activities[activity_name]["participants"]


def test_signup_duplicate_returns_bad_request():
    # Arrange
    activity_name = "Chess Club"
    existing_email = activities[activity_name]["participants"][0]
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.post(
        f"/activities/{encoded_activity}/signup",
        params={"email": existing_email},
    )

    # Assert
    assert response.status_code == 400
    assert response.json()["detail"] == "Student already signed up for this activity"


def test_delete_participant_unregisters_participant():
    # Arrange
    activity_name = "Chess Club"
    email_to_remove = activities[activity_name]["participants"][0]
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{encoded_activity}/participants",
        params={"email": email_to_remove},
    )

    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email_to_remove} from {activity_name}"
    assert email_to_remove not in activities[activity_name]["participants"]


def test_delete_missing_participant_returns_not_found():
    # Arrange
    activity_name = "Chess Club"
    missing_email = "missing@mergington.edu"
    encoded_activity = quote(activity_name, safe="")

    # Act
    response = client.delete(
        f"/activities/{encoded_activity}/participants",
        params={"email": missing_email},
    )

    # Assert
    assert response.status_code == 404
    assert response.json()["detail"] == "Participant not found for this activity"
