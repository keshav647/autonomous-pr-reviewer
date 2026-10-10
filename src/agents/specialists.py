"""
Specialist Review Agents: Security, Performance, and Architecture.
Provides both LLM-driven structured inference (Gemini API) and deterministic AST/heuristic inspection.
"""

import re
from typing import List, Dict, Any, Optional
from ..schemas.models import ReviewComment, FileDiff
from ..config import settings
from .prompts import (
    SECURITY_SPECIALIST_PROMPT,
    PERFORMANCE_SPECIALIST_PROMPT,
    ARCHITECTURE_SPECIALIST_PROMPT,
)
from .llm_gateway import UniversalLLMGateway

class SpecialistEngine:
    """Dispatches audits to Universal LLM Gateway or fallback deterministic AST rule engines."""
    last_engine_name: Optional[str] = None
    last_used_gemini: bool = False

    @classmethod
    def audit_security(
        cls,
        file_diff: FileDiff,
        ast_context: Dict[str, Any],
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> List[ReviewComment]:
        """Runs security audit on modified hunks via Universal LLM Gateway or deterministic AST rules."""
        # 1. Try Universal LLM Inference if API key is provided
        res = UniversalLLMGateway.audit_diff(
            system_prompt=SECURITY_SPECIALIST_PROMPT,
            file_path=file_diff.new_path,
            diff_chunk=file_diff.raw_diff,
            ast_context=ast_context,
            api_key=api_key,
            provider=provider,
            model_name=model_name
        )
        if res is not None:
            comments, engine_label = res
            cls.last_engine_name = engine_label
            cls.last_used_gemini = "Gemini" in engine_label
            return comments

        # 2. Fallback Deterministic AST / Pattern Checks
        findings: List[ReviewComment] = []
        for hunk in file_diff.hunks:
            for line in hunk.lines:
                if line.line_type != "add":
                    continue

                line_num = line.new_line_number or 1
                content = line.content

                # Check SQL Injection
                if re.search(r"f[\"'].*?(SELECT|INSERT|UPDATE|DELETE).*?\{.*?\}", content, re.IGNORECASE):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="CRITICAL",
                        category="SECURITY",
                        issue_summary="Potential SQL Injection via f-string dynamic query construction.",
                        detailed_explanation=(
                            f"The query in `{file_diff.new_path}` at line {line_num} directly formats unvalidated "
                            "user input into a raw SQL statement, allowing attackers to manipulate queries via SQL injection."
                        ),
                        suggested_diff_fix=(
                            f"-    {content.strip()}\n"
                            f"+    # Use parameterized query binding\n"
                            f"+    cursor.execute(\"SELECT * FROM table WHERE param = %s\", (param,))"
                        )
                    ))

                # Check Hardcoded Secrets
                secret_match = re.search(r'(?:api_key|token|secret|password|private_key)\s*=\s*["\']([a-zA-Z0-9_\-]{16,})["\']', content, re.IGNORECASE)
                if secret_match:
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="CRITICAL",
                        category="SECURITY",
                        issue_summary="Hardcoded secret or sensitive token detected.",
                        detailed_explanation=(
                            f"Line {line_num} contains a plaintext secret. Hardcoded credentials checked into version "
                            "control can easily be scraped and lead to account compromise."
                        ),
                        suggested_diff_fix=(
                            f"-    {content.strip()}\n"
                            f"+    import os\n"
                            f"+    api_key = os.getenv(\"API_KEY\")"
                        )
                    ))

                # Check Dynamic Code Execution
                if re.search(r"\b(eval|exec)\s*\(", content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="CRITICAL",
                        category="SECURITY",
                        issue_summary="Dangerous dynamic code execution (`eval`/`exec`).",
                        detailed_explanation="Dynamic evaluation of code strings allows Remote Code Execution (RCE) if input is tainted.",
                        suggested_diff_fix=(
                            f"-    {content.strip()}\n"
                            f"+    # Refactor to use safe ast.literal_eval or json.loads\n"
                            f"+    import ast\n"
                            f"+    safe_data = ast.literal_eval(user_input)"
                        )
                    ))

                # Check Command Injection / Insecure Subprocess Execution
                if re.search(r"\b(os\.system|os\.popen|subprocess\.(?:Popen|run|call|check_output))\s*\((?!\s*[\"'][a-zA-Z0-9_\-\s./]*[\"']\s*\))", content, re.IGNORECASE):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="CRITICAL",
                        category="SECURITY",
                        issue_summary="Command Injection / Insecure Subprocess Execution vulnerability.",
                        detailed_explanation=(
                            f"Unsanitized command execution at line {line_num} invokes system shells with non-constant input, "
                            "permitting Remote Code Execution (RCE) and full server takeover."
                        ),
                        suggested_diff_fix=(
                            f"-    {content.strip()}\n"
                            f"+    # Use safe subprocess with argument lists and shell=False\n"
                            f"+    import subprocess\n"
                            f"+    subprocess.run([\"safe_binary\", validated_arg], check=True, shell=False)"
                        )
                    ))

        return findings

    @classmethod
    def audit_performance(
        cls,
        file_diff: FileDiff,
        ast_context: Dict[str, Any],
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> List[ReviewComment]:
        """Runs performance and systems audit on modified hunks via Universal LLM Gateway or AST rules."""
        # 1. Try Live LLM Inference
        res = UniversalLLMGateway.audit_diff(
            system_prompt=PERFORMANCE_SPECIALIST_PROMPT,
            file_path=file_diff.new_path,
            diff_chunk=file_diff.raw_diff,
            ast_context=ast_context,
            api_key=api_key,
            provider=provider,
            model_name=model_name
        )
        if res is not None:
            comments, engine_label = res
            cls.last_engine_name = engine_label
            cls.last_used_gemini = "Gemini" in engine_label
            return comments

        # 2. Fallback Deterministic AST / Pattern Checks
        findings: List[ReviewComment] = []
        in_loop = False
        loop_line = 0

        for hunk in file_diff.hunks:
            for line in hunk.lines:
                if line.line_type != "add":
                    continue

                line_num = line.new_line_number or 1
                content = line.content.strip()

                if content.startswith("for ") or content.startswith("while "):
                    in_loop = True
                    loop_line = line_num

                # Check N+1 database queries inside loop
                if in_loop and re.search(r"\b(cursor\.execute|session\.query|\.get_user|\.find_by_id)\s*\(", content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="WARNING",
                        category="PERFORMANCE",
                        issue_summary="N+1 Query Anti-Pattern inside iteration loop.",
                        detailed_explanation=(
                            f"Executing individual queries at line {line_num} inside the loop initiated at line {loop_line} "
                            "causes O(N) database round-trips. This degrades response latency under high data volumes."
                        ),
                        suggested_diff_fix=(
                            f"-    {content}\n"
                            f"+    # Batch fetch records before entering the loop\n"
                            f"+    # e.g., cursor.execute(\"SELECT * FROM items WHERE id IN %s\", (tuple(ids),))"
                        )
                    ))

                # Check unclosed resource connection
                if re.search(r"(?:open|connect|cursor)\s*\(", content) and not content.startswith("with "):
                    if "=" in content:
                        findings.append(ReviewComment(
                            file_path=file_diff.new_path,
                            line_number=line_num,
                            severity="WARNING",
                            category="PERFORMANCE",
                            issue_summary="Resource opened without context manager (`with` statement).",
                            detailed_explanation=(
                                f"Acquiring resources on line {line_num} without a context manager (`with`) risks resource/socket "
                                "leaks if exceptions occur before explicit `.close()` calls."
                            ),
                            suggested_diff_fix=(
                                f"-    {content}\n"
                                f"+    with open(...) as resource:\n"
                                f"+        # Perform operations inside context manager"
                            )
                        ))

                # Check blocking sleep in async code
                if "time.sleep(" in content:
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="CRITICAL",
                        category="PERFORMANCE",
                        issue_summary="Blocking `time.sleep()` call in asynchronous/event-loop context.",
                        detailed_explanation="Synchronous sleep blocks the entire Python async event loop, stalling concurrent requests.",
                        suggested_diff_fix=(
                            f"-    {content}\n"
                            f"+    await asyncio.sleep(...)  # Non-blocking async sleep"
                        )
                    ))

        return findings

    @classmethod
    def audit_architecture(
        cls,
        file_diff: FileDiff,
        ast_context: Dict[str, Any],
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> List[ReviewComment]:
        """Runs architecture, code quality, and typing audit via Universal LLM Gateway or AST rules."""
        # 1. Try Live LLM Inference
        res = UniversalLLMGateway.audit_diff(
            system_prompt=ARCHITECTURE_SPECIALIST_PROMPT,
            file_path=file_diff.new_path,
            diff_chunk=file_diff.raw_diff,
            ast_context=ast_context,
            api_key=api_key,
            provider=provider,
            model_name=model_name
        )
        if res is not None:
            comments, engine_label = res
            cls.last_engine_name = engine_label
            cls.last_used_gemini = "Gemini" in engine_label
            return comments

        # 2. Fallback Deterministic AST / Pattern Checks
        findings: List[ReviewComment] = []
        for hunk in file_diff.hunks:
            for line in hunk.lines:
                if line.line_type != "add":
                    continue

                line_num = line.new_line_number or 1
                content = line.content.strip()

                # Check bare except: or except Exception: pass
                if content == "except:" or re.search(r"except\s+Exception\s*:\s*pass", content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="WARNING",
                        category="ARCHITECTURE",
                        issue_summary="Silent exception swallowing (`bare except:` or `pass`).",
                        detailed_explanation=(
                            f"Suppressing all exceptions at line {line_num} masks fatal bugs (e.g., KeyboardInterrupt, "
                            "MemoryError, or unhandled null references) and makes debugging production failures nearly impossible."
                        ),
                        suggested_diff_fix=(
                            f"-    {content}\n"
                            f"+    except SpecificDatabaseError as err:\n"
                            f"+        logger.exception(\"Operation failed\", exc_info=err)\n"
                            f"+        raise"
                        )
                    ))

                # Check wildcard imports
                if re.match(r"^from\s+[\w\.]+\s+import\s+\*", content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="INFO",
                        category="ARCHITECTURE",
                        issue_summary="Wildcard import detected (`from module import *`).",
                        detailed_explanation="Wildcard imports pollute the local namespace and obscure where functions/classes originate.",
                        suggested_diff_fix=(
                            f"-    {content}\n"
                            f"+    from module import SpecificClass, specific_function"
                        )
                    ))

        return findings
