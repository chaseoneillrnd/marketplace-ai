"""Application settings via pydantic-settings."""

from __future__ import annotations

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """SkillHub configuration — all values overridable via SKILLHUB_* env vars."""

    model_config = SettingsConfigDict(env_prefix="SKILLHUB_", env_file=".env")

    # App
    app_name: str = "SkillHub"
    app_version: str = "1.0.0"
    debug: bool = False

    # Database
    database_url: str = "postgresql://skillhub:skillhub@localhost:5432/skillhub"

    # Auth
    jwt_secret: str = "dev-secret-change-me"
    jwt_algorithm: str = "HS256"
    jwt_expire_minutes: int = 60

    # Stub auth
    stub_auth_enabled: bool = True
