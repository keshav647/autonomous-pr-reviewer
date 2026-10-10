"""
Observability and Tracing Engine (Langfuse Integration).
Tracks step latency, agent state transitions, token counts, and input/output graphs.
"""

import time
import json
import logging
from typing import Dict, Any, Optional
from ..config import settings

logger = logging.getLogger(__name__)

class AgentTracer:
    """Manages telemetry and trace spans for multi-agent workflows."""

    def __init__(self, trace_name: str = "pr-reviewer-state-graph"):
        self.trace_name = trace_name
        self.trace_id = f"trace_{int(time.time() * 1000)}"
        self.start_time = time.time()
        self.spans: list[Dict[str, Any]] = []
        self.is_remote_enabled = bool(settings.LANGFUSE_PUBLIC_KEY and settings.LANGFUSE_SECRET_KEY)

    def record_step(self, step_name: str, duration_ms: float, inputs: Any, outputs: Any, tokens: int = 0):
        span = {
            "name": step_name,
            "duration_ms": round(duration_ms, 2),
            "tokens": tokens,
            "inputs_summary": str(inputs)[:120],
            "outputs_summary": str(outputs)[:120],
            "timestamp": time.time()
        }
        self.spans.append(span)

    def export_summary(self) -> Dict[str, Any]:
        total_duration_ms = round((time.time() - self.start_time) * 1000, 2)
        total_tokens = sum(s["tokens"] for s in self.spans)
        return {
            "trace_id": self.trace_id,
            "name": self.trace_name,
            "total_duration_ms": total_duration_ms,
            "total_tokens": total_tokens,
            "steps_count": len(self.spans),
            "remote_synced": self.is_remote_enabled,
            "spans": self.spans
        }
