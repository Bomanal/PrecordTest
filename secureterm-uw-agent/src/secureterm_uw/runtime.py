"""Compose agents from spec/agents.yaml and apply checkpoints."""

from __future__ import annotations

import time
import uuid
from typing import Any

from .agents import run_blk01, run_blk02
from .case_model import Case
from .checkpoints import STORE
from .config import get_settings
from .observability import RUN_LATENCY, record_run, tracer
from .spec_loader import agent_by_id
from .tools.gateway import Gateway
from .tools.mock_policycenter import build_gateway


def run_agent(
    agent_id: str,
    case: Case,
    *,
    gateway: Gateway | None = None,
    correlation_id: str | None = None,
    stage: str | None = None,
) -> dict[str, Any]:
    spec = agent_by_id(agent_id)
    cid = correlation_id or str(uuid.uuid4())
    gw = gateway or build_gateway(get_settings())
    started = time.perf_counter()
    with tracer().start_as_current_span(f"agent.{agent_id}") as span:
        span.set_attribute("agent.id", agent_id)
        span.set_attribute("case.id", case.case_identifier or "")
        span.set_attribute("correlation.id", cid)
        span.set_attribute("agent.autonomy", spec.get("autonomy", ""))
        if agent_id == "BLK-01":
            result = run_blk01(case, gw, correlation_id=cid, stage=stage)
        elif agent_id == "BLK-02":
            result = run_blk02(case, gw, correlation_id=cid)
        else:
            raise KeyError(agent_id)

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
    return {
        "correlation_id": cid,
        "autonomy": spec.get("autonomy"),
        "result": result.to_dict(),
        "checkpoint": checkpoint,
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
                "status": call.status,
                "held": call.held,
                "error": call.error,
            }
            for call in gw.executed
        ],
    }


def run_from_dict(agent_id: str, payload: dict[str, Any], **kwargs: Any) -> dict[str, Any]:
    return run_agent(agent_id, Case.model_validate(payload), **kwargs)
