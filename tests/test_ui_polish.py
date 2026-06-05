from fastapi.testclient import TestClient
from app.main import app


def get_auth_client():
    """Helper to return an authenticated TestClient instance"""
    client = TestClient(app)
    client.post(
        "/login",
        data={"email": "admin@clothcrm.local", "password": "Admin123!"},
        follow_redirects=True
    )
    return client


def test_login_page_ui_polish():
    """Verify that the login page contains the inline SVG favicon and stylesheet link"""
    client = TestClient(app)
    response = client.get("/login")
    assert response.status_code == 200
    
    # Check for custom crm.css link
    assert "/static/css/crm.css" in response.text
    # Check for inline SVG favicon
    assert "data:image/svg+xml" in response.text
    assert "👕" in response.text


def test_base_layout_ui_polish():
    """Verify that the main authenticated template contains favicon, sidebar overlay and responsiveness toggler"""
    client = get_auth_client()
    response = client.get("/")
    assert response.status_code == 200
    
    # Check inline SVG favicon
    assert "data:image/svg+xml" in response.text
    assert "👕" in response.text
    
    # Check responsive sidebar overlay backdrop and toggler button
    assert "sidebar-overlay" in response.text
    assert "sidebarToggle" in response.text
    
    # Check for floating toast animation classes
    assert "toast-container" in response.text
