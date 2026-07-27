"""Runtime configuration for the task backend."""

from __future__ import annotations

import os


class Settings:
    """Read backend configuration from environment variables with local-safe defaults."""

    def __init__(self) -> None:
        """Initialize browser-origin configuration."""
        origins = os.getenv("CORS_ORIGINS", "http://localhost:3000")
        self.cors_origins = [origin.strip() for origin in origins.split(",") if origin.strip()]
