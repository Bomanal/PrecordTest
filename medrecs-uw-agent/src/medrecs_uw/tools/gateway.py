"""HTTP client for declared tools. Writes are idempotent."""

from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from typing import Any

import httpx

from ..config import Settings, get_settings
from ..observability import tool_span
from .catalog import TOOL_DEFAULTS


class ToolError(RuntimeError):
    def __init__(self, message: str, status_code: int | None = None) -> None:
        super().__init__(message)
        self.status_code = status_code


@dataclass
class ToolCall:
    tool_id: str
    method: str
    path: str
    direction: str
    payload: dict[str, Any] | None = None
    response: Any = None
    status: str = "ok"
    idempotency_key: str | None = None
    error: str | None = None
    held: bool = False


@dataclass
class Gateway:
    settings: Settings = field(default_factory=get_settings)
    held_writes: list[ToolCall] = field(default_factory=list)
    executed: list[ToolCall] = field(default_factory=list)
    _seen_keys: dict[str, Any] = field(default_factory=dict)
    _token: str | None = None

    def idempotency_key(self, template: str, **parts: Any) -> str:
        payload = parts.pop("payload", {})
        digest = hashlib.sha256(
            json.dumps(payload, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        return template.format(payload_hash=digest, **parts)

    def call(
        self,
        tool_id: str,
        method: str,
        path: str,
        *,
        direction: str,
        payload: dict[str, Any] | None = None,
        idempotency_key: str | None = None,
        hold_write: bool = False,
        correlation_id: str,
        timeout_s: int | None = None,
    ) -> ToolCall:
        record = ToolCall(
            tool_id=tool_id,
            method=method,
            path=path,
            direction=direction,
            payload=payload,
            idempotency_key=idempotency_key,
        )
        if hold_write and direction == "write":
            record.held = True
            record.status = "held_for_checkpoint"
            self.held_writes.append(record)
            self.executed.append(record)
            return record
        if idempotency_key and idempotency_key in self._seen_keys:
            record.response = self._seen_keys[idempotency_key]
            record.status = "idempotent_replay"
            self.executed.append(record)
            return record
        try:
            with tool_span(tool_id, path, correlation_id):
                response = self._request(
                    method, path, payload, idempotency_key, correlation_id, timeout_s
                )
            record.response = response
            if idempotency_key:
                self._seen_keys[idempotency_key] = response
        except ToolError as exc:
            record.status = "error"
            record.error = str(exc)
            self.executed.append(record)
            raise
        self.executed.append(record)
        return record

    def release_held(self, correlation_id: str) -> list[ToolCall]:
        released: list[ToolCall] = []
        pending = list(self.held_writes)
        self.held_writes.clear()
        for call in pending:
            released.append(
                self.call(
                    call.tool_id,
                    call.method,
                    call.path,
                    direction=call.direction,
                    payload=call.payload,
                    idempotency_key=call.idempotency_key,
                    hold_write=False,
                    correlation_id=correlation_id,
                )
            )
        return released

    def drop_held(self) -> None:
        self.held_writes.clear()

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        idempotency_key: str | None,
        correlation_id: str,
        timeout_s: int | None,
    ) -> Any:
        timeout = timeout_s or TOOL_DEFAULTS["timeout_s"]
        headers = {
            self.settings.correlation_id_header: correlation_id,
            "Accept": "application/json",
        }
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key
        token = self._access_token()
        if token:
            headers["Authorization"] = f"Bearer {token}"
        url = f"{self.settings.api_gateway_base_url.rstrip('/')}{path}"
        retry = TOOL_DEFAULTS["retry_policy"]
        delay = retry["initial_delay_ms"] / 1000.0
        last_error: Exception | None = None
        for _attempt in range(retry["max_attempts"]):
            try:
                with httpx.Client(timeout=timeout) as client:
                    response = client.request(method, url, json=payload, headers=headers)
                if response.status_code in {429} or response.status_code >= 500:
                    last_error = ToolError(
                        f"{method} {path} -> {response.status_code}",
                        response.status_code,
                    )
                    time.sleep(delay)
                    delay = min(delay * 2, retry["max_delay_ms"] / 1000.0)
                    continue
                if response.status_code >= 400:
                    raise ToolError(
                        f"{method} {path} -> {response.status_code}: {response.text}",
                        response.status_code,
                    )
                if not response.content:
                    return {}
                return response.json()
            except httpx.TimeoutException as exc:
                last_error = ToolError(f"{method} {path} timed out", None)
                time.sleep(delay)
                delay = min(delay * 2, retry["max_delay_ms"] / 1000.0)
                last_error.__cause__ = exc
        raise last_error or ToolError(f"{method} {path} failed")

    def _access_token(self) -> str | None:
        if not self.settings.oauth_token_url:
            return None
        if self._token:
            return self._token
        with httpx.Client(timeout=15) as client:
            response = client.post(
                self.settings.oauth_token_url,
                data={
                    "grant_type": "client_credentials",
                    "client_id": self.settings.oauth_client_id,
                    "client_secret": self.settings.oauth_client_secret,
                },
            )
            response.raise_for_status()
            self._token = response.json().get("access_token")
        return self._token
