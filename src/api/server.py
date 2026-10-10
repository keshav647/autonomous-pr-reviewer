"""Server entrypoint exposing FastAPI ASGI 'app' and native dual-port runner."""

import os
from .app import app, get_ui_html
from .native_server import run_native_server, NativeReviewHandler

__all__ = ["app", "run_native_server", "NativeReviewHandler", "get_ui_html"]

if __name__ == "__main__":
    port = int(os.getenv("PORT", "8000"))
    run_native_server(port=port)
