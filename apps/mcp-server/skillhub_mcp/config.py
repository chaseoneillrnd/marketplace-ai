"""MCP server configuration via pydantic-settings."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    """MCP server settings — all values overridable via SKILLHUB_MCP_* env vars."""

    model_config = SettingsConfigDict(env_prefix="SKILLHUB_MCP_", env_file=".env")

    # API connection
    api_base_url: str = "http://localhost:8000"

    # Skills install directory
    skills_dir: str = str(Path.home() / ".local" / "share" / "claude" / "skills")

    # Server
    host: str = "127.0.0.1"
    port: int = 8001
    debug: bool = False
