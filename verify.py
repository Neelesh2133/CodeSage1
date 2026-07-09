from fastapi.testclient import TestClient
from app.main import app
from unittest.mock import patch, MagicMock
from openai import AuthenticationError

client = TestClient(app)

# 1. Sign up and Login to get token
print('--- Step 1: Signing up and Logging in ---')
email = 'testuser_verify_unique2@example.com'
signup_res = client.post('/auth/signup', json={'email': email, 'password': 'password123'})
print(f'Signup status: {signup_res.status_code}')

login_res = client.post('/auth/login', data={'username': email, 'password': 'password123'})
print(f'Login status: {login_res.status_code}')

token = login_res.json().get('access_token')
if not token:
    print("Could not obtain token!")
    exit(1)
headers = {'Authorization': f'Bearer {token}'}
print('Success!')

# 2. Test Invalid PR URL (should return 400)
print('\n--- Step 2: Testing Invalid PR URL ---')
res = client.post('/reviews/pr', headers=headers, json={'pr_url': 'https://github.com/invalid'})
print(f'Status Code: {res.status_code}')
print(f'Response Detail: {res.json()["detail"]}')

# 3. Test Garbage API Key (should return 502)
print('\n--- Step 3: Testing Garbage API Key ---')
mock_request = MagicMock()
mock_http_response = MagicMock()
mock_http_response.status_code = 401
mock_http_response.headers = {}
err = AuthenticationError('Invalid API key', response=mock_http_response, body=None)
with patch('app.llm_client.client.chat.completions.create', side_effect=err):
    res = client.post('/reviews/', headers=headers, json={'code': 'def test(): pass'})
    print(f'Status Code: {res.status_code}')
    print(f'Response Detail: {res.json()["detail"]}')

# 4. Test 20+ files PR (should return chunked warning)
print('\n--- Step 4: Testing 20+ Files PR Chunking ---')
mock_files = [{'filename': f'file_{i}.py', 'patch': 'print("hello")\n' * 150} for i in range(25)]
mock_findings = [{'file_path': 'file_0.py', 'line_number': 1, 'severity': 'info', 'category': 'style', 'message': 'Looks good', 'suggestion': None}]

with patch('app.routers.reviews.fetch_pr_files', return_value=mock_files), patch('app.review_service.review_code', return_value=mock_findings):
    res = client.post('/reviews/pr', headers=headers, json={'pr_url': 'https://github.com/owner/repo/pull/123'})
    print(f'Status Code: {res.status_code}')
    print(f'Warnings: {res.json().get("warnings")}')
