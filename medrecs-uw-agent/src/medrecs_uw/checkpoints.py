"""Human checkpoints from spec/checkpoints.yaml."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import Any, Literal

from .spec_loader import checkpoint_by_id
from .tools.gateway import Gateway

Action = Literal["approve", "escalate"]


@dataclass
class CheckpointRecord:
    checkpoint_run_id: str
    checkpoint_id: str
    agent_id: str
    case_id: str
    shown: dict[str, Any]
    status: str = "pending"
    reason_code: str | None = None
    reviewer: str | None = None
    resolved_at: str | None = None
    notes: str | None = None


class CheckpointStore:
    def __init__(self) -> None:
        self._items: dict[str, CheckpointRecord] = {}

    def create(
        self, checkpoint_id: str, agent_id: str, case_id: str, shown: dict[str, Any]
    ) -> CheckpointRecord:
        spec = checkpoint_by_id(checkpoint_id)
        record = CheckpointRecord(
            checkpoint_run_id=str(uuid.uuid4()),
            checkpoint_id=spec["checkpoint_id"],
            agent_id=agent_id,
            case_id=case_id,
            shown=shown,
        )
        self._items[record.checkpoint_run_id] = record
        return record

    def pending(self) -> list[CheckpointRecord]:
        return [item for item in self._items.values() if item.status == "pending"]

    def all(self) -> list[CheckpointRecord]:
        return list(self._items.values())

    def get(self, checkpoint_run_id: str) -> CheckpointRecord:
        return self._items[checkpoint_run_id]

    def resolve(
        self,
        checkpoint_run_id: str,
        action: Action,
        *,
        reason_code: str | None,
        reviewer: str | None,
        gateway: Gateway,
        correlation_id: str,
        notes: str | None = None,
    ) -> CheckpointRecord:
        record = self._items[checkpoint_run_id]
        spec = checkpoint_by_id(record.checkpoint_id)
        allowed = set(spec.get("actions") or [])
        if action not in allowed:
            raise ValueError(f"action {action} is not allowed on {record.checkpoint_id}")
        record.reviewer = reviewer
        record.reason_code = reason_code
        record.notes = notes
        record.resolved_at = datetime.now(UTC).isoformat()
        if action == "approve":
            record.status = "approved"
            gateway.release_held(correlation_id)
        else:
            record.status = "escalated"
            gateway.drop_held()
        return record


STORE = CheckpointStore()
