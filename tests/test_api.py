import copy
from urllib.parse import quote

import pytest
from fastapi.testclient import TestClient

from src.app import app, activities


@pytest.fixture(autouse=True)
def reset_activities_state():
    original_state = copy.deepcopy(activities)
    activities.clear()
    activities.update(copy.deepcopy(original_state))
    yield
    activities.clear()
    activities.update(copy.deepcopy(original_state))


@pytest.fixture()
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_root_redirects_to_static_index(client):
    # Arrange
    url = "/"
    expected_location = "/static/index.html"

    # Act
    response = client.get(url, follow_redirects=False)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == expected_location


def test_get_activities_returns_activity_catalog(client):
    # Arrange
    url = "/activities"
    expected_activity = "Chess Club"
    expected_participants = [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]

    # Act
    response = client.get(url)

    # Assert
    assert response.status_code == 200
    payload = response.json()
    assert expected_activity in payload
    assert payload[expected_activity]["participants"] == expected_participants


def test_signup_for_activity_adds_participant(client):
    # Arrange
    activity_name = "Chess Club"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"
    signup_params = {"email": "newstudent@mergington.edu"}

    # Act
    response = client.post(signup_url, params=signup_params)

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {signup_params['email']} for {activity_name}"
    }
    assert signup_params["email"] in activities[activity_name]["participants"]


def test_duplicate_signup_is_rejected(client):
    # Arrange
    activity_name = "Chess Club"
    signup_url = f"/activities/{quote(activity_name, safe='')}/signup"
    signup_params = {"email": "michael@mergington.edu"}

    # Act
    response = client.post(signup_url, params=signup_params)

    # Assert
    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }


def test_remove_participant_removes_student(client):
    # Arrange
    activity_name = "Chess Club"
    participant_email = "michael@mergington.edu"
    delete_url = (
        f"/activities/{quote(activity_name, safe='')}/participants/{participant_email}"
    )

    # Act
    response = client.delete(delete_url)

    # Assert
    assert response.status_code == 200
    assert response.json() == {
        "message": f"Removed {participant_email} from {activity_name}"
    }
    assert participant_email not in activities[activity_name]["participants"]
