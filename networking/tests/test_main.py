from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_check():
    """Verify that the health check endpoint returns 200 OK and status ok"""
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_home_page():
    """Verify that the home page renders correctly and references ClothCRM"""
    response = client.get("/")
    assert response.status_code == 200
    assert "Cloth" in response.text
    assert "CRM" in response.text
