"""FastAPI ASGI application factory and production router wiring."""

import os
from pathlib import Path
from typing import Optional

from ..config import settings
from .routes.health import router as health_router
from .routes.review import router as review_router
from .routes.github import router as github_router

HTML_PATH = Path(__file__).parent.parent / "ui" / "index.html"
STATIC_DIR = Path(__file__).parent.parent / "ui" / "static"

def get_ui_html() -> str:
    """Reads the static UI template."""
    if HTML_PATH.is_file():
        with open(HTML_PATH, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Multi-Agent PR Reviewer UI missing</h1>"

try:
    from fastapi import FastAPI
    from fastapi.responses import HTMLResponse, FileResponse
    from fastapi.staticfiles import StaticFiles
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(
        title="Autonomous Multi-Agent PR Reviewer & Security Auditor",
        description="Production Multi-Agent PR Reviewer and Security Auditor powered by LangGraph, Pydantic v2, and GitHub REST API.",
        version="1.0.0"
    )

    # Enable CORS for local and web tooling
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Register modular API routers
    if health_router:
        app.include_router(health_router)
    if review_router:
        app.include_router(review_router)
    if github_router:
        app.include_router(github_router)

    # Static assets mounting if directory exists
    if STATIC_DIR.is_dir():
        app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

    @app.get("/favicon.ico", include_in_schema=False)
    def serve_favicon():
        logo_path = STATIC_DIR / "logo.png"
        if logo_path.is_file():
            return FileResponse(str(logo_path), media_type="image/png")
        return HTMLResponse(status_code=204)

    @app.get("/", response_class=HTMLResponse)
    @app.get("/ui", response_class=HTMLResponse)
    def serve_dashboard():
        return HTMLResponse(content=get_ui_html())

except ImportError:
    app = None
