from unittest.mock import patch, MagicMock
import pytest

#Testing signup
def test_signup(client):
    response = client.post(
        "/auth/signup",
        json={"email": "testuser@example.com", "password": "securepassword"}
    )
    assert response.status_code == 200
    data = response.json()
    assert data["email"] == "testuser@example.com"
    assert "id" in data

def test_login_wrong_password(client):
    # Register the user first
    signup_res = client.post(
        "/auth/signup",
        json={"email": "testuser@example.com", "password": "securepassword"}
    )
    assert signup_res.status_code == 200

    # Try logging in with the wrong password
    response = client.post(
        "/auth/login",
        data={"username": "testuser@example.com", "password": "wrongpassword"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Incorrect email or password"

def test_create_review_without_token(client):
    response = client.post(
        "/reviews/",
        json={"code": "print('hello')"}
    )
    assert response.status_code == 401
    assert response.json()["detail"] == "Not authenticated"

def test_llm_malformed_json_retry_and_502(client):
    # Register and login to get a valid token
    signup_res = client.post(
        "/auth/signup",
        json={"email": "testuser@example.com", "password": "securepassword"}
    )
    assert signup_res.status_code == 200

    login_res = client.post(
        "/auth/login",
        data={"username": "testuser@example.com", "password": "securepassword"}
    )
    assert login_res.status_code == 200
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Set up mock response that returns malformed JSON
    mock_response = MagicMock()
    mock_response.choices = [MagicMock()]
    mock_response.choices[0].message.content = "This is not valid JSON string."

    with patch("app.llm_client.client.chat.completions.create", return_value=mock_response) as mock_create:
        response = client.post(
            "/reviews/",
            headers=headers,
            json={"code": "def process(): pass"}
        )
        
        # Check that it returned a 502 Bad Gateway
        assert response.status_code == 502
        data = response.json()
        assert data["detail"]["error"] == "LLM returned malformed JSON"
        assert data["detail"]["raw_response"] == "This is not valid JSON string."
        
        # Check that it tried once and retried once (total of 2 calls)
        assert mock_create.call_count == 2


def get_auth_headers(client, email, password="securepassword"):
    client.post("/auth/signup", json={"email": email, "password": password})
    login_res = client.post("/auth/login", data={"username": email, "password": password})
    return {"Authorization": f"Bearer {login_res.json()['access_token']}"}


def test_pr_review_invalid_url(client):
    headers = get_auth_headers(client, "testuser_pr1@example.com")
    response = client.post(
        "/reviews/pr",
        headers=headers,
        json={"pr_url": "https://github.com/invalid"}
    )
    assert response.status_code == 400
    assert "Invalid GitHub PR URL" in response.json()["detail"]


def test_pr_review_private_repo(client):
    headers = get_auth_headers(client, "testuser_pr2@example.com")
    
    # Mock fetch_pr_files to raise ValueError with "not found"
    with patch("app.routers.reviews.fetch_pr_files", side_effect=ValueError("PR not found: owner/repo#12")):
        response = client.post(
            "/reviews/pr",
            headers=headers,
            json={"pr_url": "https://github.com/owner/private-repo/pull/12"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()

    # Mock fetch_pr_files to raise ValueError with "rate limit exceeded"
    with patch("app.routers.reviews.fetch_pr_files", side_effect=ValueError("GitHub API rate limit exceeded.")):
        response = client.post(
            "/reviews/pr",
            headers=headers,
            json={"pr_url": "https://github.com/owner/private-repo/pull/12"}
        )
        assert response.status_code == 400
        assert "rate limit" in response.json()["detail"].lower()


def test_pr_review_binary_files(client):
    headers = get_auth_headers(client, "testuser_pr3@example.com")
    
    mock_files = [
        {"filename": "logo.png", "patch": None},  # binary
        {"filename": "app.py", "patch": "@@ -1 +1 @@\n-print('hello')\n+print('world')"}
    ]
    
    mock_findings = [
        {
            "file_path": "app.py",
            "line_number": 1,
            "severity": "info",
            "category": "style",
            "message": "Looks good",
            "suggestion": None
        }
    ]
    
    with patch("app.routers.reviews.fetch_pr_files", return_value=mock_files), \
         patch("app.review_service.review_code", return_value=mock_findings) as mock_review:
        response = client.post(
            "/reviews/pr",
            headers=headers,
            json={"pr_url": "https://github.com/owner/repo/pull/123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "findings" in data
        assert len(data["findings"]) == 1
        assert data["findings"][0]["file_path"] == "app.py"
        
        # Verify binary file logo.png was NOT included in LLM prompt
        mock_review.assert_called_once()
        called_prompt = mock_review.call_args[0][0]
        assert "logo.png" not in called_prompt
        assert "app.py" in called_prompt


def test_pr_review_success(client):
    headers = get_auth_headers(client, "testuser_pr4@example.com")
    
    mock_files = [
        {"filename": "main.py", "patch": "@@ -1,5 +1,6 @@\n-def add(a, b):\n-    return a + b\n+def add(a: int, b: int) -> int:\n+    return a + b"}
    ]
    
    mock_findings = [
        {
            "file_path": "main.py",
            "line_number": 1,
            "severity": "info",
            "category": "style",
            "message": "Good type hints",
            "suggestion": None
        }
    ]
    
    with patch("app.routers.reviews.fetch_pr_files", return_value=mock_files), \
         patch("app.review_service.review_code", return_value=mock_findings):
        response = client.post(
            "/reviews/pr",
            headers=headers,
            json={"pr_url": "https://github.com/owner/repo/pull/123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["findings"][0]["file_path"] == "main.py"
        assert data["findings"][0]["line_number"] == 1


def test_pr_review_chunked_20_plus_files(client):
    headers = get_auth_headers(client, "testuser_chunked@example.com")
    
    # Generate 25 files, each with enough content to cause chunking
    # Total character size: 25 * 2000 = 50,000 characters (> 32,000 MAX_CHUNK_CHARS)
    mock_files = [
        {"filename": f"file_{i}.py", "patch": "@@ -1 +1 @@\n" + "print('hello')\n" * 150}
        for i in range(25)
    ]
    
    mock_findings = [
        {
            "file_path": "file_0.py",
            "line_number": 1,
            "severity": "info",
            "category": "style",
            "message": "Looks good",
            "suggestion": None
        }
    ]
    
    with patch("app.routers.reviews.fetch_pr_files", return_value=mock_files), \
         patch("app.review_service.review_code", return_value=mock_findings) as mock_review:
        response = client.post(
            "/reviews/pr",
            headers=headers,
            json={"pr_url": "https://github.com/owner/repo/pull/123"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "findings" in data
        assert "warnings" in data
        warnings_str = " ".join(data["warnings"])
        assert "split" in warnings_str or "chunk" in warnings_str
        assert mock_review.call_count > 1


from openai import AuthenticationError

def test_review_openrouter_garbage_key_returns_502(client):
    headers = get_auth_headers(client, "testuser_garbage_key@example.com")
    
    mock_request = MagicMock()
    mock_http_response = MagicMock()
    mock_http_response.status_code = 401
    mock_http_response.headers = {}
    err = AuthenticationError("Invalid API key", response=mock_http_response, body=None)
    
    with patch("app.llm_client.client.chat.completions.create", side_effect=err):
        response = client.post(
            "/reviews/",
            headers=headers,
            json={"code": "def test(): pass"}
        )
        assert response.status_code == 502
        assert "LLM review failed" in response.json()["detail"]

