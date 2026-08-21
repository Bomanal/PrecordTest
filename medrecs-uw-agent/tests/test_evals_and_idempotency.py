from medrecs_uw.evals.runner import run_evals
from medrecs_uw.tools.mock_systems import MockGateway


def test_eval_suite_passes():
    report = run_evals()
    failed = [row for row in report["results"] if not row.get("passed")]
    assert report["passed"], failed


def test_write_idempotency_replays_without_second_create():
    gateway = MockGateway()
    payload = {
        "to": "agent_or_clinic",
        "underwriting_case_id": "UW-REQ-01",
        "requirements": ["attending_physician_statement"],
    }
    key = gateway.idempotency_key(
        "<correlation_id>/T-04",
        correlation_id="c1",
        payload=payload,
    )
    first = gateway.call(
        "T-04",
        "POST",
        "/mail/v1/messages",
        direction="write",
        payload=payload,
        idempotency_key=key,
        correlation_id="c1",
    )
    second = gateway.call(
        "T-04",
        "POST",
        "/mail/v1/messages",
        direction="write",
        payload=payload,
        idempotency_key=key,
        correlation_id="c1",
    )
    assert first.status == "ok"
    assert second.status == "idempotent_replay"
    assert len(gateway.sent_mail) == 1
