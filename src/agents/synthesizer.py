"""
Synthesis, Deduplication, and Conflict Resolution Agent.
Merges findings from parallel specialists, eliminates duplicate line comments,
determines PR overall verdict, and generates a structured summary report.
"""

from typing import List, Dict, Tuple
from ..schemas.models import ReviewComment, PRReviewResult

SEVERITY_WEIGHT = {
    "CRITICAL": 3,
    "WARNING": 2,
    "INFO": 1,
}

CATEGORY_PRIORITY = {
    "SECURITY": 4,
    "BUG_RISK": 3,
    "PERFORMANCE": 2,
    "ARCHITECTURE": 1,
}

class ReviewSynthesizer:
    """Consolidates and synthesizes specialist audit findings."""

    @staticmethod
    def deduplicate_and_merge(
        security_findings: List[ReviewComment],
        performance_findings: List[ReviewComment],
        architecture_findings: List[ReviewComment],
    ) -> List[ReviewComment]:
        """
        Groups comments by (file_path, line_number) and deduplicates based on severity and priority.
        """
        all_comments = list(security_findings) + list(performance_findings) + list(architecture_findings)
        grouped: Dict[Tuple[str, int], List[ReviewComment]] = {}

        for comment in all_comments:
            key = (comment.file_path, comment.line_number)
            if key not in grouped:
                grouped[key] = []
            grouped[key].append(comment)

        deduplicated: List[ReviewComment] = []

        for key, comment_list in grouped.items():
            if len(comment_list) == 1:
                deduplicated.append(comment_list[0])
            else:
                # Sort by severity descending, then category priority descending
                sorted_comments = sorted(
                    comment_list,
                    key=lambda c: (
                        SEVERITY_WEIGHT.get(c.severity, 0),
                        CATEGORY_PRIORITY.get(c.category, 0)
                    ),
                    reverse=True
                )
                winner = sorted_comments[0]
                deduplicated.append(winner)

        # Sort all final comments by severity (CRITICAL first) then file path and line number
        return sorted(
            deduplicated,
            key=lambda c: (-SEVERITY_WEIGHT.get(c.severity, 0), c.file_path, c.line_number)
        )

    @staticmethod
    def determine_verdict(comments: List[ReviewComment]) -> str:
        """Calculates final PR review status based on issue severities."""
        critical_count = sum(1 for c in comments if c.severity == "CRITICAL")
        warning_count = sum(1 for c in comments if c.severity == "WARNING")

        if critical_count > 0 or warning_count >= 3:
            return "REQUEST_CHANGES"
        elif warning_count > 0:
            return "COMMENT"
        else:
            return "APPROVE"

    @staticmethod
    def build_summary_markdown(
        pr_id: int,
        status: str,
        comments: List[ReviewComment],
        token_cost: float = 0.0
    ) -> str:
        """Constructs an executive GitHub PR summary markdown comment."""
        critical_count = sum(1 for c in comments if c.severity == "CRITICAL")
        warning_count = sum(1 for c in comments if c.severity == "WARNING")
        info_count = sum(1 for c in comments if c.severity == "INFO")

        status_label = {
            "APPROVE": "**PR STATUS: APPROVED**",
            "REQUEST_CHANGES": "**PR STATUS: CHANGES REQUESTED**",
            "COMMENT": "**PR STATUS: REVIEW COMMENTS PROVIDED**",
        }.get(status, "**PR STATUS: COMPLETED**")

        lines = [
            f"## Autonomous Multi-Agent Pull Request Audit Report",
            f"",
            f"{status_label}",
            f"",
            f"### Audit Summary Matrix",
            f"| Metric | Count |",
            f"| :--- | :--- |",
            f"| **Critical Vulnerabilities / Blockers** | `{critical_count}` |",
            f"| **Warnings (Performance & Architecture)** | `{warning_count}` |",
            f"| **Informational / Style Notes** | `{info_count}` |",
            f"| **Estimated Audit Token Cost** | `${token_cost:.4f}` |",
            f"",
        ]

        if comments:
            lines.append("### Key Action Items")
            for c in comments:
                lines.append(f"- **[{c.severity}]** `{c.file_path}:{c.line_number}` &mdash; **{c.category}**: {c.issue_summary}")
            lines.append("")
            lines.append("> *Inspect individual inline diff comments for suggested code replacements.*")
        else:
            lines.append("**All security, performance, and architecture specialist checks passed cleanly. Zero regressions detected.**")

        return "\n".join(lines)
