import httpx
import sys

BASE_URL = "http://localhost:8000"

def test_flow():
    client = httpx.Client()
    
    # 1. Signup
    print("1. Registering user 'you@test.com'...")
    try:
        signup_res = client.post(
            f"{BASE_URL}/auth/signup",
            json={"email": "you@test.com", "password": "test1234"}
        )
        print(f"   Status Code: {signup_res.status_code}")
        print(f"   Response: {signup_res.text}\n")
    except Exception as e:
        print(f"   Signup request failed: {e}\n")

    # 2. Login
    print("2. Logging in to get access token...")
    try:
        login_res = client.post(
            f"{BASE_URL}/auth/login",
            data={"username": "you@test.com", "password": "test1234"}
        )
        print(f"   Status Code: {login_res.status_code}")
        print(f"   Response: {login_res.text}\n")
        
        if login_res.status_code != 200:
            print("Login failed, stopping flow.")
            return
            
        token = login_res.json()["access_token"]
    except Exception as e:
        print(f"   Login request failed: {e}")
        return

    # 3. Create Review
    print("3. Creating a code review with authorization token...")
    code_to_review = "def get_user(id):\n    query = \"SELECT * FROM users WHERE id = \" + id"
    headers = {"Authorization": f"Bearer {token}"}
    
    try:
        review_res = client.post(
            f"{BASE_URL}/reviews/",
            headers=headers,
            json={"code": code_to_review},
            timeout=60.0
        )
        print(f"   Status Code: {review_res.status_code}")
        print(f"   Response: {review_res.text}\n")
    except Exception as e:
        print(f"   Create review request failed: {e}\n")

    # 4. List Reviews
    print("4. Listing reviews for the current user...")
    try:
        list_res = client.get(f"{BASE_URL}/reviews/", headers=headers)
        print(f"   Status Code: {list_res.status_code}")
        print(f"   Response: {list_res.text}\n")
    except Exception as e:
        print(f"   List reviews request failed: {e}\n")

if __name__ == "__main__":
    test_flow()
