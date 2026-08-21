"""In-process stand-in for Case Queue Workbench, PolicyCenter, mail, vault, warehouse."""

from __future__ import annotations

import copy
from typing import Any
from urllib.parse import parse_qs, urlparse

from .gateway import Gateway, ToolError


SYNTHETIC_CASES: dict[str, dict[str, Any]] = {
    "UW-REQ-01": {
        "underwriting_case_id": "UW-REQ-01",
        "case": "UW-REQ-01",
        "status": "Referred for medical evidence",
        "aging": "0 days",
        "risk_classification": None,
        "underwriting_decision": None,
        "assigned_underwriter": "Alex Chen",
        "product_type": "Term Life",
        "face_amount": 500_000,
        "applicant_name": "Jordan Hale",
        "attending_physician_statement_required": True,
        "laboratory_report_required": True,
        "documents_received": [],
        "application_received_at": "2026-08-01T09:00:00Z",
        "touches": 1,
    },
    "UW-REQ-02": {
        "underwriting_case_id": "UW-REQ-02",
        "case": "UW-REQ-02",
        "status": "Referred for medical evidence",
        "aging": "3 days",
        "assigned_underwriter": "Alex Chen",
        "product_type": "Term Life",
        "face_amount": 250_000,
        "applicant_name": "Riley Patel",
        "attending_physician_statement_required": True,
        "laboratory_report_required": True,
        "documents_received": ["attending_physician_statement", "laboratory_report"],
        "application_received_at": "2026-08-10T09:00:00Z",
        "touches": 2,
    },
    "UW-CHASE-03": {
        "underwriting_case_id": "UW-CHASE-03",
        "case": "UW-CHASE-03",
        "status": "Pending medical records",
        "aging": "21 days",
        "assigned_underwriter": "Sam Ortiz",
        "product_type": "Term Life",
        "face_amount": 1_000_000,
        "applicant_name": "Morgan Lee",
        "attending_physician_statement_required": True,
        "laboratory_report_required": False,
        "documents_received": [],
        "application_received_at": "2026-07-20T09:00:00Z",
        "touches": 3,
    },
    "UW-MAIL-04": {
        "underwriting_case_id": "UW-MAIL-04",
        "case": "UW-MAIL-04",
        "status": "Awaiting records",
        "aging": "5 days",
        "assigned_underwriter": "Alex Chen",
        "product_type": "Term Life",
        "face_amount": 400_000,
        "applicant_name": "Chris Nguyen",
        "attending_physician_statement_required": True,
        "documents_received": [],
        "inbound_email": {
            "id": "msg-mail-04",
            "subject": "APS timeline for UW-MAIL-04",
            "body": (
                "Confirming case UW-MAIL-04. Attending physician statement "
                "expected in 7 days. Clinic will deliver by 2026-08-28."
            ),
            "from": "agent@broker.example",
        },
        "application_received_at": "2026-08-12T09:00:00Z",
        "touches": 2,
    },
    "UW-MAIL-05": {
        "underwriting_case_id": "UW-MAIL-05",
        "case": "UW-MAIL-05",
        "status": "Awaiting records",
        "aging": "2 days",
        "assigned_underwriter": "Sam Ortiz",
        "applicant_name": "Taylor Brooks",
        "inbound_email": {
            "id": "msg-mail-05",
            "subject": "records coming",
            "body": "Hey, the files are coming soon. Will update later.",
            "from": "agent@broker.example",
        },
        "application_received_at": "2026-08-15T09:00:00Z",
        "touches": 1,
    },
    "UW-VAULT-06": {
        "underwriting_case_id": "UW-VAULT-06",
        "case": "UW-VAULT-06",
        "status": "Awaiting records",
        "aging": "4 days",
        "assigned_underwriter": "Alex Chen",
        "product_type": "Term Life",
        "face_amount": 600_000,
        "applicant_name": "Jamie Cole",
        "laboratory_report_required": True,
        "attending_physician_statement_required": False,
        "documents_received": [],
        "vault_documents": [
            {
                "document_id": "DOC-LAB-06",
                "document_type": "laboratory_report",
                "case_id": "UW-VAULT-06",
                "applicant_name": "Jamie Cole",
                "received_at": "2026-08-18T14:00:00Z",
            }
        ],
        "application_received_at": "2026-08-14T09:00:00Z",
        "touches": 2,
    },
    "UW-VAULT-07": {
        "underwriting_case_id": "UW-VAULT-07",
        "case": "UW-VAULT-07",
        "status": "Awaiting records",
        "aging": "6 days",
        "assigned_underwriter": "Sam Ortiz",
        "applicant_name": "Avery Shah",
        "laboratory_report_required": True,
        "vault_documents": [
            {
                "document_id": "DOC-LAB-07",
                "document_type": "laboratory_report",
                "case_id": "UW-VAULT-07",
                "applicant_name": "Different Person",
                "received_at": "2026-08-18T15:00:00Z",
            }
        ],
        "application_received_at": "2026-08-12T09:00:00Z",
        "touches": 2,
    },
    "UW-BOUND-08": {
        "underwriting_case_id": "UW-BOUND-08",
        "case": "UW-BOUND-08",
        "status": "Bound",
        "aging": "18 days",
        "risk_classification": "Preferred Non-Tobacco",
        "underwriting_decision": "Approve",
        "assigned_underwriter": "Alex Chen",
        "product_type": "Term Life",
        "face_amount": 750_000,
        "applicant_name": "Quinn Adler",
        "policy_bound": True,
        "policy_issued": True,
        "application_received_at": "2026-08-01T09:00:00Z",
        "bound_at": "2026-08-19T09:00:00Z",
        "touches": 4,
        "documents_received": ["attending_physician_statement", "laboratory_report"],
    },
    "UW-DECLINE-09": {
        "underwriting_case_id": "UW-DECLINE-09",
        "case": "UW-DECLINE-09",
        "status": "Decision pending",
        "aging": "12 days",
        "underwriting_decision": "Decline",
        "assigned_underwriter": "Alex Chen",
        "product_type": "Term Life",
        "face_amount": 2_000_000,
        "applicant_name": "Reese Kamara",
        "policy_bound": False,
        "policy_issued": False,
        "application_received_at": "2026-08-05T09:00:00Z",
        "touches": 5,
    },
    "UW-FAIL-10": {
        "underwriting_case_id": "UW-FAIL-10",
        "case": "UW-FAIL-10",
        "status": "Bound",
        "aging": "9 days",
        "underwriting_decision": "Approve",
        "assigned_underwriter": "Sam Ortiz",
        "product_type": "Term Life",
        "face_amount": 300_000,
        "applicant_name": "Harper Diaz",
        "policy_bound": True,
        "policy_issued": True,
        "force_archive_failure": True,
        "application_received_at": "2026-08-10T09:00:00Z",
        "bound_at": "2026-08-19T09:00:00Z",
        "touches": 3,
    },
    "UW-2026-00042": {
        "underwriting_case_id": "UW-2026-00042",
        "case": "UW-2026-00042",
        "status": "Open",
        "aging": "8 days",
        "assigned_underwriter": "Alex Chen",
        "product_type": "Term Life",
        "face_amount": 500_000,
        "applicant_name": "Case Forty Two",
        "attending_physician_statement_required": True,
        "documents_received": [],
        "application_received_at": "2026-08-13T09:00:00Z",
        "touches": 2,
        "notes": "OI-01: status discrepancy recorded; agent does not invent a resolution.",
    },
}


class MockGateway(Gateway):
    def __init__(self) -> None:
        super().__init__()
        self.store: dict[str, dict[str, Any]] = copy.deepcopy(SYNTHETIC_CASES)
        self.mailbox: list[dict[str, Any]] = []
        self.sent_mail: list[dict[str, Any]] = []
        self.vault: dict[str, list[dict[str, Any]]] = {}
        self.archives: dict[str, dict[str, Any]] = {}
        self.notes: list[dict[str, Any]] = []
        self.tickets: list[dict[str, Any]] = []
        self.decisions: dict[str, dict[str, Any]] = {}
        for case_id, case in self.store.items():
            email = case.get("inbound_email")
            if email:
                message = dict(email)
                message.setdefault("case_id", case_id)
                message.setdefault("label", "underwriting")
                self.mailbox.append(message)
            docs = list(case.get("vault_documents") or [])
            if docs:
                self.vault[case_id] = copy.deepcopy(docs)

    def _request(
        self,
        method: str,
        path: str,
        payload: dict[str, Any] | None,
        idempotency_key: str | None,
        correlation_id: str,
        timeout_s: int | None,
    ) -> Any:
        del timeout_s, correlation_id, idempotency_key
        parsed = urlparse(path)
        route = parsed.path
        query = parse_qs(parsed.query)

        if method == "GET" and route == "/pc/cases":
            status = (query.get("status") or ["open"])[0]
            cases = []
            for item in self.store.values():
                current = str(item.get("status") or "")
                if status.lower() == "open" and current.lower() == "closed":
                    continue
                if status.lower() not in {"open", "all"} and current.lower() != status.lower():
                    continue
                cases.append(copy.deepcopy(item))
            return {"cases": cases}

        if method == "GET" and route.startswith("/pc/cases/"):
            case_id = route.split("/")[3]
            if case_id not in self.store:
                raise ToolError(f"case {case_id} not found", 404)
            return copy.deepcopy(self.store[case_id])

        if method == "POST" and route.endswith("/notes"):
            case_id = route.split("/")[3]
            note = dict(payload or {})
            note["underwriting_case_id"] = case_id
            self.notes.append(note)
            self.store.setdefault(case_id, {}).setdefault("workbench_notes", []).append(note)
            return {"recorded": True, "underwriting_case_id": case_id}

        if method == "PATCH" and route.endswith("/workbench"):
            case_id = route.split("/")[3]
            body = payload or {}
            self.store.setdefault(case_id, {}).update(body)
            return {"updated": True, "case": copy.deepcopy(self.store[case_id])}

        if method == "POST" and "/decision" in route:
            case_id = route.split("/")[3]
            if (payload or {}).get("simulate_failure") or self.store.get(case_id, {}).get(
                "force_archive_failure"
            ):
                raise ToolError("PolicyCenter decision API failure", 503)
            self.decisions[case_id] = payload or {}
            self.store.setdefault(case_id, {}).update(
                {k: v for k, v in (payload or {}).items() if k in {"status", "underwriting_decision"}}
            )
            return {"accepted": True, "underwriting_case_id": case_id}

        if method == "PATCH" and route.endswith("/status"):
            case_id = route.split("/")[3]
            status = (payload or {}).get("status")
            self.store.setdefault(case_id, {})["status"] = status
            return {"status": status, "underwriting_case_id": case_id}

        if method == "GET" and route == "/mail/v1/messages":
            case_id = (query.get("caseId") or query.get("case_id") or [None])[0]
            messages = [
                copy.deepcopy(msg)
                for msg in self.mailbox
                if case_id is None or msg.get("case_id") == case_id
            ]
            return {"messages": messages}

        if method == "POST" and route == "/mail/v1/messages":
            message = dict(payload or {})
            self.sent_mail.append(message)
            return {"queued": True, "id": f"out-{len(self.sent_mail):04d}"}

        if method == "GET" and route == "/vault/v1/documents":
            case_id = (query.get("caseId") or query.get("case_id") or [None])[0]
            if not case_id:
                raise ToolError("caseId is required", 422)
            return {"documents": copy.deepcopy(self.vault.get(case_id, []))}

        if method == "GET" and route == "/warehouse/v1/underwriting/cases":
            return {"cases": [copy.deepcopy(row) for row in self.archives.values()]}

        if method == "POST" and route == "/warehouse/v1/underwriting/cases":
            case_id = (payload or {}).get("underwriting_case_id", "unknown")
            if self.store.get(case_id, {}).get("force_archive_failure"):
                raise ToolError("Historical DB write timeout", 504)
            self.archives[case_id] = copy.deepcopy(payload or {})
            if case_id in self.store:
                self.store[case_id]["status"] = (payload or {}).get("status") or "Closed"
            return {"archived": True, "underwriting_case_id": case_id}

        if method == "POST" and route == "/ops/tickets":
            self.tickets.append(payload or {})
            return {"ticket_id": f"IT-{len(self.tickets):04d}"}

        raise ToolError(f"unmapped mock path {method} {path}", 404)


def build_gateway(settings=None) -> Gateway:
    from ..config import get_settings

    cfg = settings or get_settings()
    if cfg.mock_gateway:
        return MockGateway()
    return Gateway(settings=cfg)
