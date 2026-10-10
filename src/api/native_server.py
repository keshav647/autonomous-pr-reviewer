"""Zero-dependency lightweight HTTP server for local development and offline environments."""

import os
import sys
import json
import logging
import mimetypes
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler
from pathlib import Path
from typing import Dict, Any

from .app import get_ui_html, STATIC_DIR
from .routes.health import handle_health
from .routes.review import handle_review
from .routes.github import handle_github_fetch, handle_github_publish

logger = logging.getLogger(__name__)

class ReusableHTTPServer(HTTPServer):
    allow_reuse_address = True

class NativeReviewHandler(BaseHTTPRequestHandler):
    """Dispatches requests to modular route handlers with zero external dependencies."""

    def _set_headers(self, status: int = 200, content_type: str = "application/json"):
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Headers", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.end_headers()

    def do_OPTIONS(self):
        self._set_headers(204)

    def do_HEAD(self):
        self.do_GET()

    def do_GET(self):
        # 1. UI Root
        if self.path in ("/", "/ui", "/index.html"):
            self._set_headers(200, "text/html; charset=utf-8")
            self.wfile.write(get_ui_html().encode("utf-8"))
            return

        # 2. Static Assets (/static/...)
        if self.path.startswith("/static/"):
            rel_path = self.path[len("/static/"):].split("?")[0]
            target_file = (STATIC_DIR / rel_path).resolve()
            if target_file.is_file() and str(target_file).startswith(str(STATIC_DIR)):
                mime, _ = mimetypes.guess_type(str(target_file))
                self._set_headers(200, mime or "application/octet-stream")
                with open(target_file, "rb") as f:
                    self.wfile.write(f.read())
                return
            self._set_headers(404, "text/plain")
            self.wfile.write(b"Static file not found")
            return

        # 3. Health Check
        if self.path == "/health":
            self._set_headers(200)
            self.wfile.write(json.dumps(handle_health()).encode("utf-8"))
            return

        self._set_headers(404)
        self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def do_POST(self):
        content_length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(content_length) if content_length > 0 else b"{}"

        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            payload = {}

        req_headers = dict(self.headers)

        if self.path == "/api/v1/review":
            try:
                res = handle_review(payload, req_headers)
                self._set_headers(200)
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except Exception as e:
                self._set_headers(500)
                self.wfile.write(json.dumps({"error": str(e)}).encode("utf-8"))

        elif self.path == "/api/v1/github/fetch":
            try:
                res = handle_github_fetch(payload, req_headers)
                self._set_headers(200)
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        elif self.path == "/api/v1/github/publish":
            try:
                res = handle_github_publish(payload, req_headers)
                self._set_headers(200)
                self.wfile.write(json.dumps(res).encode("utf-8"))
            except Exception as e:
                self._set_headers(400)
                self.wfile.write(json.dumps({"success": False, "error": str(e)}).encode("utf-8"))

        else:
            self._set_headers(404)
            self.wfile.write(json.dumps({"error": "Endpoint not found"}).encode("utf-8"))

    def log_message(self, format, *args):
        # Clean formatted logging
        sys.stderr.write(f"[{self.log_date_time_string()}] {self.command} {self.path} {args[1]}\n")


def run_native_server(host: str = "0.0.0.0", port: int = 8000):
    """Starts the native lightweight server with dual-port 8000/8080 listening."""
    server_address = (host, port)
    try:
        httpd = ReusableHTTPServer(server_address, NativeReviewHandler)
    except OSError as e:
        if e.errno == 48:
            alt_port = 8080 if port == 8000 else port + 1
            print(f"Port {port} in use, falling back to port {alt_port}...")
            httpd = ReusableHTTPServer((host, alt_port), NativeReviewHandler)
            port = alt_port
        else:
            raise

    # Also bind secondary port so user can access both http://localhost:8000 and http://localhost:8080
    sec_port = 8080 if port == 8000 else 8000
    try:
        httpd_sec = ReusableHTTPServer((host, sec_port), NativeReviewHandler)
        threading.Thread(target=httpd_sec.serve_forever, daemon=True).start()
        sec_msg = f"  and http://localhost:{sec_port}"
    except Exception:
        sec_msg = ""

    print(f"\n[SERVER] Multi-Agent Reviewer UI & API Server running at:")
    print(f"  \033[1m\033[36mhttp://localhost:{port}\033[0m")
    if sec_msg:
        print(f"  \033[1m\033[36m{sec_msg}\033[0m\n")
    print(f"Features active: [Modular Architecture] [BYOK API Key Support] [Dual-Port Listening]")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nShutting down server...")
        httpd.server_close()
