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

                # Check SQL Injection (f-string, format, % or concatenation)
                if re.search(r"(?:f[\"'].*?(SELECT|INSERT|UPDATE|DELETE|DROP|ALTER|WHERE).*?\{.*?\}|[\"'].*?(SELECT|INSERT|UPDATE|DELETE|WHERE).*?[\"']\s*%\s*\w+|\.format\(.*?\)|[\"'].*?(SELECT|INSERT|UPDATE|DELETE|WHERE).*?[\"']\s*\+\s*\w+)", content, re.IGNORECASE):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="CRITICAL",
                        category="SECURITY",
                        issue_summary="Potential SQL Injection via unparameterized dynamic query construction.",
                        detailed_explanation=(
                            f"The query in `{file_diff.new_path}` at line {line_num} directly formats unvalidated "
                            "user input into a raw SQL statement, allowing attackers to manipulate queries via SQL injection (CWE-89)."
                        ),
                        suggested_diff_fix=(
                            f"-    {content.strip()}\n"
                            f"+    # Use parameterized query binding\n"
                            f"+    cursor.execute(\"SELECT * FROM table WHERE param = %s\", (param,))"
                        )
                    ))

                # Check Hardcoded Secrets & High-Entropy Credentials
                secret_patterns = [
                    (r'(?:api_key|token|secret|password|private_key|jwt_secret)\s*=\s*["\']([a-zA-Z0-9_\-]{14,})["\']', "Hardcoded secret or sensitive token detected (CWE-798)."),
                    (r'AKIA[0-9A-Z]{16}', "Hardcoded AWS Access Key ID detected."),
                    (r'gh[pous]_[a-zA-Z0-9]{36}', "Hardcoded GitHub Personal Access Token detected."),
                    (r'(?:sk|rk)_live_[0-9a-zA-Z]{24,}', "Hardcoded Stripe Live Secret Key detected."),
                    (r'-----BEGIN (?:RSA )?PRIVATE KEY-----', "Embedded cryptographic private key detected.")
                ]
                for pattern, desc in secret_patterns:
                    if re.search(pattern, content, re.IGNORECASE):
                        findings.append(ReviewComment(
                            file_path=file_diff.new_path,
                            line_number=line_num,
                            severity="CRITICAL",
                            category="SECURITY",
                            issue_summary=desc,
                            detailed_explanation=(
                                f"Line {line_num} contains a plaintext credential. Hardcoded secrets checked into version "
                                "control can easily be scraped, leading to infrastructure or data compromise."
                            ),
                            suggested_diff_fix=(
                                f"-    {content.strip()}\n"
                                f"+    import os\n"
                                f"+    secret_val = os.getenv(\"CONFIGURED_SECRET_KEY\")"
                            )
                        ))
                        break

                # Check Dynamic Code Execution
                if re.search(r"\b(eval|exec)\s*\(", content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="CRITICAL",
                        category="SECURITY",
                        issue_summary="Dangerous dynamic code execution (`eval`/`exec`).",
                        detailed_explanation="Dynamic evaluation of code strings allows Remote Code Execution (RCE) if input is tainted (CWE-95).",
                        suggested_diff_fix=(
                            f"-    {content.strip()}\n"
                            f"+    # Refactor to use safe ast.literal_eval or json.loads\n"
                            f"+    import ast\n"
                            f"+    safe_data = ast.literal_eval(user_input)"
                        )
                    ))

                # Check Command Injection / Insecure Subprocess Execution
                if re.search(r"\b(os\.system|os\.popen|subprocess\.(?:Popen|run|call|check_output))\s*\((?!\s*[\"'][a-zA-Z0-9_\-\s./]*[\"']\s*\))", content, re.IGNORECASE) or ("shell=True" in content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="CRITICAL",
                        category="SECURITY",
                        issue_summary="Command Injection / Insecure Subprocess Execution vulnerability (CWE-78).",
                        detailed_explanation=(
                            f"Unsanitized command execution at line {line_num} invokes system shells with dynamic input, "
                            "permitting Remote Code Execution (RCE) and full server takeover."
                        ),
                        suggested_diff_fix=(
                            f"-    {content.strip()}\n"
                            f"+    # Use safe subprocess with argument lists and shell=False\n"
                            f"+    import subprocess\n"
                            f"+    subprocess.run([\"safe_binary\", validated_arg], check=True, shell=False)"
                        )
                    ))

                # Check Path Traversal
                if re.search(r"os\.path\.join\(.*,\s*(?:filename|filepath|user_path|path)\)", content) or re.search(r"open\(f?[\"'].*?\{.*?(?:file|path|name).*?\}.*?[\"']", content):
                    if "os.path.abspath" not in content and "os.path.commonpath" not in content:
                        findings.append(ReviewComment(
                            file_path=file_diff.new_path,
                            line_number=line_num,
                            severity="CRITICAL",
                            category="SECURITY",
                            issue_summary="Potential Path Traversal / Arbitrary File Access vulnerability (CWE-22).",
                            detailed_explanation=(
                                f"Constructing filesystem paths from dynamic variables at line {line_num} without canonical path boundary verification "
                                "allows attackers to supply `../` sequences and read/overwrite arbitrary files on the host."
                            ),
                            suggested_diff_fix=(
                                f"-    {content.strip()}\n"
                                f"+    # Canonicalize and verify directory boundary\n"
                                f"+    safe_path = os.path.abspath(os.path.join(BASE_DIR, os.path.basename(filename)))\n"
                                f"+    if not safe_path.startswith(os.path.abspath(BASE_DIR)):\n"
                                f"+        raise ValueError(\"Path traversal detected\")"
                            )
                        ))

                # Check Insecure Deserialization
                if re.search(r"\b(pickle\.(?:loads?|load)|yaml\.load\((?!.*Loader=yaml\.SafeLoader))\b", content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="CRITICAL",
                        category="SECURITY",
                        issue_summary="Insecure Deserialization vulnerability (CWE-502).",
                        detailed_explanation=(
                            f"Deserializing untrusted streams at line {line_num} using `pickle` or unconstrained `yaml.load` "
                            "permits arbitrary object instantiation and Remote Code Execution."
                        ),
                        suggested_diff_fix=(
                            f"-    {content.strip()}\n"
                            f"+    import json\n"
                            f"+    safe_data = json.loads(untrusted_payload)"
                        )
                    ))

                # Check Weak Cryptography / Hashing
                if re.search(r"\bhashlib\.(md5|sha1)\s*\(", content, re.IGNORECASE):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="WARNING",
                        category="SECURITY",
                        issue_summary="Use of cryptographically weak hash algorithm (MD5/SHA1, CWE-327).",
                        detailed_explanation=(
                            f"Hash algorithm at line {line_num} is collision-vulnerable. Use SHA-256 for integrity "
                            "or Argon2/bcrypt/PBKDF2 for password storage."
                        ),
                        suggested_diff_fix=(
                            f"-    {content.strip()}\n"
                            f"+    import hashlib\n"
                            f"+    secure_hash = hashlib.sha256(data.encode()).hexdigest()"
                        )
                    ))

                # Check Insecure SSL/TLS Verification
                if re.search(r"\bverify\s*=\s*False\b", content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="WARNING",
                        category="SECURITY",
                        issue_summary="Disabled SSL/TLS Certificate Verification (CWE-295).",
                        detailed_explanation=(
                            f"Disabling certificate verification at line {line_num} allows Man-in-the-Middle (MITM) attacks "
                            "where eavesdroppers can intercept and modify sensitive network traffic."
                        ),
                        suggested_diff_fix=(
                            f"-    {content.strip()}\n"
                            f"+    # Retain standard CA certificate verification\n"
                            f"+    response = httpx.get(url, verify=True)"
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
                if in_loop and re.search(r"\b(cursor\.execute|session\.query|\.get_user|\.find_by_id|\.select)\s*\(", content):
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

                # Check string concatenation accumulation inside loops
                if in_loop and re.search(r"\w+\s*\+=\s*[\"'].*?[\"']", content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="INFO",
                        category="PERFORMANCE",
                        issue_summary="Inefficient string concatenation in loop (O(N^2) memory reallocations).",
                        detailed_explanation=(
                            f"Accumulating strings with `+=` on line {line_num} creates intermediate string copies on every iteration. "
                            "Use a list accumulator with `''.join(...)`."
                        ),
                        suggested_diff_fix=(
                            f"-    {content}\n"
                            f"+    chunks.append(item)\n"
                            f"+    result = ''.join(chunks)"
                        )
                    ))

                # Check repeated regex compilation in loop
                if in_loop and re.search(r"\bre\.(?:compile|search|match|findall)\s*\(", content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="INFO",
                        category="PERFORMANCE",
                        issue_summary="Repeated regular expression compilation inside loop.",
                        detailed_explanation=(
                            f"Compiling regex on line {line_num} repeatedly during iteration causes unnecessary CPU overhead. "
                            "Pre-compile the pattern at module level."
                        ),
                        suggested_diff_fix=(
                            f"-    {content}\n"
                            f"+    # Pre-compile outside loop: PATTERN = re.compile(...)\n"
                            f"+    PATTERN.search(item)"
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
                if content == "except:" or re.search(r"except\s+(?:Exception)?\s*:\s*(?:pass|\.\.\.)", content):
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

                # Check mutable default arguments
                if re.search(r"def\s+\w+\s*\(.*?(?:=\s*\[\]|=\s*\{\})\s*.*?\):", content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="WARNING",
                        category="ARCHITECTURE",
                        issue_summary="Dangerous mutable default argument (`[]` or `{}`).",
                        detailed_explanation=(
                            f"Default parameter at line {line_num} is instantiated once at function definition time. "
                            "Mutating it inside the function affects all subsequent calls."
                        ),
                        suggested_diff_fix=(
                            f"-    {content}\n"
                            f"+    def function_name(param: Optional[List] = None):\n"
                            f"+        if param is None: param = []"
                        )
                    ))

                # Check global variable mutation
                if re.match(r"^global\s+\w+", content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="INFO",
                        category="ARCHITECTURE",
                        issue_summary="Global state mutation (`global` keyword).",
                        detailed_explanation="Mutating global state introduces hidden coupling between components and prevents thread-safe concurrent execution.",
                        suggested_diff_fix=(
                            f"-    {content}\n"
                            f"+    # Pass state explicitly as parameter or encapsulate inside a class"
                        )
                    ))

                # Check hardcoded localhost endpoint
                if re.search(r"https?://(?:localhost|127\.0\.0\.1)(?::\d+)?", content):
                    findings.append(ReviewComment(
                        file_path=file_diff.new_path,
                        line_number=line_num,
                        severity="INFO",
                        category="ARCHITECTURE",
                        issue_summary="Hardcoded local development URL (`localhost` / `127.0.0.1`).",
                        detailed_explanation="Hardcoding development URLs breaks portability in containerized, staging, and production environments.",
                        suggested_diff_fix=(
                            f"-    {content}\n"
                            f"+    SERVICE_URL = os.getenv(\"SERVICE_URL\", \"https://api.example.com\")"
                        )
                    ))

        return findings
