"""Health check and service status route."""

from typing import Any, Dict
from ...config import settings

def handle_health() -> Dict[str, Any]:
    """Pure functional handler for health check."""
    return {
        "status": "healthy",
        "service": "pr-reviewer-agent",
        "model": settings.GEMINI_MODEL,
        "byok_ready": True,
    }

try:
    from fastapi import APIRouter
    router = APIRouter(tags=["Health"])

    @router.get("/health")
    def get_health() -> Dict[str, Any]:
        return handle_health()

except ImportError:
    router = None
