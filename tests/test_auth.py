from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_unauthenticated_redirect():
    """Verify that unauthenticated access to home page redirects to /login"""
    response = client.get("/", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_login_success():
    """Verify that logging in with valid credentials redirects to home and sets a cookie"""
    # Start a clean client to isolate cookies
    local_client = TestClient(app)
    response = local_client.post(
        "/login",
        data={"email": "admin@clothcrm.local", "password": "Admin123!"},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    assert "clothcrm_session" in local_client.cookies


def test_login_invalid_credentials():
    """Verify that invalid credentials redirect back to /login"""
    local_client = TestClient(app)
    response = local_client.post(
        "/login",
        data={"email": "admin@clothcrm.local", "password": "wrongpassword"},
        follow_redirects=False
    )
    assert response.status_code == 303
    assert response.headers["location"] == "/login"


def test_role_restrictions_admin():
    """Verify that an admin can access the users dashboard"""
    local_client = TestClient(app)
    # Login as admin
    login_response = local_client.post(
        "/login",
        data={"email": "admin@clothcrm.local", "password": "Admin123!"},
        follow_redirects=True
    )
    # Check access to /users
    response = local_client.get("/users", follow_redirects=False)
    assert response.status_code == 200
    assert "User Accounts" in response.text


def test_role_restrictions_sales():
    """Verify that a sales representative is blocked from accessing users dashboard"""
    local_client = TestClient(app)
    # Login as sales rep
    login_response = local_client.post(
        "/login",
        data={"email": "sales@clothcrm.local", "password": "Sales123!"},
        follow_redirects=True
    )
    # Check access to /users. It should raise RoleDeniedException, which redirects to /
    response = local_client.get("/users", follow_redirects=False)
    assert response.status_code == 303
    assert response.headers["location"] == "/"
