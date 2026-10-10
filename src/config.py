"""
Application Configuration Module.
Loads environment variables and sets defaults for models, rate limits, and server options.
"""

import os
from pathlib import Path
from typing import Optional

def _load_env_file():
    """Manually loads .env file if python-dotenv is not installed."""
    candidates = [
        Path.cwd() / ".env",
        Path(__file__).resolve().parent.parent / ".env",
        Path(__file__).resolve().parent.parent.parent / ".env",
    ]
    for env_path in candidates:
        if env_path.is_file():
            try:
                with open(env_path, "r", encoding="utf-8") as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith("#") and "=" in line:
                            k, v = line.split("=", 1)
                            k = k.strip()
                            v = v.strip().strip("'\"")
                            if k not in os.environ:
                                os.environ[k] = v
                break
            except Exception:
                pass

_load_env_file()

class Settings:
    # LLM Settings
    @property
    def GEMINI_API_KEY(self) -> Optional[str]:
        return os.getenv("GEMINI_API_KEY")

    @property
    def GEMINI_MODEL(self) -> str:
        return os.getenv("GEMINI_MODEL", "gemini-3.8-flash")
    
    # GitHub Settings
    @property
    def GITHUB_TOKEN(self) -> Optional[str]:
        return os.getenv("GITHUB_TOKEN")

    @property
    def GITHUB_WEBHOOK_SECRET(self) -> Optional[str]:
        return os.getenv("GITHUB_WEBHOOK_SECRET")
    
    # Langfuse Tracing
    @property
    def LANGFUSE_PUBLIC_KEY(self) -> Optional[str]:
        return os.getenv("LANGFUSE_PUBLIC_KEY")

    @property
    def LANGFUSE_SECRET_KEY(self) -> Optional[str]:
        return os.getenv("LANGFUSE_SECRET_KEY")

    @property
    def LANGFUSE_HOST(self) -> str:
        return os.getenv("LANGFUSE_HOST", "https://cloud.langfuse.com")
    
    # Runtime & Mock settings
    @property
    def MOCK_MODE(self) -> bool:
        return os.getenv("MOCK_MODE", "false").lower() in ("true", "1", "yes")

    @property
    def DEBUG(self) -> bool:
        return os.getenv("DEBUG", "false").lower() in ("true", "1", "yes")

    @property
    def HOST(self) -> str:
        return os.getenv("HOST", "0.0.0.0")

    @property
    def PORT(self) -> int:
        return int(os.getenv("PORT", "8000"))

settings = Settings()
