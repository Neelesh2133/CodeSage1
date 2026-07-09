def test_signup_creates_user(client):
    resp = client.post("/auth/signup", json={"email": "a@test.com", "password": "test1234"})
    assert resp.status_code == 200
    assert resp.json()["email"] == "a@test.com"

def test_signup_rejects_duplicate_email(client):
    client.post("/auth/signup", json={"email": "a@test.com", "password": "test1234"})
    resp = client.post("/auth/signup", json={"email": "a@test.com", "password": "different"})
    assert resp.status_code == 400

def test_login_succeeds_with_correct_password(client):
    client.post("/auth/signup", json={"email": "a@test.com", "password": "test1234"})
    resp = client.post("/auth/login", data={"username": "a@test.com", "password": "test1234"})
    assert resp.status_code == 200
    assert "access_token" in resp.json()

def test_login_fails_with_wrong_password(client):
    client.post("/auth/signup", json={"email": "a@test.com", "password": "test1234"})
    resp = client.post("/auth/login", data={"username": "a@test.com", "password": "wrong"})
    assert resp.status_code == 401

def test_reviews_endpoint_requires_auth(client):
    resp = client.post("/reviews/", json={"code": "print('hi')"})
    assert resp.status_code == 401