"""
State definitions for the Multi-Agent PR Reviewer state machine.
"""

from typing import List, Dict, Any, Optional
try:
    from typing import TypedDict
except ImportError:
    try:
        from typing_extensions import TypedDict
    except ImportError:
        TypedDict = dict  # type: ignore
from ..schemas.models import FileDiff, ReviewComment

class AgentReviewState(TypedDict, total=False):
    """
    State passed through the LangGraph StateMachine.
    """
    pull_request_id: int
    repo_owner: str
    repo_name: str
    diff_text: str
    files: List[FileDiff]
    ast_analyses: Dict[str, Any]
    
    # Optional BYOK API Key supplied via UI/request
    api_key: Optional[str]
    provider: Optional[str]
    model_name: Optional[str]
    
    # Active specialists determined by orchestrator
    active_specialists: List[str]
    
    # Raw findings collected from each specialist
    security_findings: List[ReviewComment]
    performance_findings: List[ReviewComment]
    architecture_findings: List[ReviewComment]
    
    # Synthesized and deduplicated outputs
    synthesized_comments: List[ReviewComment]
    overall_status: str  # "APPROVE", "REQUEST_CHANGES", "COMMENT"
    summary_markdown: str
    total_token_cost_usd: float
    engine_used: str
    
    # Validation and error recovery
    validation_passed: bool
    validation_errors: List[str]
    iteration_count: int
