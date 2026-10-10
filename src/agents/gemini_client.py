"""
Google Gemini Live API Client.
Provides structured LLM inference via google-genai SDK or direct HTTPS REST interactions.
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

# Structured JSON Schema expected from Gemini for findings
FINDINGS_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "findings": {
            "type": "ARRAY",
            "items": {
                "type": "OBJECT",
                "properties": {
                    "file_path": {"type": "STRING"},
                    "line_number": {"type": "INTEGER"},
                    "severity": {"type": "STRING", "enum": ["CRITICAL", "WARNING", "INFO"]},
                    "category": {"type": "STRING", "enum": ["SECURITY", "PERFORMANCE", "ARCHITECTURE", "BUG_RISK"]},
                    "issue_summary": {"type": "STRING"},
                    "detailed_explanation": {"type": "STRING"},
                    "suggested_diff_fix": {"type": "STRING"}
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

class GeminiReviewClient:
    """Invokes Google Gemini with structured output validation."""

    def __init__(self, api_key: Optional[str] = None, model: Optional[str] = None):
        self.api_key = api_key or settings.GEMINI_API_KEY
        self.model = model or settings.GEMINI_MODEL

    def is_configured(self) -> bool:
        return bool(self.api_key and not settings.MOCK_MODE)

    def analyze_diff(
        self,
        system_prompt: str,
        file_path: str,
        diff_chunk: str,
        ast_context: Dict[str, Any]
    ) -> Optional[List[ReviewComment]]:
        """
        Sends the diff chunk and AST context to Gemini and returns structured ReviewComment models.
        """
        if not self.is_configured():
            return None

        prompt = (
            f"{system_prompt}\n\n"
            f"FILE TARGET: {file_path}\n"
            f"AST SCOPES & FLAGS: {json.dumps(ast_context, indent=2)}\n\n"
            f"GIT DIFF CHUNK:\n```diff\n{diff_chunk}\n```\n\n"
            f"Audit the modified code lines. Return structured JSON matching the findings schema."
        )

        raw_json_str = self._call_gemini_api(prompt)
        if not raw_json_str:
            return None

        try:
            data = json.loads(raw_json_str)
            raw_findings = data.get("findings", [])
            comments = []
            for item in raw_findings:
                comments.append(ReviewComment(
                    file_path=item.get("file_path", file_path),
                    line_number=int(item.get("line_number", 1)),
                    severity=item.get("severity", "WARNING"),
                    category=item.get("category", "SECURITY"),
                    issue_summary=item.get("issue_summary", ""),
                    detailed_explanation=item.get("detailed_explanation", ""),
                    suggested_diff_fix=item.get("suggested_diff_fix", "")
                ))
            return comments
        except Exception as e:
            logger.warning(f"Failed to parse Gemini structured JSON response: {e}")
            return None

    def _call_gemini_api(self, prompt: str) -> Optional[str]:
        """Tries official google-genai SDK first, falls back to direct REST request."""
        # Method 1: Try official google-genai SDK if installed
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            interaction = client.interactions.create(
                model=self.model,
                input=prompt,
                response_format=[{
                    "type": "text",
                    "mime_type": "application/json",
                    "schema": FINDINGS_SCHEMA
                }]
            )
            if interaction and interaction.output_text:
                return interaction.output_text
        except Exception as sdk_err:
            logger.debug(f"google-genai SDK call deferred: {sdk_err}. Falling back to HTTPS REST endpoint.")

        # Method 2: Direct REST request with model fallback
        candidate_models = [self.model, "gemini-2.5-flash", "gemini-2.0-flash", "gemini-1.5-flash"]
        # Deduplicate while preserving order
        unique_models = list(dict.fromkeys(m for m in candidate_models if m))

        for model_name in unique_models:
            url = f"https://generativelanguage.googleapis.com/v1beta/models/{model_name}:generateContent?key={self.api_key}"
            payload = {
                "contents": [{
                    "role": "user",
                    "parts": [{"text": prompt}]
                }],
                "generationConfig": {
                    "responseMimeType": "application/json",
                    "responseSchema": FINDINGS_SCHEMA
                }
            }

            try:
                req = urllib.request.Request(
                    url,
                    data=json.dumps(payload).encode("utf-8"),
                    headers={"Content-Type": "application/json"},
                    method="POST"
                )
                with urllib.request.urlopen(req, timeout=20) as resp:
                    res_data = json.loads(resp.read().decode("utf-8"))
                    candidates = res_data.get("candidates", [])
                    if candidates:
                        parts = candidates[0].get("content", {}).get("parts", [])
                        if parts:
                            text = parts[0].get("text", "")
                            if text:
                                sys.stderr.write(f"✓ Gemini API responded successfully via {model_name}\n")
                                self.model = model_name
                                return text
            except urllib.error.HTTPError as http_err:
                err_msg = http_err.read().decode("utf-8", errors="ignore")
                sys.stderr.write(f"Gemini API model {model_name} returned {http_err.code}: {err_msg[:120]}...\n")
                if http_err.code in (404, 400):
                    continue  # Try next candidate model
                break
            except Exception as e:
                sys.stderr.write(f"Gemini API request failed for {model_name}: {e}\n")
                break

        return None
