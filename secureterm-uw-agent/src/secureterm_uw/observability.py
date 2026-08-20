"""Prometheus + OpenTelemetry. Correlation id is propagated to every tool call."""

from __future__ import annotations

import logging
import sys
from contextlib import contextmanager
from typing import Iterator

from prometheus_client import Counter, Histogram, Info
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, ConsoleSpanExporter
from opentelemetry.trace import Status, StatusCode

from .config import get_settings

logger = logging.getLogger("secureterm_uw")

AGENT_RUNS = Counter(
    "secureterm_agent_runs_total",
    "Agent runs",
    ["agent_id", "status"],
)
AGENT_ERRORS = Counter(
    "secureterm_agent_errors_total",
    "Agent runs ending in error",
    ["agent_id"],
)
API_HITS = Counter(
    "secureterm_api_hits_total",
    "Tool / API hits",
    ["tool_id", "path"],
)
RUN_LATENCY = Histogram(
    "secureterm_agent_run_seconds",
    "Agent wall time",
    ["agent_id"],
)
BUILD_INFO = Info("secureterm_build", "Workbench identity")
BUILD_INFO.info({"product": "SecureTerm", "carrier": "Meridian Life Assurance Ltd"})

_tracer_ready = False


def setup_tracing() -> None:
    global _tracer_ready
    if _tracer_ready:
        return
    settings = get_settings()
    resource = Resource.create({"service.name": "secureterm-uw-agent"})
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
    return trace.get_tracer("secureterm_uw")


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
            span.record_exception(exc)
            span.set_status(Status(StatusCode.ERROR))
            raise


def record_run(agent_id: str, status: str) -> None:
    AGENT_RUNS.labels(agent_id=agent_id, status=status).inc()
    if status in {"error", "blocked", "escalated"}:
        AGENT_ERRORS.labels(agent_id=agent_id).inc()
