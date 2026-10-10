"""GitHub integration endpoints and handlers."""

import re
from typing import Any, Dict, Optional
from ...github.client import GitHubReviewClient

def handle_github_fetch(data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Pure functional handler fetching unified diff and metadata from GitHub."""
    headers = headers or {}
    repo_input = (data.get("repo") or data.get("pr_url") or data.get("url") or "").strip()
    pull_number = int(data.get("pull_number", 0) or 0)
    token = data.get("github_token") or headers.get("x-github-token") or None

    # Support parsing full GitHub PR URL: https://github.com/owner/repo/pull/123
    if "github.com/" in repo_input:
        m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", repo_input)
        if m:
            owner = m.group(1)
            repo = m.group(2)
            pull_number = int(m.group(3))
        else:
            raise ValueError("Invalid GitHub Pull Request URL. Expected format: https://github.com/owner/repo/pull/123")
    elif "/" in repo_input:
        parts = repo_input.split("/")
        owner = parts[0].strip()
        repo = parts[1].strip()
    else:
        raise ValueError("Repository must be specified as 'owner/repo' or a direct GitHub PR URL.")

    if not pull_number:
        raise ValueError("Pull Request number must be provided.")

    client = GitHubReviewClient(token=token)
    diff = client.fetch_pr_diff(owner=owner, repo=repo, pull_number=pull_number)
    details = client.get_pr_details(owner=owner, repo=repo, pull_number=pull_number)

    return {
        "success": True,
        "diff_text": diff,
        "owner": owner,
        "repo": repo,
        "pull_number": pull_number,
        "title": details.get("title", f"PR #{pull_number}"),
        "html_url": details.get("html_url", f"https://github.com/{owner}/{repo}/pull/{pull_number}"),
        "author": details.get("author", "unknown"),
        "lines_count": len(diff.splitlines()) if diff else 0,
    }


def handle_github_publish(data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Pure functional handler publishing audit review comments to GitHub."""
    headers = headers or {}
    owner = data.get("owner", "demo")
    repo = data.get("repo", "repo")
    pull_number = int(data.get("pull_number", 1))
    token = data.get("github_token") or headers.get("x-github-token") or None
    commit_id = data.get("commit_id")
    dry_run = bool(data.get("dry_run", not bool(token)))
    review_data = data.get("review_result", {})

    client = GitHubReviewClient(token=token)
    resp = client.post_pr_review(
        owner=owner,
        repo=repo,
        pull_number=pull_number,
        review_result=review_data,
        commit_id=commit_id,
        dry_run=dry_run
    )
    return {
        "success": True,
        "response": resp,
        "dry_run": dry_run
    }


try:
    from fastapi import APIRouter, Request, HTTPException
    from pydantic import BaseModel

    router = APIRouter(prefix="/api/v1/github", tags=["GitHub"])

    class GitHubFetchPayload(BaseModel):
        repo: Optional[str] = ""
        pull_number: Optional[int] = 0
        pr_url: Optional[str] = None
        url: Optional[str] = None
        github_token: Optional[str] = None

    class GitHubPublishPayload(BaseModel):
        owner: str = "demo"
        repo: str = "repo"
        pull_number: int = 1
        review_result: Dict[str, Any]
        github_token: Optional[str] = None
        commit_id: Optional[str] = None
        dry_run: Optional[bool] = False

    @router.post("/fetch")
    def fetch_pr(payload: GitHubFetchPayload, request: Request):
        try:
            return handle_github_fetch(payload.model_dump(), dict(request.headers))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

    @router.post("/publish")
    def publish_review(payload: GitHubPublishPayload, request: Request):
        try:
            return handle_github_publish(payload.model_dump(), dict(request.headers))
        except Exception as e:
            raise HTTPException(status_code=400, detail=str(e))

except ImportError:
    router = None
