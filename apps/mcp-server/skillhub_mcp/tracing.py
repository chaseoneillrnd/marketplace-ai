"""OpenTelemetry tracing setup with graceful degradation."""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from opentelemetry import trace

if TYPE_CHECKING:
    from skillhub_mcp.config import MCPSettings

logger = logging.getLogger(__name__)

_SERVICE_TRACER_NAME = "skillhub-mcp"


def setup_tracing(settings: MCPSettings) -> trace.Tracer:
    """Configure OpenTelemetry tracing if enabled.

    If tracing is disabled or Jaeger is unreachable, the server continues
    normally with a no-op tracer.
    """
    if not settings.otel_traces_enabled:
        logger.info("OpenTelemetry tracing is disabled")
        return trace.get_tracer(_SERVICE_TRACER_NAME)

    try:
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import (
            OTLPSpanExporter,
        )
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": settings.otel_service_name})
        provider = TracerProvider(resource=resource)

        exporter = OTLPSpanExporter(endpoint=settings.otel_exporter_otlp_endpoint)
        provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)
        logger.info(
            "OpenTelemetry tracing enabled, exporting to %s",
            settings.otel_exporter_otlp_endpoint,
        )
    except Exception:
        logger.warning(
            "Failed to initialize OpenTelemetry exporter — tracing will be no-op",
            exc_info=True,
        )

    return trace.get_tracer(_SERVICE_TRACER_NAME)
