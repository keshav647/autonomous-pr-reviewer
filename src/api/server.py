"""
FastAPI & Native HTTP Web Server for Autonomous Multi-Agent PR Reviewer.
Serves interactive BYOK Web UI and REST API with zero external dependencies.
"""

import sys
import os
import json
import logging
import hmac
import hashlib
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from typing import Dict, Any, Optional

from ..config import settings
from ..schemas.models import PRReviewResult
from ..agents.graph import PRReviewGraph
from ..github.client import GitHubReviewClient

logger = logging.getLogger(__name__)

HTML_PATH = Path(__file__).parent.parent / "ui" / "index.html"

def get_ui_html() -> str:
    """Reads the static UI template."""
    if HTML_PATH.is_file():
        with open(HTML_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Multi-Agent PR Reviewer UI missing</h1>"

# -------------------------------------------------------------
# 1. Native Zero-Dependency HTTP Request Handler
# -------------------------------------------------------------
class NativeReviewHandler(BaseHTTPRequestHandler):
    """Zero-dependency HTTP server handling both UI and JSON API endpoints."""

    def _set_headers(self, status=200, content_type="application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_GET(self):
        if self.path in ("/", "/ui", "/index.html"):
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(get_ui_html().encode("utf-8"))
        elif self.path == "/health":
            self._set_headers(200)
            res = {
                "status": "healthy",
                "service": "pr-reviewer-agent",
                "model": settings.GEMINI_MODEL,
                "byok_ready": True
            }
            self.wfile.write(json.dumps(res).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Not Found"}).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length)

        if self.path == "/api/v1/review":
            try:
                data = json.loads(body.decode("utf-8"))
                diff_text = data.get("diff_text", "")
                pr_id = data.get("pull_request_id", 1)
                byok_key = data.get("api_key") or self.headers.get("x-api-key") or self.headers.get("x-gemini-api-key")
                provider = data.get("provider")
                model_name = data.get("model_name")

                result = PRReviewGraph.execute(
                    diff_text=diff_text,
                    pr_id=pr_id,
                    api_key=byok_key,
                    provider=provider,
                    model_name=model_name
                )
                self._set_headers(200)
                self.wfile.write(json.dumps(result.model_dump()).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))
        elif self.path == "/api/v1/github/fetch":
            try:
                data = json.loads(body.decode("utf-8"))
                repo_input = (data.get("repo") or "").strip()
                pull_number = int(data.get("pull_number", 0) or 0)
                token = data.get("github_token") or self.headers.get("x-github-token") or None

                # Support parsing full GitHub PR URL: https://github.com/owner/repo/pull/123
                if "github.com/" in repo_input:
                    import re
                    m = re.search(r"github\.com/([^/]+)/([^/]+)/pull/(\d+)", repo_input)
                    if m:
                        owner = m.group(1)
                        repo = m.group(2)
                        pull_number = int(m.group(3))
                    else:
                        raise ValueError("Invalid GitHub Pull Request URL. Expected: https://github.com/owner/repo/pull/123")
                elif "/" in repo_input:
                    parts = repo_input.split("/")
                    owner = parts[0].strip()
                    repo = parts[1].strip()
                else:
                    raise ValueError("Repository must be 'owner/repo' or a direct GitHub PR URL.")

                if not pull_number:
                    raise ValueError("Pull Request number must be provided.")

                client = GitHubReviewClient(token=token)
                diff = client.fetch_pr_diff(owner=owner, repo=repo, pull_number=pull_number)
                details = client.get_pr_details(owner=owner, repo=repo, pull_number=pull_number)

                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "diff_text": diff,
                    "owner": owner,
                    "repo": repo,
                    "pull_number": pull_number,
                    "title": details.get("title", f"PR #{pull_number}"),
                    "html_url": details.get("html_url", f"https://github.com/{owner}/{repo}/pull/{pull_number}"),
                    "author": details.get("author", "unknown"),
                    "lines_count": len(diff.splitlines()) if diff else 0,
                }).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        elif self.path == "/api/v1/github/publish":
            try:
                data = json.loads(body.decode("utf-8"))
                owner = data.get("owner", "demo")
                repo = data.get("repo", "repo")
                pull_number = int(data.get("pull_number", 1))
                token = data.get("github_token") or self.headers.get("x-github-token") or None
                commit_id = data.get("commit_id")
                dry_run = bool(data.get("dry_run", not bool(token)))

                review_data = data.get("review_result", {})
                from ..schemas.models import PRReviewResult
                review_obj = PRReviewResult(**review_data)

                client = GitHubReviewClient(token=token)
                resp = client.post_pr_review(
                    owner=owner,
                    repo=repo,
                    pull_number=pull_number,
                    review_result=review_obj,
                    commit_id=commit_id,
                    dry_run=dry_run
                )
                self._set_headers(200)
                self.wfile.write(json.dumps({
                    "success": True,
                    "response": resp,
                    "dry_run": dry_run
                }).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))
        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # Concise logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.command} {self.path} {args[1]}\n")

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

def run_native_server(host: str = "0.0.0.0", port: int = 8000):
    """Starts the native lightweight HTTP server."""
    server_address = (host, port)
    try:
        httpd = ReusableHTTPServer(server_address, NativeReviewHandler)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            alt_port = 8080 if port == 8000 else port + 1
            print(f"Port {port} in use, falling back to port {alt_port}...")
            httpd = ReusableHTTPServer((host, alt_port), NativeReviewHandler)
            port = alt_port
        else:
            raise
    print(f"\n[SERVER] Multi-Agent Reviewer UI & API Server running at:")
    print(f"  \033[1m\033[36mhttp://localhost:{port}\033[0m\n")
    print(f"Features active: [BYOK API Key Support] [Interactive Pipeline Animation] [Zero Cloud Drain]")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()

# -------------------------------------------------------------
# 2. FastAPI ASGI App (for Docker / Production ASGI runtimes)
# -------------------------------------------------------------
try:
    from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
    from fastapi.responses import HTMLResponse, JSONResponse
    from pydantic import BaseModel

    app = FastAPI(
        title="Autonomous Multi-Agent PR Reviewer & Security Auditor",
        version="0.1.0"
    )

    class DirectReviewRequest(BaseModel):
        diff_text: str
        pull_request_id: Optional[int] = 1
        repo_owner: Optional[str] = "demo"
        repo_name: Optional[str] = "repo"
        api_key: Optional[str] = None
        provider: Optional[str] = None
        model_name: Optional[str] = None

    @app.get("/", response_class=HTMLResponse)
    @app.get("/ui", response_class=HTMLResponse)
    def serve_dashboard():
        return HTMLResponse(content=get_ui_html())

    @app.get("/health")
    def health_check():
        return {
            "status": "healthy",
            "service": "pr-reviewer-agent",
            "model": settings.GEMINI_MODEL,
            "byok_ready": True
        }

    @app.post("/api/v1/review", response_model=PRReviewResult)
    def review_diff(payload: DirectReviewRequest):
        result = PRReviewGraph.execute(
            diff_text=payload.diff_text,
            pr_id=payload.pull_request_id or 1,
            repo_owner=payload.repo_owner or "demo",
            repo_name=payload.repo_name or "repo",
            api_key=payload.api_key,
            provider=payload.provider,
            model_name=payload.model_name
        )
        return result

except ImportError:
    app = None

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    run_native_server(port=port)
