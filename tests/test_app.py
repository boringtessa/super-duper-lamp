from copy import deepcopy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


client = TestClient(app)


def reset_activities():
    baseline = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"],
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"],
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"],
        },
    }

    activities.clear()
    activities.update(deepcopy(baseline))


@pytest.fixture(autouse=True)
def restore_activity_state():
    reset_activities()
    yield
    reset_activities()


def test_root_redirects_to_static_index():
    # Arrange
    expected_location = "/static/index.html"

    # Act
    response = client.get("/", follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_all_activity_metadata():
    # Arrange
    expected_activity_names = {"Chess Club", "Programming Class", "Gym Class"}

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    response_body = response.json()
    assert set(response_body) == expected_activity_names
    assert response_body["Chess Club"]["max_participants"] == 12
    assert response_body["Programming Class"]["schedule"] == (
        "Tuesdays and Thursdays, 3:30 PM - 4:30 PM"
    )


def test_signup_for_activity_adds_email_to_participants():
    # Arrange
    activity_name = "Chess Club"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {activity_name}"
    }
    assert email in activities[activity_name]["participants"]


def test_signup_for_unknown_activity_returns_404():
    # Arrange
    activity_name = "Unknown Activity"
    email = "student@mergington.edu"

    # Act
    response = client.post(f"/activities/{activity_name}/signup?email={email}")

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_participant_removes_from_activity():
    activity_name = "Chess Club"
    email = "michael@mergington.edu"

    initial_response = client.get("/activities")
    assert initial_response.status_code == 200
    assert email in initial_response.json()[activity_name]["participants"]

    response = client.delete(
        f"/activities/{quote(activity_name)}/participants/{quote(email)}"
    )

    assert response.status_code == 200
    assert response.json()["message"] == f"Removed {email} from {activity_name}"

    updated_response = client.get("/activities")
    assert updated_response.status_code == 200
    assert email not in updated_response.json()[activity_name]["participants"]
