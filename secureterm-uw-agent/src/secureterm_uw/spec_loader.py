"""Load the Precord package as the specification authority."""

from __future__ import annotations

import csv
import json
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from .config import get_settings


def precord_root() -> Path:
    root = get_settings().precord_path
    if not root.exists():
        raise FileNotFoundError(f"Precord package not found at {root}")
    return root


def _read_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def _read_json(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as handle:
        return json.load(handle)


def _read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        rows = []
        for raw in reader:
            rows.append({(k or "").strip().strip('"'): (v or "") for k, v in raw.items()})
        return rows


@lru_cache(maxsize=1)
def agents_spec() -> dict[str, Any]:
    return _read_yaml(precord_root() / "spec" / "agents.yaml")


@lru_cache(maxsize=1)
def tools_spec() -> dict[str, Any]:
    return _read_yaml(precord_root() / "spec" / "tools.yaml")


@lru_cache(maxsize=1)
def checkpoints_spec() -> dict[str, Any]:
    return _read_yaml(precord_root() / "spec" / "checkpoints.yaml")


@lru_cache(maxsize=1)
def runtime_spec() -> dict[str, Any]:
    return _read_yaml(precord_root() / "spec" / "runtime.yaml")


@lru_cache(maxsize=1)
def case_schema() -> dict[str, Any]:
    return _read_json(precord_root() / "schemas" / "case.schema.json")


@lru_cache(maxsize=1)
def open_items() -> list[dict[str, str]]:
    return _read_csv(precord_root() / "spec" / "open_items.csv")


@lru_cache(maxsize=1)
def ontology_nodes() -> list[dict[str, str]]:
    return _read_csv(precord_root() / "context" / "ontology_nodes.csv")


@lru_cache(maxsize=1)
def not_automated() -> list[dict[str, str]]:
    return _read_csv(precord_root() / "context" / "not_automated_register.csv")


@lru_cache(maxsize=1)
def agent_specifications() -> list[dict[str, str]]:
    return _read_csv(precord_root() / "context" / "agent_specifications.csv")


def prompt_text(agent_id: str) -> str:
    path = precord_root() / "prompts" / f"{agent_id}.md"
    return path.read_text(encoding="utf-8")


def agent_by_id(agent_id: str) -> dict[str, Any]:
    for agent in agents_spec().get("agents", []):
        if agent.get("agent_id") == agent_id:
            return agent
    raise KeyError(f"Unknown agent_id {agent_id}")


def checkpoint_by_id(checkpoint_id: str) -> dict[str, Any]:
    for checkpoint in checkpoints_spec().get("checkpoints", []):
        if checkpoint.get("checkpoint_id") == checkpoint_id:
            return checkpoint
    raise KeyError(f"Unknown checkpoint_id {checkpoint_id}")
