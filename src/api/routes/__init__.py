"""API Route modules for Autonomous Multi-Agent PR Reviewer."""

from .health import router as health_router, handle_health
from .review import router as review_router, handle_review
from .github import router as github_router, handle_github_fetch, handle_github_publish

__all__ = [
    "health_router",
    "review_router",
    "github_router",
    "handle_health",
    "handle_review",
    "handle_github_fetch",
    "handle_github_publish",
]
