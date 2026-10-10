"""
Universal Multi-Provider LLM Gateway.
Supports Google Gemini (gemini-3.8-flash), OpenAI (GPT-4o), Anthropic (Claude 3.5 Sonnet),
Groq (Llama 3.3), and OpenRouter with strict structured JSON output and auto-provider detection.
"""

import sys
import json
import logging
import urllib.request
import urllib.error
from typing import Optional, Dict, Any, List

from ..config import settings
from ..schemas.models import ReviewComment

logger = logging.getLogger(__name__)

# Standard JSON Schema (strict lowercase types per JSON Schema RFC)
UNIVERSAL_FINDINGS_SCHEMA = {
    "type": "object",
    "properties": {
        "findings": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "file_path": {"type": "string", "description": "Exact relative file path"},
                    "line_number": {"type": "integer", "description": "Target line number in diff"},
                    "severity": {"type": "string", "enum": ["CRITICAL", "WARNING", "INFO"]},
                    "category": {"type": "string", "enum": ["SECURITY", "PERFORMANCE", "ARCHITECTURE", "BUG_RISK"]},
                    "issue_summary": {"type": "string", "description": "One sentence summary"},
                    "detailed_explanation": {"type": "string", "description": "Technical root cause"},
                    "suggested_diff_fix": {"type": "string", "description": "Replacement git diff block"}
                },
                "required": [
                    "file_path",
                    "line_number",
                    "severity",
                    "category",
                    "issue_summary",
                    "detailed_explanation",
                    "suggested_diff_fix"
                ]
            }
        }
    },
    "required": ["findings"]
}

def detect_provider(api_key: str, requested_provider: Optional[str] = None) -> str:
    """Auto-detects model provider from key format or uses explicit provider selection."""
    if requested_provider and requested_provider.lower() not in ("auto", ""):
        return requested_provider.lower()
    
    key = api_key.strip()
    if key.startswith("AIza"):
        return "gemini"
    elif key.startswith("sk-ant-"):
        return "anthropic"
    elif key.startswith("gsk_"):
        return "groq"
    elif key.startswith("sk-or-"):
        return "openrouter"
    elif key.startswith("sk-"):
        return "openai"
    return "gemini"

class UniversalLLMGateway:
    """Unified client for invoking any LLM provider with structured output."""

    @classmethod
    def audit_diff(
        cls,
        system_prompt: str,
        file_path: str,
        diff_chunk: str,
        ast_context: Dict[str, Any],
        api_key: Optional[str] = None,
        provider: Optional[str] = None,
        model_name: Optional[str] = None
    ) -> Optional[tuple[List[ReviewComment], str]]:
        """
        Dispatches audit prompt to the selected LLM provider.
        Returns: tuple(comments, resolved_model_name) or None
        """
        key = api_key or settings.GEMINI_API_KEY
        if not key:
            return None

        prov = detect_provider(key, provider)
        prompt = (
            f"{system_prompt}\n\n"
            f"TARGET FILE: {file_path}\n"
            f"AST SCOPES & FLAGS: {json.dumps(ast_context, indent=2)}\n\n"
            f"GIT DIFF CHUNK:\n```diff\n{diff_chunk}\n```\n\n"
            f"Audit the modified code lines. Respond ONLY with valid JSON matching this schema:\n"
            f"{json.dumps(UNIVERSAL_FINDINGS_SCHEMA)}"
        )

        try:
            if prov == "gemini":
                return cls._call_gemini(key, prompt, file_path, model_name or "gemini-2.5-flash")
            elif prov == "openai":
                return cls._call_openai(key, prompt, file_path, model_name or "gpt-4o-mini")
            elif prov == "groq":
                return cls._call_openai_compatible(
                    key, prompt, file_path,
                    base_url="https://api.groq.com/openai/v1/chat/completions",
                    model_name=model_name or "llama-3.3-70b-versatile",
                    provider_label="Groq"
                )
            elif prov == "openrouter":
                return cls._call_openai_compatible(
                    key, prompt, file_path,
                    base_url="https://openrouter.ai/api/v1/chat/completions",
                    model_name=model_name or "google/gemini-2.5-flash",
                    provider_label="OpenRouter"
                )
            elif prov == "anthropic":
                return cls._call_anthropic(key, prompt, file_path, model_name or "claude-3-5-sonnet-20241022")
            else:
                return cls._call_gemini(key, prompt, file_path, model_name or "gemini-2.5-flash")
        except Exception as e:
            sys.stderr.write(f"LLM Gateway exception ({prov}): {e}\n")
            return None

    @classmethod
    def _call_gemini(cls, api_key: str, prompt: str, default_path: str, model_name: str) -> Optional[tuple[List[ReviewComment], str]]:
        """Calls Google Gemini using standard REST endpoint and standard lowercase JSON schema."""
        # Clean model name if legacy or invalid model passed
        resolved_model = model_name if model_name not in ("gemini-3.8-flash", "auto", "") else "gemini-2.5-flash"
        candidate_models = [resolved_model, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        unique_models = list(dict.fromkeys(candidate_models))

        for m in unique_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{m}:generateContent?key={api_key}"
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": UNIVERSAL_FINDINGS_SCHEMA
                }
            }

            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=12) as resp:
                    data = json.loads(resp.read().decode("utf-8"))
                    candidates = data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            raw_text = parts[0].get("text", "")
                            comments = cls._parse_findings_json(raw_text, default_path)
                            if comments is not None:
                                sys.stderr.write(f"✓ Gemini API response parsed successfully via {m}\n")
                                return comments, f"Google Gemini ({m})"
            except urllib.error.HTTPError as http_err:
                err_msg = http_err.read().decode("utf-8", errors="ignore")
                sys.stderr.write(f"Gemini API model {m} returned {http_err.code}: {err_msg[:120]}...\n")
                if http_err.code in (404, 400):
                    continue
                break
            except Exception as e:
                sys.stderr.write(f"Gemini request failed ({m}): {e}\n")
                break

        return None

    @classmethod
    def _call_openai(cls, api_key: str, prompt: str, default_path: str, model_name: str) -> Optional[tuple[List[ReviewComment], str]]:
        """Calls OpenAI Chat Completions API with JSON object response format."""
        return cls._call_openai_compatible(
            api_key=api_key,
            prompt=prompt,
            default_path=default_path,
            base_url="https://api.openai.com/v1/chat/completions",
            model_name=model_name,
            provider_label="OpenAI"
        )

    @classmethod
    def _call_openai_compatible(
        cls,
        api_key: str,
        prompt: str,
        default_path: str,
        base_url: str,
        model_name: str,
        provider_label: str
    ) -> Optional[tuple[List[ReviewComment], str]]:
        """Universal handler for OpenAI-compatible APIs (OpenAI, Groq, OpenRouter)."""
        payload = {
            "model": model_name,
            "messages": [
                {"role": "system", "content": "You are a senior code reviewer. Respond only with JSON conforming to the schema."},
                {"role": "user", "content": prompt}
            ],
            "response_format": {"type": "json_object"}
        }

        try:
            req = urllib.request.Request(
                base_url,
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=25) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                choices = data.get("choices", [])
                if choices:
                    content = choices[0].get("message", {}).get("content", "")
                    comments = cls._parse_findings_json(content, default_path)
                    if comments is not None:
                        sys.stderr.write(f"✓ {provider_label} response parsed successfully via {model_name}\n")
                        return comments, f"{provider_label} ({model_name})"
        except Exception as e:
            sys.stderr.write(f"{provider_label} API request failed ({model_name}): {e}\n")

        return None

    @classmethod
    def _call_anthropic(cls, api_key: str, prompt: str, default_path: str, model_name: str) -> Optional[tuple[List[ReviewComment], str]]:
        """Calls Anthropic Messages API."""
        payload = {
            "model": model_name,
            "max_tokens": 4096,
            "messages": [{"role": "user", "content": prompt}],
            "system": "You are an autonomous code reviewer. Respond exclusively with valid JSON conforming to the findings schema."
        }
        try:
            req = urllib.request.Request(
                "https://api.anthropic.com/v1/messages",
                data=json.dumps(payload).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "x-api-key": api_key,
                    "anthropic-version": "2023-06-01"
                },
                method="POST"
            )
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                contents = data.get("content", [])
                if contents:
                    raw_text = contents[0].get("text", "")
                    comments = cls._parse_findings_json(raw_text, default_path)
                    if comments is not None:
                        return comments, f"Anthropic ({model_name})"
        except Exception as e:
            sys.stderr.write(f"Anthropic API request failed: {e}\n")
        return None

    @classmethod
    def _parse_findings_json(cls, raw_text: str, default_path: str) -> Optional[List[ReviewComment]]:
        """Parses LLM JSON output into strict ReviewComment instances."""
        if not raw_text or not raw_text.strip():
            return None

        # Clean markdown codeblocks if model wrapped json in ```json ... ```
        cleaned = raw_text.strip()
        if cleaned.startswith("```"):
            lines = cleaned.splitlines()
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        try:
            data = json.loads(cleaned)
            raw_findings = data.get("findings", [])
            comments: List[ReviewComment] = []
            for item in raw_findings:
                comments.append(ReviewComment(
                    file_path=item.get("file_path", default_path),
                    line_number=int(item.get("line_number", 1)),
                    severity=item.get("severity", "WARNING"),
                    category=item.get("category", "SECURITY"),
                    issue_summary=item.get("issue_summary", ""),
                    detailed_explanation=item.get("detailed_explanation", ""),
                    suggested_diff_fix=item.get("suggested_diff_fix", "")
                ))
            return comments
        except Exception as e:
            logger.warning(f"Failed to parse LLM structured findings JSON: {e}")
            return None
