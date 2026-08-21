"""Integrated medical-records agent workbench and dashboard."""

from __future__ import annotations

from pathlib import Path
from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest, REGISTRY
from pydantic import BaseModel, Field

from .case_model import Case
from .checkpoints import STORE
from .config import get_settings
from .evals.runner import run_evals
from .history import recent
from .observability import setup_tracing
from .open_items import items as open_item_rows
from .runtime import run_agent
from .spec_loader import agent_by_id, agent_ids, runtime_spec, thresholds
from .tools.catalog import TOOLS, UNAVAILABLE_TOOLS
from .tools.mock_systems import SYNTHETIC_CASES, build_gateway

setup_tracing()
SETTINGS = get_settings()
GATEWAY = build_gateway(SETTINGS)
STATIC_DIR = Path(__file__).resolve().parent / "static"
APP = FastAPI(
    title="Medical Records UW workbench",
    description=(
        "Life insurance underwriting — medical-records chase, intake, and post-bind archive. "
        "Agents BLK-REQS-CHASE, BLK-INTAKE-MONITOR, and BLK-AUTO-ARCHIVE."
    ),
    version="0.1.0",
)

LIVE_AGENTS = agent_ids()


class RunRequest(BaseModel):
    case: dict[str, Any]
    stage: str | None = None
    correlation_id: str | None = None


class ResolveRequest(BaseModel):
    action: Literal["approve", "escalate"]
    reason_code: str | None = None
    reviewer: str = Field(default="underwriter")
    notes: str | None = None
    correlation_id: str | None = None


def _labelled_sum(name: str) -> float:
    total = 0.0
    names = {name, name.removesuffix("_total"), f"{name.removesuffix('_total')}_total"}
    for metric in REGISTRY.collect():
        if metric.name not in names and not metric.name.startswith(name.removesuffix("_total")):
            continue
        for sample in metric.samples:
            if sample.name.endswith("_created") or sample.name.endswith("_sum") or sample.name.endswith("_count") or sample.name.endswith("_bucket"):
                continue
            total += float(sample.value)
    return total


@APP.get("/health")
def health() -> dict[str, Any]:
    agents = []
    for agent_id in LIVE_AGENTS:
        spec = agent_by_id(agent_id)
        agents.append(
            {
                "agent_id": agent_id,
                "name": spec.get("name"),
                "autonomy": spec.get("autonomy"),
                "steps": ", ".join(spec.get("serves_steps") or []),
            }
        )
    return {
        "status": "ok",
        "agents_live": LIVE_AGENTS,
        "agents": agents,
        "environment": SETTINGS.environment,
        "mock_gateway": SETTINGS.mock_gateway,
        "deployment_target": (runtime_spec().get("deployment") or {}).get("target"),
    }


@APP.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@APP.get("/cases/synthetic")
def synthetic_cases() -> dict[str, Any]:
    return {"cases": list(SYNTHETIC_CASES.values())}


@APP.get("/tools")
def list_tools() -> dict[str, Any]:
    return {"tools": TOOLS, "unavailable": UNAVAILABLE_TOOLS}


@APP.get("/open-items")
def list_open_items() -> dict[str, Any]:
    return {"items": open_item_rows()}


@APP.get("/dashboard/history")
def dashboard_history() -> dict[str, Any]:
    return {"runs": recent()}


@APP.get("/dashboard/kpis")
def dashboard_kpis() -> dict[str, Any]:
    runs = _labelled_sum("medrecs_agent_runs")
    errors = _labelled_sum("medrecs_agent_errors")
    hits = _labelled_sum("medrecs_api_hits")
    api_errors = _labelled_sum("medrecs_api_errors")
    error_rate = (errors / runs * 100.0) if runs else 0.0
    api_live = 100.0 if hits == 0 else max(0.0, 100.0 - (api_errors / hits * 100.0))
    alerts: list[str] = []
    if error_rate > SETTINGS.error_rate_alert_percent:
        alerts.append(
            f"Agent error rate {error_rate:.2f}% exceeds {SETTINGS.error_rate_alert_percent:.0f}% guardrail."
        )
    if hits and api_live < SETTINGS.api_health_alert_percent:
        alerts.append(
            f"API live status {api_live:.2f}% is below {SETTINGS.api_health_alert_percent:.0f}% guardrail."
        )
    cards = [
        {"label": "Agents live", "value": len(LIVE_AGENTS), "hint": "BLK-REQS-CHASE, BLK-INTAKE-MONITOR, BLK-AUTO-ARCHIVE"},
        {"label": "Agent runs", "value": int(runs), "hint": "inputs processed this process"},
        {"label": "Error rate", "value": f"{error_rate:.2f}%", "hint": "alert > 2%"},
        {"label": "API hits", "value": int(hits), "hint": "tool calls"},
        {"label": "API live", "value": f"{api_live:.1f}%", "hint": "alert < 99%"},
        {
            "label": "Dup requests blocked",
            "value": int(_labelled_sum("medrecs_duplicate_request_blocks")),
            "hint": "KPI_P11",
        },
        {
            "label": "Manual chase escalations",
            "value": int(_labelled_sum("medrecs_manual_chase_escalations")),
            "hint": "aging threshold unknown",
        },
        {"label": "Monitor KPIs", "value": len(thresholds()), "hint": "gates are empty — not invented"},
    ]
    return {"cards": cards, "alerts": alerts, "thresholds": thresholds()}


@APP.post("/agents/{agent_id}/run")
def run(agent_id: str, body: RunRequest) -> dict[str, Any]:
    if agent_id not in LIVE_AGENTS:
        raise HTTPException(404, f"unknown agent {agent_id}")
    case = Case.model_validate(body.case)
    return run_agent(
        agent_id,
        case,
        gateway=GATEWAY,
        correlation_id=body.correlation_id,
        stage=body.stage,
    )


@APP.get("/checkpoints")
def list_checkpoints() -> dict[str, Any]:
    return {
        "pending": [
            {
                "checkpoint_run_id": item.checkpoint_run_id,
                "checkpoint_id": item.checkpoint_id,
                "agent_id": item.agent_id,
                "case_id": item.case_id,
                "shown": item.shown,
                "status": item.status,
            }
            for item in STORE.pending()
        ]
    }


@APP.post("/checkpoints/{checkpoint_run_id}")
def resolve_checkpoint(checkpoint_run_id: str, body: ResolveRequest) -> dict[str, Any]:
    try:
        record = STORE.resolve(
            checkpoint_run_id,
            body.action,
            reason_code=body.reason_code,
            reviewer=body.reviewer,
            gateway=GATEWAY,
            correlation_id=body.correlation_id or checkpoint_run_id,
            notes=body.notes,
        )
    except KeyError as exc:
        raise HTTPException(404, "checkpoint not found") from exc
    except ValueError as exc:
        raise HTTPException(400, str(exc)) from exc
    return {
        "checkpoint_run_id": record.checkpoint_run_id,
        "status": record.status,
        "reason_code": record.reason_code,
        "reviewer": record.reviewer,
    }


@APP.post("/evals/run")
def evals_run() -> dict[str, Any]:
    return run_evals()


@APP.get("/", response_class=HTMLResponse)
def workbench() -> str:
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


def create_app() -> FastAPI:
    return APP
