"""Flask application configuration wrapping pydantic-settings."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.orm import Session


class Settings(BaseSettings):
    """SkillHub configuration — all values overridable via SKILLHUB_* env vars."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # App
    app_name: str = "SkillHub"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://skillhub:skillhub@localhost:5433/skillhub"

    # Auth
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Stub auth
    stub_auth_enabled: bool = False

    # CORS
    cors_origins: list[str] = [
        "http://localhost:5173",
        "http://localhost:5174",
        "http://localhost:3000",
    ]

    # LLM Judge
    llm_router_url: str = ""
    llm_judge_enabled: bool = False

    # Tracing
    otel_traces_enabled: bool = False
    otel_exporter_otlp_endpoint: str = "http://localhost:4317"
    otel_service_name: str = "skillhub-api"


@dataclass
class AppConfig:
    """Application configuration container with test injection support."""

    settings: Settings = field(default_factory=Settings)
    session_factory: Callable[[], Session] | None = None
