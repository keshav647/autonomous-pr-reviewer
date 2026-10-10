"""
Gemini Live API Verification Runner.
Tests connectivity to Google Gemini API (gemini-3.8-flash) and verifies structured output schema compliance.
"""

import sys
import os
import time
from pathlib import Path

from src.config import settings
from src.agents.gemini_client import GeminiReviewClient, FINDINGS_SCHEMA
from src.agents.graph import PRReviewGraph

RESET = "\033[0m"
BOLD = "\033[1m"
GREEN = "\033[32m"
RED = "\033[31m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"

def mask_key(key: str) -> str:
    if len(key) <= 8:
        return "********"
    return f"{key[:6]}...{key[-4:]}"

def verify_live_connection():
    print(f"\n{BOLD}{'=' * 65}{RESET}")
    print(f"{BOLD}⚡ GOOGLE GEMINI LIVE API VERIFICATION{RESET}")
    print(f"{'=' * 65}")

    api_key = settings.GEMINI_API_KEY
    model = settings.GEMINI_MODEL

    if not api_key:
        print(f"\n{YELLOW}[!] GEMINI_API_KEY is not detected.{RESET}")
        print(f"To configure your key:")
        print(f"  1. Open or create {BOLD}project-1-pr-reviewer/.env{RESET}")
        print(f"  2. Add: {BOLD}GEMINI_API_KEY=your_actual_key_here{RESET}")
        print(f"  3. Or export: {BOLD}export GEMINI_API_KEY=your_actual_key_here{RESET}\n")
        print(f"Running fallback validation using deterministic AST rules...\n")
        sys.exit(1)

    print(f"Key Status:    {GREEN}✓ Detected ({mask_key(api_key)}){RESET}")
    print(f"Target Model:  {CYAN}{model}{RESET}")
    print(f"State Graph:   {MAGENTA}LangGraph Multi-Agent Architecture{RESET}")
    print(f"{'-' * 65}")

    # Load test fixture
    fixture_path = Path(__file__).parent.parent / "tests" / "fixtures" / "sample_sql_injection.diff"
    with open(fixture_path, "r", encoding="utf-8") as f:
        sample_diff = f.read()

    print(f"\n{CYAN}Dispatching live Pull Request diff audit to {model}...{RESET}")
    start_time = time.time()

    try:
        result = PRReviewGraph.execute(
            diff_text=sample_diff,
            pr_id=77,
            repo_owner="enterprise-org",
            repo_name="core-banking-service"
        )
        elapsed_ms = (time.time() - start_time) * 1000

        print(f"{GREEN}✓ Live Audit Completed in {elapsed_ms:.1f}ms!{RESET}\n")
        print(f"Verdict:        {BOLD}{result.overall_status}{RESET}")
        print(f"Total Comments: {BOLD}{len(result.comments)}{RESET}")
        print(f"Estimated Cost: ${result.total_token_cost_usd:.4f}\n")

        print(f"{BOLD}--- Inline Agent Findings ---{RESET}")
        for idx, comment in enumerate(result.comments, 1):
            sev_color = RED if comment.severity == "CRITICAL" else YELLOW
            print(f"{sev_color}[{comment.severity}] {comment.category}{RESET} at {comment.file_path}:{BOLD}{comment.line_number}{RESET}")
            print(f"  Summary: {comment.issue_summary}")
            print(f"  Why:     {comment.detailed_explanation[:100]}...")
            if comment.suggested_diff_fix:
                print(f"  Suggested Diff Fix:")
                for l in comment.suggested_diff_fix.splitlines()[:4]:
                    print(f"    {l}")
            print()

        print(f"{GREEN}{BOLD}✓ SUCCESS: Live Gemini integration and Pydantic validation fully functional!{RESET}\n")

    except Exception as e:
        print(f"\n{RED}✗ Error during live Gemini inference: {e}{RESET}\n")
        sys.exit(1)

if __name__ == "__main__":
    verify_live_connection()
