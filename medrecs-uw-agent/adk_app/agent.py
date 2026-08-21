"""Google ADK adapter around the deterministic medical-records runtime.

This project runs without Google ADK. Use::

    python -m medrecs_uw serve

``adk web`` / ``adk run`` only work after ``pip install google-adk`` and
should be pointed at this folder::

    adk web adk_app
"""

from __future__ import annotations

import json
from collections.abc import AsyncGenerator

try:
    from google.adk.agents import BaseAgent, InvocationContext
    from google.adk.events import Event
    from google.genai import types
except ImportError as exc:  # pragma: no cover
    raise ImportError(
        "Google ADK is not required to run this project.\n"
        "Start the workbench with:\n"
        "  python -m medrecs_uw serve\n"
        "If you intentionally want the ADK Dev UI, install google-adk in a "
        "separate virtualenv (it can conflict with this project's OpenTelemetry)."
    ) from exc

from medrecs_uw.case_model import Case
from medrecs_uw.runtime import run_agent
from medrecs_uw.spec_loader import agent_ids
from medrecs_uw.tools.mock_systems import SYNTHETIC_CASES, build_gateway

AGENTS = set(agent_ids())


def _user_text(ctx: InvocationContext) -> str:
    content = ctx.user_content
    if content is None:
        return ""
    parts = getattr(content, "parts", None) or []
    return "\n".join(str(getattr(part, "text", "") or "") for part in parts).strip()


def _dispatch(message: str) -> dict:
    raw = message.strip()
    if not raw:
        raw = "BLK-REQS-CHASE UW-REQ-01 s3"
    if raw[0] == "{":
        payload = json.loads(raw)
        agent_id = payload.pop("agent_id", "BLK-REQS-CHASE")
        stage = payload.pop("stage", None)
        case = Case.model_validate(payload)
    else:
        tokens = raw.split()
        agent_id = tokens[0] if tokens and tokens[0] in AGENTS else "BLK-REQS-CHASE"
        rest = tokens[1:] if tokens and tokens[0] == agent_id else tokens
        synthetic = rest[0] if rest else "UW-REQ-01"
        stage = rest[1] if len(rest) > 1 else None
        if synthetic not in SYNTHETIC_CASES:
            return {
                "error": f"unknown case {synthetic}",
                "synthetic_cases": sorted(SYNTHETIC_CASES),
                "hint": "Try: BLK-REQS-CHASE UW-REQ-01 s3",
            }
        case = Case.model_validate(SYNTHETIC_CASES[synthetic])
    return run_agent(agent_id, case, gateway=build_gateway(), stage=stage)


class MedrecsAgent(BaseAgent):
    """Custom ADK agent: no Gemini call. Delegates to the deterministic runtime."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        try:
            output = _dispatch(_user_text(ctx))
            text = json.dumps(output, indent=2, default=str)
        except Exception as exc:  # noqa: BLE001
            text = json.dumps({"error": str(exc)}, indent=2)
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=text)]),
        )


root_agent = MedrecsAgent(
    name="medrecs_uw",
    description=(
        "Medical-records underwriting workbench "
        "(BLK-REQS-CHASE, BLK-INTAKE-MONITOR, BLK-AUTO-ARCHIVE). "
        "Send `BLK-REQS-CHASE UW-REQ-01 s3` or a case JSON object."
    ),
)
