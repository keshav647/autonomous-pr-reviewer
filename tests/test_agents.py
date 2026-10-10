"""
Unit tests for Multi-Agent Graph, Specialist review logic, and synthesis.
"""

import os
import unittest
from src.agents.graph import PRReviewGraph
from src.agents.synthesizer import ReviewSynthesizer
from src.schemas.models import ReviewComment

FIXTURES_DIR = os.path.join(os.path.dirname(__file__), "fixtures")

class TestMultiAgentSystem(unittest.TestCase):
    def test_sql_injection_pr_audit(self):
        fixture_path = os.path.join(FIXTURES_DIR, "sample_sql_injection.diff")
        with open(fixture_path, "r", encoding="utf-8") as f:
            diff_text = f.read()

        result = PRReviewGraph.execute(diff_text, pr_id=12)

        self.assertEqual(result.pull_request_id, 12)
        self.assertEqual(result.overall_status, "REQUEST_CHANGES")
        self.assertTrue(len(result.comments) >= 1)

        categories = [c.category for c in result.comments]
        severities = [c.severity for c in result.comments]

        self.assertIn("SECURITY", categories)
        self.assertIn("CRITICAL", severities)
        self.assertIn("PR STATUS: CHANGES REQUESTED", result.summary_markdown)

    def test_performance_leak_audit(self):
        fixture_path = os.path.join(FIXTURES_DIR, "sample_performance_leak.diff")
        with open(fixture_path, "r", encoding="utf-8") as f:
            diff_text = f.read()

        result = PRReviewGraph.execute(diff_text, pr_id=15)

        self.assertIn(result.overall_status, ("REQUEST_CHANGES", "COMMENT"))
        self.assertTrue(len(result.comments) >= 1)
        categories = [c.category for c in result.comments]
        self.assertIn("PERFORMANCE", categories)

    def test_clean_pr_audit(self):
        fixture_path = os.path.join(FIXTURES_DIR, "sample_clean_pr.diff")
        with open(fixture_path, "r", encoding="utf-8") as f:
            diff_text = f.read()

        result = PRReviewGraph.execute(diff_text, pr_id=20)

        self.assertEqual(result.overall_status, "APPROVE")
        self.assertEqual(len(result.comments), 0)
        self.assertIn("PR STATUS: APPROVED", result.summary_markdown)

    def test_deduplication_and_conflict_resolution(self):
        c1 = ReviewComment(
            file_path="app.py",
            line_number=10,
            severity="WARNING",
            category="PERFORMANCE",
            issue_summary="Slow query",
            detailed_explanation="N+1 loop",
            suggested_diff_fix=""
        )
        c2 = ReviewComment(
            file_path="app.py",
            line_number=10,
            severity="CRITICAL",
            category="SECURITY",
            issue_summary="SQL injection",
            detailed_explanation="Exploitable string interpolation",
            suggested_diff_fix=""
        )

        merged = ReviewSynthesizer.deduplicate_and_merge(
            security_findings=[c2],
            performance_findings=[c1],
            architecture_findings=[]
        )

        self.assertEqual(len(merged), 1)
        # Winner must be the CRITICAL security finding
        self.assertEqual(merged[0].severity, "CRITICAL")
        self.assertEqual(merged[0].category, "SECURITY")

    def test_universal_gateway_provider_detection(self):
        from src.agents.llm_gateway import detect_provider, UniversalLLMGateway
        self.assertEqual(detect_provider("AIzaSyD-xxx"), "gemini")
        self.assertEqual(detect_provider("sk-ant-api03-xxx"), "anthropic")
        self.assertEqual(detect_provider("gsk_xxx"), "groq")
        self.assertEqual(detect_provider("sk-or-v1-xxx"), "openrouter")
        self.assertEqual(detect_provider("sk-proj-xxx"), "openai")
        self.assertEqual(detect_provider("any-key", requested_provider="openai"), "openai")

    def test_universal_gateway_json_parsing(self):
        from src.agents.llm_gateway import UniversalLLMGateway
        sample_json = '''
        {
            "findings": [
                {
                    "file_path": "auth.py",
                    "line_number": 14,
                    "severity": "CRITICAL",
                    "category": "SECURITY",
                    "issue_summary": "SQL injection vulnerability",
                    "detailed_explanation": "Raw query interpolation",
                    "suggested_diff_fix": "+ cursor.execute(query, (id,))"
                }
            ]
        }
        '''
        comments = UniversalLLMGateway._parse_findings_json(sample_json, "auth.py")
        self.assertIsNotNone(comments)
        self.assertEqual(len(comments), 1)
        self.assertEqual(comments[0].severity, "CRITICAL")
        self.assertEqual(comments[0].line_number, 14)

if __name__ == "__main__":
    unittest.main()
