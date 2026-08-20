"""Google ADK adapter around the deterministic SecureTerm runtime.

This project runs without Google ADK. Use::

    python -m secureterm_uw serve

``adk web`` / ``adk run`` only work after ``pip install google-adk`` and
should be pointed at this folder::

    adk web adk_app

Do not run ``adk web`` from the repository root — ADK will try to load
``src/secureterm_uw`` as an agent and fail because that package has no
``root_agent``.
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
        "  python -m secureterm_uw serve\n"
        "If you intentionally want the ADK Dev UI, install google-adk in a "
        "separate virtualenv (it can conflict with this project's OpenTelemetry)."
    ) from exc

from secureterm_uw.case_model import Case
from secureterm_uw.runtime import run_agent
from secureterm_uw.tools.mock_policycenter import SYNTHETIC_CASES, build_gateway


def _user_text(ctx: InvocationContext) -> str:
    content = ctx.user_content
    if content is None:
        return ""
    parts = getattr(content, "parts", None) or []
    return "\n".join(str(getattr(part, "text", "") or "") for part in parts).strip()


def _dispatch(message: str) -> dict:
    raw = message.strip()
    if not raw:
        raw = "BLK-01 LUW-FAST-01 s3"
    if raw[0] == "{":
        payload = json.loads(raw)
        agent_id = payload.pop("agent_id", "BLK-01")
        stage = payload.pop("stage", None)
        case = Case.model_validate(payload)
    else:
        tokens = raw.split()
        agent_id = tokens[0] if tokens and tokens[0] in {"BLK-01", "BLK-02"} else "BLK-01"
        rest = tokens[1:] if agent_id == tokens[0] else tokens
        synthetic = rest[0] if rest else "LUW-FAST-01"
        stage = rest[1] if len(rest) > 1 else ("s3" if agent_id == "BLK-01" else None)
        if synthetic not in SYNTHETIC_CASES:
            return {
                "error": f"unknown case {synthetic}",
                "synthetic_cases": sorted(SYNTHETIC_CASES),
                "hint": "Try: BLK-01 LUW-FAST-01 s3",
            }
        case = Case.model_validate(SYNTHETIC_CASES[synthetic])
    return run_agent(agent_id, case, gateway=build_gateway(), stage=stage)


class SecureTermAgent(BaseAgent):
    """Custom ADK agent: no Gemini call. Delegates to the SecureTerm runtime."""

    async def _run_async_impl(self, ctx: InvocationContext) -> AsyncGenerator[Event, None]:
        try:
            output = _dispatch(_user_text(ctx))
            text = json.dumps(output, indent=2, default=str)
        except Exception as exc:  # noqa: BLE001 — surface the failure in the ADK turn
            text = json.dumps({"error": str(exc)}, indent=2)
        yield Event(
            author=self.name,
            content=types.Content(role="model", parts=[types.Part(text=text)]),
        )


root_agent = SecureTermAgent(
    name="secureterm_uw",
    description=(
        "Meridian Life Assurance SecureTerm underwriting workbench "
        "(BLK-01 medical orchestration, BLK-02 rating/referral). "
        "Send `BLK-01 LUW-FAST-01 s3` or a case JSON object."
    ),
)
