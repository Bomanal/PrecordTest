"""Compose agents from spec/agents.yaml and apply checkpoints."""

from __future__ import annotations

import time
import uuid
from typing import Any

from .agents import AGENTS
from .case_model import Case
from .checkpoints import STORE
from .config import get_settings
from .history import record as record_history
from .observability import RUN_LATENCY, record_run, tracer
from .spec_loader import agent_by_id
from .tools.gateway import Gateway
from .tools.mock_systems import build_gateway


def run_agent(
    agent_id: str,
    case: Case,
    *,
    gateway: Gateway | None = None,
    correlation_id: str | None = None,
    stage: str | None = None,
) -> dict[str, Any]:
    spec = agent_by_id(agent_id)
    handler = AGENTS.get(agent_id)
    if handler is None:
        raise KeyError(agent_id)
    cid = correlation_id or str(uuid.uuid4())
    gw = gateway or build_gateway(get_settings())
    started = time.perf_counter()
    with tracer().start_as_current_span(f"agent.{agent_id}") as span:
        span.set_attribute("agent.id", agent_id)
        span.set_attribute("case.id", case.case_id)
        span.set_attribute("correlation.id", cid)
        span.set_attribute("agent.autonomy", spec.get("autonomy", ""))
        result = handler(case, gw, correlation_id=cid, stage=stage)

    elapsed = time.perf_counter() - started
    RUN_LATENCY.labels(agent_id=agent_id).observe(elapsed)
    record_run(agent_id, result.status)

    checkpoint = None
    if result.status == "checkpoint_pending" and spec.get("checkpoints"):
        record = STORE.create(
            spec["checkpoints"][0],
            agent_id,
            result.case_id,
            result.shown,
        )
        checkpoint = {
            "checkpoint_run_id": record.checkpoint_run_id,
            "checkpoint_id": record.checkpoint_id,
            "status": record.status,
            "shown": record.shown,
            "actions": ["approve", "escalate"],
        }

    payload = {
        "correlation_id": cid,
        "autonomy": spec.get("autonomy"),
        "result": result.to_dict(),
        "checkpoint": checkpoint,
        "elapsed_ms": round(elapsed * 1000, 2),
        "held_writes": [
            {
                "tool_id": call.tool_id,
                "path": call.path,
                "payload": call.payload,
                "idempotency_key": call.idempotency_key,
            }
            for call in gw.held_writes
        ],
        "tool_log": [
            {
                "tool_id": call.tool_id,
                "path": call.path,
                "method": call.method,
                "status": call.status,
                "held": call.held,
                "error": call.error,
            }
            for call in gw.executed
        ],
    }
    record_history(
        {
            "agent_id": agent_id,
            "case_id": result.case_id,
            "status": result.status,
            "step_id": result.step_id,
            "correlation_id": cid,
            "elapsed_ms": payload["elapsed_ms"],
        }
    )
    return payload


def run_from_dict(agent_id: str, payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return run_agent(agent_id, Case.model_validate(payload), **kwargs)
