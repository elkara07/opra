"""OpenTelemetry auto-instrumentation and custom Prometheus metrics."""

from __future__ import annotations

from prometheus_client import Counter, Histogram, Gauge, CollectorRegistry, generate_latest

# ---------------------------------------------------------------------------
# Custom Prometheus Metrics
# ---------------------------------------------------------------------------

REGISTRY = CollectorRegistry()

# Ticket metrics
TICKETS_CREATED = Counter(
    "tickets_created_total",
    "Total tickets created",
    ["tenant", "source", "priority", "type"],
    registry=REGISTRY,
)

SLA_BREACH = Counter(
    "sla_breach_total",
    "Total SLA breaches",
    ["tenant", "priority", "sla_type"],
    registry=REGISTRY,
)

SLA_REMAINING = Gauge(
    "sla_remaining_minutes",
    "Minutes remaining before SLA breach (per active ticket)",
    ["tenant", "priority", "ticket_number"],
    registry=REGISTRY,
)

ESCALATION = Counter(
    "escalation_total",
    "Total escalations triggered",
    ["tenant", "level"],
    registry=REGISTRY,
)

# Voice metrics
VOICE_CALL_DURATION = Histogram(
    "voice_call_duration_seconds",
    "Voice call duration in seconds",
    ["tenant", "status"],
    buckets=[30, 60, 120, 180, 300, 600, 900],
    registry=REGISTRY,
)

VOICE_CALL_COST = Counter(
    "voice_call_cost_total",
    "Voice call cost in USD",
    ["tenant", "provider_type"],
    registry=REGISTRY,
)

# Email metrics
EMAIL_PROCESSED = Counter(
    "email_processed_total",
    "Total emails processed",
    ["tenant", "direction", "action"],
    registry=REGISTRY,
)

# Jira sync metrics
JIRA_SYNC = Counter(
    "jira_sync_total",
    "Total Jira sync operations",
    ["tenant", "direction", "status"],
    registry=REGISTRY,
)

# Active tickets gauge
ACTIVE_TICKETS = Gauge(
    "active_tickets",
    "Number of active (non-closed) tickets",
    ["tenant", "priority"],
    registry=REGISTRY,
)


def get_metrics() -> bytes:
    """Generate Prometheus metrics output."""
    return generate_latest(REGISTRY)


# ---------------------------------------------------------------------------
# OpenTelemetry Setup
# ---------------------------------------------------------------------------

def setup_otel(app_name: str = "callcenter", otlp_endpoint: str | None = None):
    """Initialize OpenTelemetry tracing and instrumentation.

    Call this at application startup. Instruments:
    - FastAPI (HTTP requests)
    - SQLAlchemy (DB queries)
    - httpx (outbound HTTP calls)
    - Celery tasks
    """
    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace.export import BatchSpanProcessor

        resource = Resource.create({"service.name": app_name})
        provider = TracerProvider(resource=resource)

        if otlp_endpoint:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
            provider.add_span_processor(BatchSpanProcessor(exporter))

        trace.set_tracer_provider(provider)

        # Auto-instrument libraries
        try:
            from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
            FastAPIInstrumentor.instrument()
        except ImportError:
            pass

        try:
            from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
            SQLAlchemyInstrumentor().instrument()
        except ImportError:
            pass

        try:
            from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
            HTTPXClientInstrumentor().instrument()
        except ImportError:
            pass

        return provider

    except ImportError:
        # OTel not installed — skip silently
        return None
