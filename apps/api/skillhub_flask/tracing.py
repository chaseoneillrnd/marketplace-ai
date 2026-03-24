"""OpenTelemetry tracing setup with graceful degradation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from opentelemetry import trace

if TYPE_CHECKING:
    from skillhub_flask.config import Settings

logger = logging.getLogger(__name__)

_tracer: trace.Tracer = trace.get_tracer("skillhub")
_initialized: bool = False


def setup_tracing(settings: Settings) -> trace.Tracer:
    """Configure OpenTelemetry tracing if enabled."""
    global _tracer, _initialized  # noqa: PLW0603

    if _initialized:
        return _tracer

    _initialized = True

    if not settings.otel_traces_enabled:
        logger.info("OpenTelemetry tracing is disabled")
        _tracer = trace.get_tracer("skillhub")
        return _tracer

    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": settings.otel_service_name})
        provider = TracerProvider(resource=resource)

        exporter = OTLPSpanExporter(
            endpoint=settings.otel_exporter_otlp_endpoint,
            insecure=True,
        )
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        trace.set_tracer_provider(provider)
        _tracer = trace.get_tracer("skillhub")

        logger.info(
            "OpenTelemetry tracing enabled, exporting to %s",
            settings.otel_exporter_otlp_endpoint,
        )
    except Exception:
        logger.warning("Failed to configure tracing", exc_info=True)
        _tracer = trace.get_tracer("skillhub")

    return _tracer


def get_tracer() -> trace.Tracer:
    """Return the module-level tracer instance."""
    return _tracer
