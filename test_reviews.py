import sys
import os
import argparse
import httpx
import json

# Ensure the root directory is in python path
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# Define the sample code snippets
SQL_INJECTION_CODE = """
def get_user_profile(user_id):
    query = "SELECT * FROM profiles WHERE id = " + user_id
    db.execute(query)
"""

BARE_EXCEPT_CODE = """
def load_config(path):
    try:
        with open(path) as f:
            return json.load(f)
    except:
        return {}
"""

CLEAN_CODE = """
import logging

logger = logging.getLogger(__name__)

def parse_port(port_str: str) -> int:
    try:
        port = int(port_str)
        if not (1 <= port <= 65535):
            raise ValueError(f"Port {port} out of range [1-65535]")
        return port
    except ValueError as e:
        logger.error("Invalid port: %s", e)
        raise
"""

SAMPLES = [
    ("SQL Injection", SQL_INJECTION_CODE),
    ("Bare Except", BARE_EXCEPT_CODE),
    ("Clean Code", CLEAN_CODE)
]

def print_findings(name, code, findings):
    print("=" * 60)
    print(f"Sample: {name}")
    print("-" * 60)
    print("Code Snippet:")
    print(code.strip())
    print("-" * 60)
    print(f"Findings ({len(findings)}):")
    if not findings:
        print("  No issues found. Code is clean!")
    for idx, finding in enumerate(findings, 1):
        print(f"  Finding #{idx}:")
        print(f"    Category:    {finding.get('category')}")
        print(f"    Severity:    {finding.get('severity')}")
        print(f"    Line Number: {finding.get('line_number')}")
        print(f"    Message:     {finding.get('message')}")
        print(f"    Suggestion:  {finding.get('suggestion')}")
        print()

def main():
    parser = argparse.ArgumentParser(description="Test POST /reviews/ endpoint")
    parser.add_argument("--url", type=str, help="Target URL of the running API (e.g. http://localhost:8000)")
    args = parser.parse_args()

    if args.url:
        target_url = args.url.rstrip("/") + "/reviews/"
        print(f"Testing against running server at: {target_url}\n")
        
        # Test connection to the live server health check first
        health_url = args.url.rstrip("/") + "/health"
        try:
            r = httpx.get(health_url)
            if r.status_code != 200:
                print(f"Warning: Health check returned status code {r.status_code}")
        except Exception as e:
            print(f"Error connecting to server at {health_url}: {e}")
            print("Please ensure the server is running.")
            sys.exit(1)

        for name, code in SAMPLES:
            try:
                response = httpx.post(target_url, json={"code": code}, timeout=60.0)
                if response.status_code == 200:
                    data = response.json()
                    print_findings(name, code, data.get("findings", []))
                else:
                    print(f"Failed to test {name}. HTTP Status: {response.status_code}, Response: {response.text}")
            except Exception as e:
                print(f"Error hitting endpoint for {name}: {e}")
    else:
        print("Testing in-process using FastAPI TestClient...\n")
        try:
            from fastapi.testclient import TestClient
            from app.main import app
            
            client = TestClient(app)
            for name, code in SAMPLES:
                response = client.post("/reviews/", json={"code": code})
                if response.status_code == 200:
                    data = response.json()
                    print_findings(name, code, data.get("findings", []))
                else:
                    print(f"Failed to test {name}. HTTP Status: {response.status_code}, Response: {response.text}")
        except Exception as e:
            print(f"Error testing in-process: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    main()
