import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture(autouse=True)
def restore_participants():
    original_participants = {
        name: details["participants"][:]
        for name, details in activities.items()
    }
    yield
    for name, participants in original_participants.items():
        activities[name]["participants"][:] = participants


@pytest.fixture
def client():
    with TestClient(app) as test_client:
        yield test_client


def test_get_activities_returns_data_without_cache(client):
    response = client.get("/activities")

    assert response.status_code == 200
    assert "Chess Club" in response.json()
    assert response.headers["cache-control"] == "no-store"


def test_signup_adds_participant(client):
    email = "test-student@mergington.edu"

    response = client.post(
        "/activities/Basketball%20Team/signup",
        params={"email": email},
    )

    assert response.status_code == 200
    assert email in activities["Basketball Team"]["participants"]
    assert response.json() == {"message": f"Signed up {email} for Basketball Team"}


def test_signup_returns_not_found_for_unknown_activity(client):
    response = client.post(
        "/activities/Unknown%20Activity/signup",
        params={"email": "test-student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_signup_rejects_duplicate_participant(client):
    email = "test-student@mergington.edu"
    url = "/activities/Basketball%20Team/signup"

    first_response = client.post(url, params={"email": email})
    duplicate_response = client.post(url, params={"email": email})

    assert first_response.status_code == 200
    assert duplicate_response.status_code == 400
    assert duplicate_response.json()["detail"] == "Student already signed up for this activity"
    assert activities["Basketball Team"]["participants"].count(email) == 1


def test_unregister_removes_participant(client):
    email = "test-student@mergington.edu"
    client.post(
        "/activities/Basketball%20Team/signup",
        params={"email": email},
    )

    response = client.delete(
        "/activities/Basketball%20Team/participants",
        params={"email": email},
    )

    assert response.status_code == 200
    assert email not in activities["Basketball Team"]["participants"]
    assert response.json() == {
        "message": f"Unregistered {email} from Basketball Team"
    }


def test_unregister_returns_not_found_for_unknown_activity(client):
    response = client.delete(
        "/activities/Unknown%20Activity/participants",
        params={"email": "test-student@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_returns_not_found_for_unsigned_participant(client):
    response = client.delete(
        "/activities/Basketball%20Team/participants",
        params={"email": "not-signed-up@mergington.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"
