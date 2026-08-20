from secureterm_uw.evals.runner import run_evals
from secureterm_uw.tools.mock_policycenter import MockGateway


def test_eval_suite_passes():
    report = run_evals()
    failed = [row for row in report["results"] if not row.get("passed")]
    assert report["passed"], failed


def test_write_idempotency_replays_without_second_create():
    gateway = MockGateway()
    payload = {"tests": ["MER"]}
    key = gateway.idempotency_key(
        "BLK-01:{case_id}:order_medical_tests:{payload_hash}",
        case_id="LUW-FAST-01",
        payload=payload,
    )
    first = gateway.call(
        "order_medical_tests",
        "POST",
        "/submissions/LUW-FAST-01/medical/tests",
        direction="write",
        payload=payload,
        idempotency_key=key,
        correlation_id="c1",
    )
    second = gateway.call(
        "order_medical_tests",
        "POST",
        "/submissions/LUW-FAST-01/medical/tests",
        direction="write",
        payload=payload,
        idempotency_key=key,
        correlation_id="c1",
    )
    assert first.status == "ok"
    assert second.status == "idempotent_replay"
    assert len(gateway.orders) == 1
