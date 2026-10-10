"""
Unit tests for GitHub REST API Integration & Review Dispatch.
"""

import unittest
from unittest.mock import patch, MagicMock
from src.github.client import GitHubReviewClient
from src.schemas.models import PRReviewResult, ReviewComment

class TestGitHubIntegration(unittest.TestCase):
    def setUp(self):
        self.client = GitHubReviewClient(token="ghp_test_token_123456789")

    def test_post_pr_review_dry_run(self):
        review = PRReviewResult(
            pull_request_id=42,
            overall_status="REQUEST_CHANGES",
            summary_markdown="## Audit Summary\nIssues found.",
            comments=[
                ReviewComment(
                    file_path="app.py",
                    line_number=15,
                    severity="CRITICAL",
                    category="SECURITY",
                    issue_summary="RCE vulnerability",
                    detailed_explanation="Command injection via os.system",
                    suggested_diff_fix="- os.system(cmd)\n+ subprocess.run([cmd])"
                )
            ],
            total_token_cost_usd=0.0015
        )

        resp = self.client.post_pr_review(
            owner="octocat",
            repo="hello-world",
            pull_number=42,
            review_result=review,
            dry_run=True
        )

        self.assertTrue(resp.get("dry_run"))
        self.assertEqual(resp.get("event"), "REQUEST_CHANGES")
        self.assertEqual(resp.get("comments_count"), 1)
        self.assertIn("comments", resp.get("payload", {}))
        self.assertEqual(resp["payload"]["comments"][0]["path"], "app.py")
        self.assertEqual(resp["payload"]["comments"][0]["line"], 15)

    def test_post_pr_review_approve_event(self):
        review = PRReviewResult(
            pull_request_id=1,
            overall_status="APPROVE",
            summary_markdown="## Clean PR",
            comments=[],
            total_token_cost_usd=0.0
        )

        resp = self.client.post_pr_review(
            owner="octocat",
            repo="hello-world",
            pull_number=1,
            review_result=review,
            dry_run=True
        )

        self.assertEqual(resp.get("event"), "APPROVE")
        self.assertEqual(resp.get("comments_count"), 0)

    @patch("urllib.request.urlopen")
    def test_fetch_pr_diff_success(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.read.return_value = b"diff --git a/test.py b/test.py\n+print('ok')"
        mock_urlopen.return_value.__enter__.return_value = mock_response

        diff = self.client.fetch_pr_diff("pallets", "flask", 5000)
        self.assertIn("diff --git", diff)

    def test_get_pr_details_offline_fallback(self):
        client = GitHubReviewClient(token=None)
        details = client.get_pr_details("nonexistent_owner", "nonexistent_repo", 9999)
        self.assertIn("PR #9999", details.get("title", ""))

if __name__ == "__main__":
    unittest.main()
