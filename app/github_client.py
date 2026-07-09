import re
import requests
from app.config import settings

GITHUB_API = "https://api.github.com"

def _headers() -> dict:
    headers = {"Accept": "application/vnd.github+json", "X-GitHub-Api-Version": "2022-11-28"}
    if settings.github_token:
        headers["Authorization"] = f"Bearer {settings.github_token}"
    return headers

def parse_pr_url(pr_url: str) -> tuple[str, str, int]:
    """Extracts (owner, repo, pr_number) from a GitHub PR URL."""
    match = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", pr_url)
    if not match:
        raise ValueError("Invalid GitHub PR URL. Expected format: https://github.com/owner/repo/pull/123")
    owner, repo, pr_number = match.groups()
    if repo.endswith(".git"):
        repo = repo[:-4]
    return owner, repo, int(pr_number)

def fetch_pr_files(owner: str, repo: str, pr_number: int) -> list[dict]:
    """Fetches changed files + patches for a PR. Handles pagination up to 300 files."""
    files = []
    page = 1
    while True:
        url = f"{GITHUB_API}/repos/{owner}/{repo}/pulls/{pr_number}/files"
        resp = requests.get(url, headers=_headers(), params={"per_page": 100, "page": page}, timeout=10)

        if resp.status_code == 404:
            raise ValueError(f"PR not found: {owner}/{repo}#{pr_number}")
        if resp.status_code == 403:
            if "secondary rate limit" in resp.text.lower():
                raise ValueError("GitHub secondary rate limit hit - wait a minute before retrying.")
            raise ValueError("GitHub API rate limit exceeded. Add a GITHUB_TOKEN to .env to increase limits.")
        resp.raise_for_status()

        batch = resp.json()
        if not batch:
            break
        files.extend(batch)
        if len(batch) < 100 or page >= 3:
            break
        page += 1

    return files