from fastapi.testclient import TestClient
from app.main import app
import uuid

client = TestClient(app)

def test_signup():
    # Use a unique email to avoid conflicts if the DB persists between runs
    test_email = f"pytest_{uuid.uuid4()}@test.com"
    response = client.post("/auth/signup", json={"email": test_email, "password": "test1234"})
    assert response.status_code in [200, 201]

def test_login_wrong_password():
    # Attempt login with incorrect credentials
    response = client.post("/auth/login", data={"username": "pytest_wrong@test.com", "password": "wrongpassword"})
    assert response.status_code == 401

def test_create_review_without_token():
    # Try to access a protected endpoint without auth
    response = client.post("/reviews/", json={"code": "def hello(): pass"})
    assert response.status_code == 401
