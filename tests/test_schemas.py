"""
Unit tests for data models and schemas.
"""

import unittest
from src.schemas.models import ReviewComment, PRReviewResult

class TestSchemas(unittest.TestCase):
    def test_review_comment_instantiation(self):
        comment = ReviewComment(
            file_path="app/main.py",
            line_number=42,
            severity="CRITICAL",
            category="SECURITY",
            issue_summary="SQL injection vulnerability",
            detailed_explanation="Formatted f-string query in cursor.execute",
            suggested_diff_fix="- query = f'...'\\n+ cursor.execute(query, (id,))"
        )
        self.assertEqual(comment.file_path, "app/main.py")
        self.assertEqual(comment.line_number, 42)
        self.assertEqual(comment.severity, "CRITICAL")
        self.assertEqual(comment.category, "SECURITY")

    def test_pr_review_result(self):
        result = PRReviewResult(
            pull_request_id=101,
            overall_status="REQUEST_CHANGES",
            summary_markdown="## Audit report",
            comments=[],
            total_token_cost_usd=0.002
        )
        self.assertEqual(result.pull_request_id, 101)
        self.assertEqual(result.overall_status, "REQUEST_CHANGES")
        self.assertEqual(result.total_token_cost_usd, 0.002)

if __name__ == "__main__":
    unittest.main()
