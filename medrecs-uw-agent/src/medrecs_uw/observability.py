"""Prometheus + OpenTelemetry. Correlation id is propagated to every tool call."""

from __future__ import annotations

import logging
import sys
from contextlib import contextmanager
from typing import Iterator

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor
from opentelemetry.trace import Status, StatusCode
from prometheus_client import Counter, Histogram, Info

from .config import get_settings

logger = logging.getLogger("medrecs_uw")

AGENT_RUNS = Counter(
    "medrecs_agent_runs_total",
    "Agent runs",
    ["agent_id", "status"],
)
AGENT_ERRORS = Counter(
    "medrecs_agent_errors_total",
    "Agent runs ending in error",
    ["agent_id"],
)
API_HITS = Counter(
    "medrecs_api_hits_total",
    "Tool / API hits",
    ["tool_id", "path"],
)
API_ERRORS = Counter(
    "medrecs_api_errors_total",
    "Tool / API errors",
    ["tool_id"],
)
RUN_LATENCY = Histogram(
    "medrecs_agent_run_seconds",
    "Agent wall time",
    ["agent_id"],
)
DUPLICATE_BLOCKS = Counter(
    "medrecs_duplicate_request_blocks_total",
    "Medical-record requests skipped because documents were already received",
)
MANUAL_CHASES = Counter(
    "medrecs_manual_chase_escalations_total",
    "S8 chases escalated because aging thresholds are unknown",
)
BUILD_INFO = Info("medrecs_build", "Workbench identity")
BUILD_INFO.info(
    {
        "product": "life insurance underwriting process",
        "package": "precord-d4fed596",
    }
)

_tracer_ready = False


def setup_tracing() -> None:
    global _tracer_ready
    if _tracer_ready:
        return
    settings = get_settings()
    resource = Resource.create({"service.name": "medrecs-uw-agent"})
    provider = TracerProvider(resource=resource)
    if settings.otlp_endpoint:
        from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

        provider.add_span_processor(
            SimpleSpanProcessor(OTLPSpanExporter(endpoint=settings.otlp_endpoint))
        )
    elif settings.log_sink in {"stdout", "stderr"}:
        provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter(out=sys.stderr)))
    trace.set_tracer_provider(provider)
    _tracer_ready = True


def tracer():
    setup_tracing()
    return trace.get_tracer("medrecs_uw")


@contextmanager
def tool_span(tool_id: str, path: str, correlation_id: str) -> Iterator[None]:
    API_HITS.labels(tool_id=tool_id, path=path.split("?")[0]).inc()
    with tracer().start_as_current_span(f"tool.{tool_id}") as span:
        span.set_attribute("tool.id", tool_id)
        span.set_attribute("http.path", path)
        span.set_attribute("correlation.id", correlation_id)
        try:
            yield
        except Exception as exc:
            API_ERRORS.labels(tool_id=tool_id).inc()
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR))
            raise


def record_run(agent_id: str, status: str) -> None:
    AGENT_RUNS.labels(agent_id=agent_id, status=status).inc()
    if status in {"error", "blocked", "escalated"}:
        AGENT_ERRORS.labels(agent_id=agent_id).inc()
