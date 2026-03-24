"""Flask application factory using APIFlask."""

from __future__ import annotations

import logging

from apiflask import APIFlask
from flask import jsonify
from flask_cors import CORS
from pydantic import ValidationError

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
    from skillhub_flask.auth import PUBLIC_ENDPOINTS
    from skillhub_flask.blueprints.health import bp as health_bp

    app.register_blueprint(health_bp)

    # Auth blueprint (always registered — /auth/me, OAuth placeholders)
    from skillhub_flask.blueprints.auth import bp as auth_bp

    app.register_blueprint(auth_bp)
    PUBLIC_ENDPOINTS.update({
        "auth.oauth_redirect",
        "auth.oauth_callback",
    })

    # Stub auth (conditional — only when stub_auth_enabled)
    if settings.stub_auth_enabled:
        from skillhub_flask.blueprints.stub_auth import bp as stub_auth_bp

        app.register_blueprint(stub_auth_bp)
        PUBLIC_ENDPOINTS.update({
            "stub_auth.login",
            "stub_auth.list_dev_users",
        })
        logger.warning("STUB AUTH ENABLED — NOT FOR PRODUCTION")
    else:
        logger.info("Stub auth disabled")

    # ── Core Domain Blueprints (Phase 3) ──────────────────────────────
    from skillhub_flask.blueprints.skills import bp as skills_bp
    from skillhub_flask.blueprints.users import bp as users_bp
    from skillhub_flask.blueprints.social import bp as social_bp
    from skillhub_flask.blueprints.submissions import bp as submissions_bp
    from skillhub_flask.blueprints.flags import bp as flags_bp
    from skillhub_flask.blueprints.feedback import bp as feedback_bp
    from skillhub_flask.blueprints.roadmap import bp as roadmap_bp

    app.register_blueprint(skills_bp)
    app.register_blueprint(users_bp)
    app.register_blueprint(social_bp)
    app.register_blueprint(submissions_bp)
    app.register_blueprint(flags_bp)
    app.register_blueprint(feedback_bp)
    app.register_blueprint(roadmap_bp)

    # Public endpoints for core domain
    PUBLIC_ENDPOINTS.update({
        "skills.list_skills",
        "skills.list_categories",
        "skills.get_skill",
        "skills.get_version",
        "skills.get_latest_version",
        "flags.list_flags",
        "roadmap.get_changelog",
        "feedback.list_public_feedback",
    })

    # ── Admin Blueprints (Phase 4) ────────────────────────────────────
    from skillhub_flask.blueprints.admin import bp as admin_bp
    from skillhub_flask.blueprints.analytics import bp as analytics_bp
    from skillhub_flask.blueprints.exports import bp as exports_bp
    from skillhub_flask.blueprints.review_queue import bp as review_queue_bp

    app.register_blueprint(admin_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(exports_bp)
    app.register_blueprint(review_queue_bp)

    # Register DivisionRestrictedError handler
    from skillhub_flask.validation import DivisionRestrictedError

    @app.errorhandler(DivisionRestrictedError)
    def handle_division_restricted(e: DivisionRestrictedError) -> tuple:
        return {"detail": {"error": "division_restricted"}}, 403

    @app.errorhandler(ValidationError)
    def handle_validation_error(e: ValidationError) -> tuple:
        return jsonify({"detail": e.errors(include_url=False)}), 422

    # Divisions reference endpoint
    from skillhub_flask.blueprints.divisions import bp as divisions_bp

    app.register_blueprint(divisions_bp)
    PUBLIC_ENDPOINTS.add("divisions.list_divisions")

    return app
