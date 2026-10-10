"""Code review execution endpoints and handlers."""

from typing import Any, Dict, Optional
from ...agents.graph import PRReviewGraph
from ...schemas.models import PRReviewResult

def handle_review(data: Dict[str, Any], headers: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
    """Pure functional handler executing the multi-agent PR review workflow."""
    headers = headers or {}
    diff_text = data.get("diff_text", "")
    pr_id = int(data.get("pull_request_id", 1) or 1)
    
    # Support multiple header/body conventions for API keys
    api_key = (
        data.get("api_key")
        or headers.get("x-api-key")
        or headers.get("x-gemini-api-key")
        or None
    )
    provider = data.get("provider")
    model_name = data.get("model_name")
    repo_owner = data.get("repo_owner", "demo")
    repo_name = data.get("repo_name", "repo")

    result = PRReviewGraph.execute(
        diff_text=diff_text,
        pr_id=pr_id,
        repo_owner=repo_owner,
        repo_name=repo_name,
        api_key=api_key,
        provider=provider,
        model_name=model_name,
    )
    return result.model_dump()

try:
    from fastapi import APIRouter, Request, Header
    from pydantic import BaseModel

    router = APIRouter(prefix="/api/v1", tags=["Review"])

    class DirectReviewRequest(BaseModel):
        diff_text: str
        pull_request_id: Optional[int] = 1
        repo_owner: Optional[str] = "demo"
        repo_name: Optional[str] = "repo"
        api_key: Optional[str] = None
        provider: Optional[str] = None
        model_name: Optional[str] = None

    @router.post("/review", response_model=PRReviewResult)
    def review_diff(payload: DirectReviewRequest, request: Request):
        return handle_review(payload.model_dump(), dict(request.headers))

except ImportError:
    router = None
