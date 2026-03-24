"""FastAPI application factory."""

from __future__ import annotations

import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from skillhub.config import Settings
from skillhub.routers import admin, analytics, auth, exports, feedback, flags, health, review_queue, roadmap, skills, social, submissions, users

logger = logging.getLogger(__name__)


def create_app(settings: Settings | None = None) -> FastAPI:
    """Create and configure the FastAPI application."""
    if settings is None:
        settings = Settings()

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        debug=settings.debug,
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    app.state.settings = settings

    # OpenTelemetry tracing setup
    from skillhub.tracing import setup_tracing

    setup_tracing(settings)

    if settings.otel_traces_enabled:
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor

            FastAPIInstrumentor.instrument_app(app)
            logger.info("FastAPI OpenTelemetry instrumentation applied")
        except Exception:
            logger.warning("Failed to apply FastAPI OpenTelemetry instrumentation", exc_info=True)

        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            from skillhub_db.session import engine

            SQLAlchemyInstrumentor().instrument(engine=engine)
            logger.info("SQLAlchemy OpenTelemetry instrumentation applied")
        except Exception:
            logger.warning("Failed to apply SQLAlchemy OpenTelemetry instrumentation", exc_info=True)

        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor

            HTTPXClientInstrumentor().instrument()
            logger.info("HTTPX OpenTelemetry instrumentation applied")
        except Exception:
            logger.warning("Failed to apply HTTPX OpenTelemetry instrumentation", exc_info=True)

    app.include_router(health.router)
    app.include_router(auth.router)
    app.include_router(skills.router)
    app.include_router(users.router)
    app.include_router(social.router)
    app.include_router(submissions.router)
    app.include_router(flags.router)
    app.include_router(admin.router)
    app.include_router(review_queue.router)
    app.include_router(analytics.router)
    app.include_router(exports.router)
    app.include_router(feedback.router)
    app.include_router(roadmap.router)
    return app


app = create_app()
