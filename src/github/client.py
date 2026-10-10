"""
GitHub REST API v3 Integration Client.
Handles PR diff fetching and inline review comment dispatch, with dry-run/mock mode support.
"""

import os
import json
import logging
from typing import Optional, Dict, Any, List
from ..schemas.models import PRReviewResult, ReviewComment
from ..config import settings

logger = logging.getLogger(__name__)

class GitHubReviewClient:
    """Dispatches PR review comments to GitHub REST API."""

    def __init__(self, token: Optional[str] = None):
        self.token = token or settings.GITHUB_TOKEN
        self.base_url = "https://api.github.com"

    def fetch_pr_diff(self, owner: str, repo: str, pull_number: int) -> str:
        """
        Fetches the unified git diff for a Pull Request from GitHub API.
        Public repositories do not require a GITHUB_TOKEN.
        """
        import urllib.request
        import urllib.error

        headers = {
            "Accept": "application/vnd.github.v3.diff",
            "User-Agent": "Autonomous-PR-Reviewer-Agent"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}"
        req = urllib.request.Request(url, headers=headers)

        try:
            with urllib.request.urlopen(req, timeout=12) as resp:
                return resp.read().decode("utf-8")
        except urllib.error.HTTPError as err:
            if err.code == 404:
                raise ValueError(f"Pull Request #{pull_number} not found in {owner}/{repo}.")
            elif err.code == 403:
                raise ValueError(f"GitHub API rate limit exceeded or private repo. Provide a GitHub Token in settings.")
            raise ValueError(f"GitHub API error {err.code}: {err.reason}")
        except urllib.error.URLError as err:
            raise ConnectionError(f"Failed to reach GitHub API: {err.reason}")

    def get_pr_details(self, owner: str, repo: str, pull_number: int) -> Dict[str, Any]:
        """Fetches metadata (title, author, url) for a Pull Request."""
        import urllib.request
        import urllib.error

        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Autonomous-PR-Reviewer-Agent"
        }
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"

        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}"
        req = urllib.request.Request(url, headers=headers)
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "title": data.get("title", f"PR #{pull_number}"),
                    "author": data.get("user", {}).get("login", "unknown"),
                    "state": data.get("state", "open"),
                    "html_url": data.get("html_url", f"https://github.com/{owner}/{repo}/pull/{pull_number}"),
                    "additions": data.get("additions", 0),
                    "deletions": data.get("deletions", 0),
                    "changed_files": data.get("changed_files", 0),
                }
        except Exception:
            return {
                "title": f"PR #{pull_number}",
                "html_url": f"https://github.com/{owner}/{repo}/pull/{pull_number}",
            }

    def post_pr_review(
        self,
        owner: str,
        repo: str,
        pull_number: int,
        review_result: PRReviewResult,
        commit_id: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Submits an aggregated Pull Request Review containing inline line comments.
        """
        # Map review status to GitHub review event
        event_map = {
            "APPROVE": "APPROVE",
            "REQUEST_CHANGES": "REQUEST_CHANGES",
            "COMMENT": "COMMENT"
        }
        event = event_map.get(review_result.overall_status, "COMMENT")

        formatted_inline_comments: List[Dict[str, Any]] = []
        for c in review_result.comments:
            body = (
                f"### **[{c.severity}] {c.category} Finding**\n\n"
                f"**Issue:** {c.issue_summary}\n\n"
                f"{c.detailed_explanation}\n\n"
                f"**Suggested Remediation:**\n"
                f"```suggestion\n{c.suggested_diff_fix}\n```"
            )
            formatted_inline_comments.append({
                "path": c.file_path,
                "line": c.line_number,
                "body": body,
            })

        payload = {
            "body": review_result.summary_markdown,
            "event": event,
            "comments": formatted_inline_comments
        }
        if commit_id:
            payload["commit_id"] = commit_id

        if dry_run or not self.token or settings.MOCK_MODE:
            logger.info("Dispatched review in DRY_RUN / MOCK mode successfully.")
            return {
                "status": "simulated",
                "dry_run": True,
                "event": event,
                "comments_count": len(formatted_inline_comments),
                "payload": payload
            }

        import urllib.request
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/reviews"
        req = urllib.request.Request(
            url,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.token}",
                "Accept": "application/vnd.github.v3+json",
                "Content-Type": "application/json",
                "User-Agent": "Autonomous-PR-Reviewer-Agent"
            },
            method="POST"
        )

        with urllib.request.urlopen(req) as resp:
            return json.loads(resp.read().decode("utf-8"))
