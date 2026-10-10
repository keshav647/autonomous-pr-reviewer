"""
Command Line Interface for Autonomous Multi-Agent PR Reviewer.
Usage:
    python3 -m src.cli review --diff path/to/file.diff
    python3 -m src.cli demo
"""

import sys
import argparse
from .agents.graph import PRReviewGraph

RESET = "\033[0m"
BOLD = "\033[1m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
MAGENTA = "\033[35m"

def render_result_terminal(result):
    status_color = GREEN if result.overall_status == "APPROVE" else (RED if result.overall_status == "REQUEST_CHANGES" else YELLOW)
    print(f"\n{BOLD}{'=' * 65}{RESET}")
    print(f"{BOLD}[PR AUDITOR] MULTI-AGENT PULL REQUEST AUDIT REPORT{RESET}")
    print(f"{'=' * 65}")
    print(f"Overall Status: {status_color}{BOLD}{result.overall_status}{RESET}")
    print(f"Total Comments: {BOLD}{len(result.comments)}{RESET}")
    print(f"Est. LLM Cost:  {BOLD}${result.total_token_cost_usd:.4f}{RESET}")
    print(f"{'-' * 65}\n")

    if not result.comments:
        print(f"{GREEN}✓ No security vulnerabilities or performance bottlenecks detected.{RESET}\n")
        return

    for idx, c in enumerate(result.comments, 1):
        sev_color = RED if c.severity == "CRITICAL" else (YELLOW if c.severity == "WARNING" else CYAN)
        print(f"{sev_color}{BOLD}[{c.severity}] {c.category}{RESET} - {c.file_path}:{BOLD}{c.line_number}{RESET}")
        print(f"  {BOLD}Issue:{RESET} {c.issue_summary}")
        print(f"  {BOLD}Why:{RESET}   {c.detailed_explanation}")
        print(f"  {CYAN}Suggested Diff Fix:{RESET}")
        for fix_line in c.suggested_diff_fix.splitlines():
            line_color = RED if fix_line.startswith("-") else (GREEN if fix_line.startswith("+") else RESET)
            print(f"    {line_color}{fix_line}{RESET}")
        print()

def main():
    parser = argparse.ArgumentParser(description="Autonomous Multi-Agent PR Reviewer & Security Auditor")
    subparsers = parser.add_subparsers(dest="command")

    # review command
    review_parser = subparsers.add_parser("review", help="Audit a git diff file")
    review_parser.add_argument("--diff", required=True, help="Path to unified diff file")
    review_parser.add_argument("--pr-id", type=int, default=1, help="Pull request ID")

    # serve command
    serve_parser = subparsers.add_parser("serve", help="Launch interactive BYOK Web UI & API server")
    serve_parser.add_argument("--port", type=int, default=8000, help="Port to listen on (default: 8000)")
    serve_parser.add_argument("--host", default="0.0.0.0", help="Host interface (default: 0.0.0.0)")

    # demo command
    demo_parser = subparsers.add_parser("demo", help="Run interactive terminal showcase demo")

    args = parser.parse_args()

    if args.command == "serve":
        from .api.server import run_native_server
        run_native_server(host=args.host, port=args.port)

    elif args.command == "review":
        with open(args.diff, "r", encoding="utf-8") as f:
            diff_text = f.read()
        result = PRReviewGraph.execute(diff_text, pr_id=args.pr_id)
        render_result_terminal(result)

    elif args.command == "demo" or len(sys.argv) == 1:
        sample_diff = (
            "diff --git a/app/routes/users.py b/app/routes/users.py\n"
            "--- a/app/routes/users.py\n"
            "+++ b/app/routes/users.py\n"
            "@@ -10,6 +10,12 @@ def get_user_data(user_id: str):\n"
            "+    # Insecure query formatting\n"
            "+    query = f\"SELECT * FROM users WHERE id = '{user_id}'\"\n"
            "+    cursor.execute(query)\n"
            "+    for row in cursor.fetchall():\n"
            "+        profile = cursor.execute(f\"SELECT * FROM profiles WHERE user_id = {row[0]}\")\n"
            "+    return cursor.fetchone()\n"
        )
        print(f"{CYAN}Running Multi-Agent Showcase Demo on Sample Vulnerability Diff...{RESET}")
        result = PRReviewGraph.execute(sample_diff, pr_id=42)
        render_result_terminal(result)

if __name__ == "__main__":
    main()
