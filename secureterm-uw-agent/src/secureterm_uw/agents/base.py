"""Shared agent types and never-automate gates."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

from ..spec_loader import not_automated

Status = Literal[
    "completed",
    "checkpoint_pending",
    "escalated",
    "blocked",
    "open_item",
    "error",
]

NEVER_AUTOMATE_STEPS = {row["step_id"] for row in not_automated()}


class AutomationForbidden(RuntimeError):
    pass


def assert_step_allowed(step_id: str) -> None:
    if step_id in NEVER_AUTOMATE_STEPS:
        raise AutomationForbidden(
            f"Step {step_id} is in not_automated_register.csv and must stay with a person."
        )


@dataclass
class AgentResult:
    agent_id: str
    case_id: str
    status: Status
    step_id: str | None = None
    unknowns: list[str] = field(default_factory=list)
    open_items: list[str] = field(default_factory=list)
    drafts: dict[str, Any] = field(default_factory=dict)
    writes: list[dict[str, Any]] = field(default_factory=list)
    reads: list[dict[str, Any]] = field(default_factory=list)
    checkpoint_id: str | None = None
    shown: dict[str, Any] = field(default_factory=dict)
    escalation_queue: str | None = None
    notes: list[str] = field(default_factory=list)
    eval_trace: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "agent_id": self.agent_id,
            "case_id": self.case_id,
            "status": self.status,
            "step_id": self.step_id,
            "unknowns": self.unknowns,
            "open_items": self.open_items,
            "drafts": self.drafts,
            "writes": self.writes,
            "reads": self.reads,
            "checkpoint_id": self.checkpoint_id,
            "shown": self.shown,
            "escalation_queue": self.escalation_queue,
            "notes": self.notes,
            "eval_trace": self.eval_trace,
        }
