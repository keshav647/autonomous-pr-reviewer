"""
Structured Data Models and Pydantic Schemas.
Enforces strict schema validation for agent findings and PR review dispatches.
"""

from typing import List, Literal, Optional, Dict, Any

try:
    from pydantic import BaseModel, Field
except ImportError:
    # Lightweight fallback for local environments without pydantic installed
    class BaseModel:
        def __init__(self, **kwargs):
            for k, v in kwargs.items():
                setattr(self, k, v)
        
        def model_dump(self) -> Dict[str, Any]:
            return {
                k: [i.model_dump() if hasattr(i, "model_dump") else i for i in v]
                if isinstance(v, list) else (v.model_dump() if hasattr(v, "model_dump") else v)
                for k, v in self.__dict__.items() if not k.startswith("_")
            }
        
        dict = model_dump
        
        @classmethod
        def model_validate(cls, data: Dict[str, Any]):
            return cls(**data)
            
    def Field(default=None, description=""):
        return default

class DiffLine(BaseModel):
    """Represents a single line inside a diff hunk."""
    line_type: Literal["add", "del", "context"]
    old_line_number: Optional[int] = None
    new_line_number: Optional[int] = None
    content: str

class DiffHunk(BaseModel):
    """A hunk in a unified diff representing a contiguous chunk of edits."""
    old_start: int
    old_lines: int
    new_start: int
    new_lines: int
    header: str
    lines: List[DiffLine] = []

class FileDiff(BaseModel):
    """Parsed git diff representation for a single file."""
    old_path: Optional[str] = None
    new_path: str
    is_new: bool = False
    is_deleted: bool = False
    is_binary: bool = False
    language: str = "unknown"
    hunks: List[DiffHunk] = []
    raw_diff: str = ""

class ReviewComment(BaseModel):
    """Individual line-level review finding with actionable remediation."""
    file_path: str = Field(description="Exact relative file path of the code")
    line_number: int = Field(description="Target line number in the PR diff")
    severity: Literal["CRITICAL", "WARNING", "INFO"] = Field(description="Issue severity level")
    category: Literal["SECURITY", "PERFORMANCE", "ARCHITECTURE", "BUG_RISK"] = Field(
        description="Category classification"
    )
    issue_summary: str = Field(description="One-sentence description of the issue")
    detailed_explanation: str = Field(description="Why this is problematic and how it impacts the system")
    suggested_diff_fix: str = Field(description="Exact git-diff replacement code block")

class PRReviewResult(BaseModel):
    """Final aggregated PR review result validated and ready for GitHub dispatch."""
    pull_request_id: int = Field(description="Target PR ID or sequence number")
    overall_status: Literal["APPROVE", "REQUEST_CHANGES", "COMMENT"] = Field(
        description="Overall review verdict"
    )
    summary_markdown: str = Field(description="Markdown report summarizing the audit findings")
    comments: List[ReviewComment] = Field(default=[], description="List of inline review comments")
    total_token_cost_usd: float = Field(default=0.0, description="Estimated total LLM token cost")
    engine_used: str = Field(default="AST Engine (Offline Fallback)", description="Underlying execution engine")

class PRMetadata(BaseModel):
    """Metadata regarding the Pull Request."""
    repo_owner: str
    repo_name: str
    pr_number: int
    title: str
    author: str
    base_branch: str = "main"
    head_branch: str = "feature"
