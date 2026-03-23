"""MCP server configuration via pydantic-settings."""

from __future__ import annotations

from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class MCPSettings(BaseSettings):
    """MCP server settings — all values overridable via SKILLHUB_MCP_* env vars."""

    model_config = SettingsConfigDict(
        env_prefix="SKILLHUB_MCP_", env_file=".env", extra="ignore"
    )

    # API connection
    api_base_url: str = "http://localhost:8000"

    # Skills install directory — matches Claude Code's skill loading path
    skills_dir: str = str(Path.home() / ".claude" / "skills")

    # Server
    host: str = "127.0.0.1"
    port: int = 8001
    debug: bool = False

    # Tracing
    otel_traces_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "skillhub-mcp"
