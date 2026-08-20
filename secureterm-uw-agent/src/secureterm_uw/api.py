"""Integrated agent workbench (Scenario A)."""

from __future__ import annotations

from typing import Any, Literal

from fastapi import FastAPI, HTTPException
from fastapi.responses import HTMLResponse, PlainTextResponse
from prometheus_client import CONTENT_TYPE_LATEST, generate_latest
from pydantic import BaseModel, Field

from .case_model import Case
from .checkpoints import STORE
from .config import get_settings
from .observability import setup_tracing
from .runtime import run_agent
from .tools.mock_policycenter import SYNTHETIC_CASES, build_gateway

setup_tracing()
SETTINGS = get_settings()
GATEWAY = build_gateway(SETTINGS)
APP = FastAPI(
    title="SecureTerm UW agent workbench",
    description=(
        "Meridian Life Assurance Ltd — SecureTerm individual term life underwriting. "
        "Agents BLK-01 and BLK-02 sit behind the API gateway next to Guidewire PolicyCenter."
    ),
    version="0.1.0",
)


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


@APP.get("/health")
def health() -> dict[str, Any]:
    return {
        "status": "ok",
        "agents_live": ["BLK-01", "BLK-02"],
        "environment": SETTINGS.environment,
        "mock_gateway": SETTINGS.mock_gateway,
    }


@APP.get("/metrics")
def metrics() -> PlainTextResponse:
    return PlainTextResponse(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@APP.get("/cases/synthetic")
def synthetic_cases() -> dict[str, Any]:
    return {"cases": list(SYNTHETIC_CASES.values())}


@APP.post("/agents/{agent_id}/run")
def run(agent_id: str, body: RunRequest) -> dict[str, Any]:
    if agent_id not in {"BLK-01", "BLK-02"}:
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


@APP.get("/", response_class=HTMLResponse)
def workbench() -> str:
    return """<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8"/>
  <title>SecureTerm UW workbench</title>
  <style>
    body { font-family: sans-serif; margin: 2rem; background: #f8fafc; color: #0f172a; }
    main { max-width: 960px; margin: auto; }
    pre { background: #0f172a; color: #e2e8f0; padding: 1rem; overflow: auto; }
    button { margin-right: .5rem; padding: .4rem .8rem; }
    label { display: block; margin-top: 1rem; }
  </style>
</head>
<body>
  <main>
    <h1>SecureTerm underwriting workbench</h1>
    <p>BLK-01 Medical Processing &amp; Referral Orchestration · BLK-02 Rating Compliance &amp; Referral Dispatch</p>
    <label>Agent
      <select id="agent"><option>BLK-01</option><option>BLK-02</option></select>
    </label>
    <label>Synthetic case JSON</label>
    <textarea id="payload" rows="16" style="width:100%"></textarea>
    <p>
      <button onclick="loadCases()">Load synthetic cases</button>
      <button onclick="runAgent()">Run agent</button>
      <button onclick="listCp()">Pending checkpoints</button>
    </p>
    <pre id="out"></pre>
  </main>
  <script>
    async function loadCases() {
      const r = await fetch('/cases/synthetic');
      const j = await r.json();
      document.getElementById('payload').value = JSON.stringify(j.cases[0], null, 2);
      document.getElementById('out').textContent = JSON.stringify(j, null, 2);
    }
    async function runAgent() {
      const agent = document.getElementById('agent').value;
      const body = { case: JSON.parse(document.getElementById('payload').value) };
      const r = await fetch('/agents/' + agent + '/run', {
        method: 'POST', headers: {'content-type': 'application/json'}, body: JSON.stringify(body)
      });
      document.getElementById('out').textContent = JSON.stringify(await r.json(), null, 2);
    }
    async function listCp() {
      const r = await fetch('/checkpoints');
      document.getElementById('out').textContent = JSON.stringify(await r.json(), null, 2);
    }
    loadCases();
  </script>
</body>
</html>
"""


def create_app() -> FastAPI:
    return APP
