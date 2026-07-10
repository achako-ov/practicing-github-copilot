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
    response = client.get("/", follow_redirects=False)

    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_activity_catalog(client):
    response = client.get("/activities")

    assert response.status_code == 200
    payload = response.json()
    assert "Chess Club" in payload
    assert payload["Chess Club"]["participants"] == [
        "michael@mergington.edu",
        "daniel@mergington.edu",
    ]


def test_signup_for_activity_adds_participant(client):
    response = client.post(
        f"/activities/{quote('Chess Club', safe='')}/signup",
        params={"email": "newstudent@mergington.edu"},
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Signed up newstudent@mergington.edu for Chess Club"
    }
    assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]


def test_duplicate_signup_is_rejected(client):
    response = client.post(
        f"/activities/{quote('Chess Club', safe='')}/signup",
        params={"email": "michael@mergington.edu"},
    )

    assert response.status_code == 400
    assert response.json() == {
        "detail": "Student is already signed up for this activity"
    }


def test_remove_participant_removes_student(client):
    response = client.delete(
        f"/activities/{quote('Chess Club', safe='')}/participants/michael@mergington.edu"
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": "Removed michael@mergington.edu from Chess Club"
    }
    assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]
