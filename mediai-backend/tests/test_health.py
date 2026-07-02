"""Tests for GET /health."""


def test_health_check_returns_200_and_running_status(client):
    response = client.get("/health")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "running"
    assert body["service"] == "medical-rag"
