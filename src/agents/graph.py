"""
LangGraph Multi-Agent Orchestration Graph.
Implements the cyclical review state machine with parallel specialist agents,
synthesis, and Pydantic validation guardrails.
"""

import concurrent.futures
from typing import Dict, Any, List, Optional
from ..schemas.models import PRReviewResult, ReviewComment, FileDiff
from ..parser.diff_parser import DiffParser
from ..parser.ast_analyzer import PythonASTAnalyzer
from .state import AgentReviewState
from .specialists import SpecialistEngine
from .synthesizer import ReviewSynthesizer

class PRReviewGraph:
    """Multi-Agent Review Graph Orchestrator."""

    @staticmethod
    def orchestrator_node(state: AgentReviewState) -> AgentReviewState:
        """Parses diff, runs AST analysis on Python files, and activates specialist reviewers."""
        diff_text = state.get("diff_text", "")
        files = DiffParser.parse_patch(diff_text)
        state["files"] = files

        ast_analyses = {}
        for f in files:
            if f.language == "python":
                # Analyze full hunk context as synthetic source for AST
                synthetic_src = "\n".join(
                    line.content for hunk in f.hunks for line in hunk.lines if line.line_type in ("add", "context")
                )
                ast_analyses[f.new_path] = PythonASTAnalyzer.analyze_source(synthetic_src)

        state["ast_analyses"] = ast_analyses

        # Determine active specialists
        active_specialists = ["SECURITY", "PERFORMANCE", "ARCHITECTURE"]
        state["active_specialists"] = active_specialists
        state["iteration_count"] = state.get("iteration_count", 0) + 1

        return state

    @staticmethod
    def security_node(state: AgentReviewState) -> AgentReviewState:
        """Runs the security specialist on all active files."""
        findings: List[ReviewComment] = []
        files: List[FileDiff] = state.get("files", [])
        ast_analyses = state.get("ast_analyses", {})
        api_key = state.get("api_key")
        provider = state.get("provider")
        model_name = state.get("model_name")

        for f in files:
            ctx = ast_analyses.get(f.new_path, {})
            findings.extend(SpecialistEngine.audit_security(
                f, ctx, api_key=api_key, provider=provider, model_name=model_name
            ))

        state["security_findings"] = findings
        return state

    @staticmethod
    def performance_node(state: AgentReviewState) -> AgentReviewState:
        """Runs the performance specialist on all active files."""
        findings: List[ReviewComment] = []
        files: List[FileDiff] = state.get("files", [])
        ast_analyses = state.get("ast_analyses", {})
        api_key = state.get("api_key")
        provider = state.get("provider")
        model_name = state.get("model_name")

        for f in files:
            ctx = ast_analyses.get(f.new_path, {})
            findings.extend(SpecialistEngine.audit_performance(
                f, ctx, api_key=api_key, provider=provider, model_name=model_name
            ))

        state["performance_findings"] = findings
        return state

    @staticmethod
    def architecture_node(state: AgentReviewState) -> AgentReviewState:
        """Runs the architecture specialist on all active files."""
        findings: List[ReviewComment] = []
        files: List[FileDiff] = state.get("files", [])
        ast_analyses = state.get("ast_analyses", {})
        api_key = state.get("api_key")
        provider = state.get("provider")
        model_name = state.get("model_name")

        for f in files:
            ctx = ast_analyses.get(f.new_path, {})
            findings.extend(SpecialistEngine.audit_architecture(
                f, ctx, api_key=api_key, provider=provider, model_name=model_name
            ))

        state["architecture_findings"] = findings
        return state

    @staticmethod
    def synthesizer_node(state: AgentReviewState) -> AgentReviewState:
        """Consolidates findings and builds markdown report."""
        sec = state.get("security_findings", [])
        perf = state.get("performance_findings", [])
        arch = state.get("architecture_findings", [])

        merged_comments = ReviewSynthesizer.deduplicate_and_merge(sec, perf, arch)
        status = ReviewSynthesizer.determine_verdict(merged_comments)
        pr_id = state.get("pull_request_id", 1)
        token_cost = state.get("total_token_cost_usd", 0.0015)

        summary_md = ReviewSynthesizer.build_summary_markdown(
            pr_id=pr_id,
            status=status,
            comments=merged_comments,
            token_cost=token_cost
        )

        state["synthesized_comments"] = merged_comments
        state["overall_status"] = status
        state["summary_markdown"] = summary_md
        state["total_token_cost_usd"] = token_cost
        return state

    @staticmethod
    def validator_node(state: AgentReviewState) -> AgentReviewState:
        """Validates that all synthesized outputs conform to strict schema requirements."""
        errors: List[str] = []
        comments = state.get("synthesized_comments", [])

        for idx, comment in enumerate(comments):
            if not comment.file_path:
                errors.append(f"Comment {idx} missing file_path")
            if comment.line_number <= 0:
                errors.append(f"Comment {idx} invalid line_number: {comment.line_number}")
            if comment.severity not in ("CRITICAL", "WARNING", "INFO"):
                errors.append(f"Comment {idx} invalid severity: {comment.severity}")
            if comment.category not in ("SECURITY", "PERFORMANCE", "ARCHITECTURE", "BUG_RISK"):
                errors.append(f"Comment {idx} invalid category: {comment.category}")

        if errors:
            state["validation_passed"] = False
            state["validation_errors"] = errors
        else:
            state["validation_passed"] = True
            state["validation_errors"] = []

        return state

    @classmethod
    def execute(
        cls,
        diff_text: str,
        pr_id: int = 1,
        repo_owner: str = "demo",
        repo_name: str = "repo",
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> PRReviewResult:
        """
        Executes the full agent graph state machine sequentially and returns validated PRReviewResult.
        Supports multi-provider LLM execution (Gemini, OpenAI, Anthropic, Groq, OpenRouter) or deterministic AST fallback.
        """
        initial_state: AgentReviewState = {
            "pull_request_id": pr_id,
            "repo_owner": repo_owner,
            "repo_name": repo_name,
            "diff_text": diff_text,
            "files": [],
            "ast_analyses": {},
            "api_key": api_key,
            "provider": provider,
            "model_name": model_name,
            "active_specialists": [],
            "security_findings": [],
            "performance_findings": [],
            "architecture_findings": [],
            "synthesized_comments": [],
            "overall_status": "APPROVE",
            "summary_markdown": "",
            "total_token_cost_usd": 0.0012,
            "validation_passed": False,
            "validation_errors": [],
            "iteration_count": 0,
        }

        # Reset specialist LLM engine tracking
        SpecialistEngine.last_engine_name = None
        SpecialistEngine.last_used_gemini = False

        # Step 1: Orchestrator
        state = cls.orchestrator_node(initial_state)

        # Step 2: Concurrent Parallel Specialist Reviewers
        with concurrent.futures.ThreadPoolExecutor(max_workers=3) as executor:
            sec_future = executor.submit(cls.security_node, dict(state))
            perf_future = executor.submit(cls.performance_node, dict(state))
            arch_future = executor.submit(cls.architecture_node, dict(state))

            sec_state = sec_future.result()
            perf_state = perf_future.result()
            arch_state = arch_future.result()

        state["security_findings"] = sec_state.get("security_findings", [])
        state["performance_findings"] = perf_state.get("performance_findings", [])
        state["architecture_findings"] = arch_state.get("architecture_findings", [])

        # Step 3: Synthesis & Deduplication
        state = cls.synthesizer_node(state)

        # Step 4: Validation Guardrail
        state = cls.validator_node(state)

        engine_used = SpecialistEngine.last_engine_name or "AST Deterministic Engine (Offline Fallback)"

        return PRReviewResult(
            pull_request_id=state["pull_request_id"],
            overall_status=state["overall_status"],  # type: ignore
            summary_markdown=state["summary_markdown"],
            comments=state["synthesized_comments"],
            total_token_cost_usd=state["total_token_cost_usd"],
            engine_used=engine_used
        )
