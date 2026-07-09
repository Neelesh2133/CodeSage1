import pytest
from app.github_client import parse_pr_url

def test_parse_pr_url_trailing_slash():
    owner, repo, pr_num = parse_pr_url("https://github.com/owner/repo/pull/123/")
    assert owner == "owner"
    assert repo == "repo"
    assert pr_num == 123

def test_parse_pr_url_git_suffix():
    owner, repo, pr_num = parse_pr_url("https://github.com/owner/repo.git/pull/123")
    assert owner == "owner"
    assert repo == "repo"
    assert pr_num == 123

def test_parse_pr_url_non_pr_url():
    with pytest.raises(ValueError) as excinfo:
        parse_pr_url("https://github.com/owner/repo/tree/main")
    assert "Invalid GitHub PR URL" in str(excinfo.value)

def test_parse_pr_url_completely_invalid():
    with pytest.raises(ValueError) as excinfo:
        parse_pr_url("completely-invalid-string")
    assert "Invalid GitHub PR URL" in str(excinfo.value)
