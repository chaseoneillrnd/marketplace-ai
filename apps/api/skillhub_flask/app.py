"""Flask application factory using APIFlask."""

from __future__ import annotations

import logging

from apiflask import APIFlask
from flask_cors import CORS

from skillhub_flask.auth import register_auth
from skillhub_flask.config import AppConfig
from skillhub_flask.db import init_db
from skillhub_flask.tracing import setup_tracing

logger = logging.getLogger(__name__)


def create_app(config: AppConfig | None = None) -> APIFlask:
    """Create and configure the Flask application."""
    config = config or AppConfig()
    settings = config.settings

    app = APIFlask(
        __name__,
        title=settings.app_name,
        version=settings.app_version,
    )
    app.config["TESTING"] = settings.debug

    # Store typed settings on extensions (not app.config — preserves type safety)
    app.extensions["settings"] = settings

    # CORS
    CORS(
        app,
        origins=settings.cors_origins,
        supports_credentials=True,
    )

    # Database
    init_db(app, config)

    # Auth (before_request with PUBLIC_ENDPOINTS)
    register_auth(app)

    # Tracing
    setup_tracing(settings)
    if settings.otel_traces_enabled:
        try:
            from opentelemetry.instrumentation.flask import FlaskInstrumentor

            FlaskInstrumentor().instrument_app(app)
            logger.info("Flask OpenTelemetry instrumentation applied")
        except Exception:
            logger.warning("Failed to apply Flask OTel instrumentation", exc_info=True)

    # Register blueprints
    from skillhub_flask.blueprints.health import bp as health_bp

    app.register_blueprint(health_bp)

    return app
