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
        self.token = token or settings.GITHUB_TOKEN or self._get_system_gh_token()
        self.base_url = "https://api.github.com"

    @staticmethod
    def _get_system_gh_token() -> Optional[str]:
        """Auto-detects GitHub token from the system gh CLI if authenticated."""
        import shutil
        import subprocess
        gh_bin = shutil.which("gh") or os.path.expanduser("~/.local/bin/gh")
        if os.path.exists(gh_bin) or shutil.which("gh"):
            try:
                res = subprocess.run([gh_bin, "auth", "token"], capture_output=True, text=True, timeout=3)
                if res.returncode == 0 and res.stdout.strip():
                    return res.stdout.strip()
            except Exception:
                pass
        return None

    @staticmethod
    def _urlopen_safe(req, timeout: int = 12):
        """Executes urllib request with macOS SSL fallback."""
        import urllib.request
        import urllib.error
        import ssl
        try:
            return urllib.request.urlopen(req, timeout=timeout)
        except urllib.error.URLError as err:
            err_str = str(err)
            if "CERTIFICATE_VERIFY_FAILED" in err_str or "certificate verify failed" in err_str:
                try:
                    unverified_ctx = ssl._create_unverified_context()
                    fresh_req = urllib.request.Request(
                        req.full_url,
                        data=req.data,
                        headers=dict(req.header_items()),
                        method=req.get_method()
                    )
                    return urllib.request.urlopen(fresh_req, timeout=timeout, context=unverified_ctx)
                except Exception:
                    pass
            raise err

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
            with self._urlopen_safe(req, timeout=12) as resp:
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
            with self._urlopen_safe(req, timeout=10) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                return {
                    "title": data.get("title", f"PR #{pull_number}"),
                    "author": data.get("user", {}).get("login", "unknown"),
                    "state": data.get("state", "open"),
                    "html_url": data.get("html_url", f"https://github.com/{owner}/{repo}/pull/{pull_number}"),
                    "additions": data.get("additions", 0),
                    "deletions": data.get("deletions", 0),
                    "changed_files": data.get("changed_files", 0),
                    "head_sha": data.get("head", {}).get("sha"),
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
        review_result: Any,
        commit_id: Optional[str] = None,
        dry_run: bool = False
    ) -> Dict[str, Any]:
        """
        Submits an aggregated Pull Request Review containing inline line comments.
        Tolerates both PRReviewResult objects and raw dictionaries.
        """
        event_map = {
            "APPROVE": "APPROVE",
            "REQUEST_CHANGES": "REQUEST_CHANGES",
            "COMMENT": "COMMENT"
        }
        status = getattr(review_result, "overall_status", None) or (
            review_result.get("overall_status") if isinstance(review_result, dict) else "COMMENT"
        )
        event = event_map.get(status, "COMMENT")

        raw_comments = getattr(review_result, "comments", []) or (
            review_result.get("comments", []) if isinstance(review_result, dict) else []
        )
        summary_md = getattr(review_result, "summary_markdown", "") or (
            review_result.get("summary_markdown", "") if isinstance(review_result, dict) else ""
        )

        formatted_inline_comments: List[Dict[str, Any]] = []
        for c in raw_comments:
            sev = getattr(c, "severity", None) or (c.get("severity") if isinstance(c, dict) else "INFO")
            cat = getattr(c, "category", None) or (c.get("category") if isinstance(c, dict) else "SECURITY")
            summary = getattr(c, "issue_summary", None) or (c.get("issue_summary") if isinstance(c, dict) else "")
            expl = getattr(c, "detailed_explanation", None) or (c.get("detailed_explanation") if isinstance(c, dict) else "")
            fix = getattr(c, "suggested_diff_fix", None) or (c.get("suggested_diff_fix") if isinstance(c, dict) else "")
            fpath = getattr(c, "file_path", None) or (c.get("file_path") if isinstance(c, dict) else "")
            line_no = getattr(c, "line_number", 1) or (c.get("line_number", 1) if isinstance(c, dict) else 1)

            body = (
                f"### [{sev}] {cat} Finding\n\n"
                f"**Issue:** {summary}\n\n"
                f"{expl}\n\n"
                f"**Suggested Remediation:**\n"
                f"```suggestion\n{fix}\n```"
            )
            formatted_inline_comments.append({
                "path": fpath,
                "line": int(line_no),
                "body": body,
            })

        if not commit_id:
            try:
                details = self.get_pr_details(owner, repo, pull_number)
                commit_id = details.get("head_sha")
            except Exception:
                pass

        payload = {
            "body": summary_md,
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
        import urllib.error
        url = f"{self.base_url}/repos/{owner}/{repo}/pulls/{pull_number}/reviews"

        def _do_post(p):
            req = urllib.request.Request(
                url,
                data=json.dumps(p).encode("utf-8"),
                headers={
                    "Authorization": f"Bearer {self.token}",
                    "Accept": "application/vnd.github.v3+json",
                    "Content-Type": "application/json",
                    "User-Agent": "Autonomous-PR-Reviewer-Agent"
                },
                method="POST"
            )
            with self._urlopen_safe(req, timeout=15) as resp:
                return json.loads(resp.read().decode("utf-8"))

        try:
            return _do_post(payload)
        except urllib.error.HTTPError as err:
            err_body = err.read().decode("utf-8", errors="ignore")
            # 1. If self-review, change event to COMMENT
            if err.code == 422 and payload.get("event") == "REQUEST_CHANGES":
                payload["event"] = "COMMENT"
                try:
                    res = _do_post(payload)
                    res["note"] = "Submitted as COMMENT because GitHub disallows authors requesting changes on their own PR."
                    return res
                except urllib.error.HTTPError as err2:
                    err = err2
                    err_body = err2.read().decode("utf-8", errors="ignore")

            # 2. If inline comments fail placement on diff (422), fallback to summary report
            if err.code == 422 and payload.get("comments"):
                payload_no_comments = {
                    "body": payload["body"],
                    "event": payload.get("event", "COMMENT")
                }
                if commit_id:
                    payload_no_comments["commit_id"] = commit_id
                try:
                    res = _do_post(payload_no_comments)
                    res["note"] = "Inline comments omitted due to diff placement; summary report published."
                    return res
                except Exception:
                    pass

            raise ValueError(f"GitHub review submission failed ({err.code}): {err_body}")
