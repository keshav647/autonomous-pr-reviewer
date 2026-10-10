"""Unit tests for FastAPI routers and API endpoints."""

import unittest
from starlette.testclient import TestClient
from src.api.server import app

class TestAPIRoutes(unittest.TestCase):
    """Verifies that all API routes respond with valid status and schemas."""

    def setUp(self):
        self.client = TestClient(app)

    def test_health_endpoint(self):
        resp = self.client.get("/health")
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("status"), "healthy")
        self.assertEqual(data.get("service"), "pr-reviewer-agent")
        self.assertTrue(data.get("byok_ready"))

    def test_review_endpoint_ast_fallback(self):
        sample_diff = (
            "diff --git a/app.py b/app.py\n"
            "--- a/app.py\n"
            "+++ b/app.py\n"
            "@@ -1,2 +1,3 @@\n"
            "+query = f\"SELECT * FROM users WHERE id = {user_id}\"\n"
        )
        resp = self.client.post("/api/v1/review", json={
            "diff_text": sample_diff,
            "pull_request_id": 42,
            "repo_owner": "test",
            "repo_name": "repo"
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertEqual(data.get("pull_request_id"), 42)
        self.assertIn("overall_status", data)
        self.assertIn("summary_markdown", data)
        self.assertIsInstance(data.get("comments"), list)

    def test_github_fetch_invalid_url(self):
        resp = self.client.post("/api/v1/github/fetch", json={
            "repo": "invalid-no-slash",
            "pull_number": 0
        })
        self.assertEqual(resp.status_code, 400)

    def test_github_publish_dry_run(self):
        resp = self.client.post("/api/v1/github/publish", json={
            "owner": "testowner",
            "repo": "testrepo",
            "pull_number": 1,
            "review_result": {
                "pull_request_id": 1,
                "overall_status": "REQUEST_CHANGES",
                "summary_markdown": "Test report",
                "comments": []
            },
            "dry_run": True
        })
        self.assertEqual(resp.status_code, 200)
        data = resp.json()
        self.assertTrue(data.get("success"))
        self.assertTrue(data.get("dry_run"))

if __name__ == "__main__":
    unittest.main()
