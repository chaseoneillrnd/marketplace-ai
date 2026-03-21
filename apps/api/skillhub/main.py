"""FastAPI application factory."""

from __future__ import annotations

from fastapi import FastAPI

from skillhub.config import Settings
from skillhub.routers import auth, health, skills, social, submissions, users


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )
    app.state.settings = settings
    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(skills.router)
    app.include_router(users.router)
    app.include_router(social.router)
    app.include_router(submissions.router)
    return app


app = create_app()
