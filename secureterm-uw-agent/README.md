# SecureTerm UW agentic workbench

Agentic underwriting for **Meridian Life Assurance Ltd** SecureTerm individual term life, integrated with Guidewire PolicyCenter (Scenario A).

This folder is the implementation. The specification it implements lives in [`precord-TestLifeUW SecureTerm UW-candidate/`](../precord-TestLifeUW%20SecureTerm%20UW-candidate/BUILD.md) and is read at runtime. Where this code needs a name, it uses the canonical term in `context/ontology_nodes.csv`.

## What runs

| Agent | Steps | Autonomy | Review |
| --- | --- | --- | --- |
| **BLK-01** Medical Processing & Referral Orchestration | S3, S4, S6 | `act_with_review` | CP-BLK-01, 100% |
| **BLK-02** Rating Compliance & Referral Dispatch | S8, S9 | `draft_for_approval` | CP-BLK-02, always |

Sub-agents are sequential as declared in `spec/agents.yaml`:

- BLK-01.1 Medical Requirements Evaluator — live medical-grid lookup and test order
- BLK-01.2 Early Referral Formatter — provisional Atlas Re summary (draft only; no dispatch endpoint)
- BLK-01.3 Clinical Evidence Ingestion & Validator — MER parse + deterministic BMI
- BLK-02.1 Rating Compliance Auditor — VAL-03-01 override-reason gate
- BLK-02.2 Reinsurance Referral Dispatcher — treaty-limit read + facultative package

**Not automated** (by decision): S2 financial underwriting rules, S11 final risk disposition, S15 policy issue.

## Rules this build follows

- All arithmetic (BMI, Extra Mortality parse, unit conversion) is deterministic Python, never a model call.
- Every write tool is idempotent (`Idempotency-Key`).
- Writes are held until the checkpoint is approved.
- Values listed in `spec/open_items.csv` are not inferred. The runtime stops and records the item.
- IP_05 has no endpoint: provisional Atlas Re dispatch is stored as a draft.

## Run locally

```bash
cd secureterm-uw-agent
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[dev]"
pytest
secureterm-uw eval
secureterm-uw run --agent BLK-01 --synthetic LUW-FAST-01 --stage s3
secureterm-uw serve
```

Workbench: http://127.0.0.1:8000  
Health: `GET /health`  
Metrics: `GET /metrics` (Prometheus)

Default mode uses an in-process PolicyCenter mock (`SECURETERM_MOCK_GATEWAY=true`). Point `SECURETERM_API_GATEWAY_BASE_URL` and OAuth settings at the client gateway to run against a real estate.

## Open items that still block production limits

These are carried, not filled in. See [ASSUMPTIONS.md](ASSUMPTIONS.md).

| ID | Subject | Runtime behaviour |
| --- | --- | --- |
| OI-01 | Retention Limit for Atlas Re | Treaty-limits tool is called; a blank limit is a halt |
| OI-02 | Non-Medical Limit bands | Grid is queried; mock bands are labelled synthetic |
| OI-03 | Referral sequencing | Uses the reimagined graph: S3 → S4 then S5 |
| OI-04 | LUW-1010 Sum Assured conflict | Conflicting figures escalate; no value is chosen |
| OI-05 | AHT discrepancy | Not used in agent logic |
| IP_05 / HR-306 | Provisional referral endpoint | Draft only |

## Observability

Prometheus counters/histograms plus OpenTelemetry spans on every agent run and tool call. The inbound `x-correlation-id` header is propagated to gateway requests. PHI and financial evidence are not logged in full; cached case payloads are process-local and dropped when the process exits.

## Layout

```
src/secureterm_uw/
  agents/          BLK-01, BLK-02, MER parser
  arithmetic/      BMI and Extra Mortality
  tools/           gateway, mock PolicyCenter, tool catalog
  checkpoints.py   CP-BLK-01 / CP-BLK-02
  runtime.py       composition + hold-until-approve
  api.py           FastAPI workbench
  evals/           EC-01, EC-02, VAL-02-01, VAL-03-01
```
