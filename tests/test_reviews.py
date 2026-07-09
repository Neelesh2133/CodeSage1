from unittest.mock import patch

def _authed_headers(client, email="a@test.com"):
    client.post("/auth/signup", json={"email": email, "password": "test1234"})
    token = client.post("/auth/login", data={"username": email, "password": "test1234"}).json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@patch("app.review_service.review_code")
def test_create_review_returns_findings(mock_review, client):
    mock_review.return_value = [{
        "file_path": None, "line_number": 3, "severity": "high",
        "category": "security", "message": "SQL injection risk", "suggestion": "Use parameterized queries"
    }]
    headers = _authed_headers(client)
    resp = client.post("/reviews/", json={"code": "query = 'SELECT * FROM users WHERE id=' + id"}, headers=headers)
    assert resp.status_code == 200
    assert resp.json()["findings"][0]["category"] == "security"

@patch("app.review_service.review_code")
def test_llm_failure_returns_502(mock_review, client):
    mock_review.side_effect = ValueError("LLM did not return valid JSON")
    headers = _authed_headers(client)
    resp = client.post("/reviews/", json={"code": "print(1)"}, headers=headers)
    assert resp.status_code == 502

@patch("app.review_service.review_code")
def test_history_filters_by_severity(mock_review, client):
    mock_review.return_value = [
        {"file_path": None, "line_number": None, "severity": "critical", "category": "bug", "message": "x", "suggestion": None},
        {"file_path": None, "line_number": None, "severity": "low", "category": "style", "message": "y", "suggestion": None},
    ]
    headers = _authed_headers(client)
    client.post("/reviews/", json={"code": "..."}, headers=headers)
    resp = client.get("/reviews/?severity=critical", headers=headers)
    findings = resp.json()[0]["findings"]
    assert all(f["severity"] == "critical" for f in findings)