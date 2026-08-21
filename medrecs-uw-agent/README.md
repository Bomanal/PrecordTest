# Medical Records UW agentic workbench

Agentic medical-records operations for a **life insurance underwriting process**: initial APS/lab requests, vendor chase, inbound email/vault intake, and post-bind archive.

This folder is the implementation. The specification it implements lives in [`Real-data_E2E_7a8e0d98-d4fed596/precord/`](../Real-data_E2E_7a8e0d98-d4fed596/precord/BUILD.md) and is read at runtime.

## What runs

| Agent | Steps | Autonomy | Review |
| --- | --- | --- | --- |
| **BLK-REQS-CHASE** Underwriting Requirements and Chase Orchestrator | S3, S8 | `draft_for_approval` | CP-BLK-REQS-CHASE, always |
| **BLK-INTAKE-MONITOR** Medical Document Intake & Logging Agent | S5, S9 | `act_with_review` | CP-BLK-INTAKE-MONITOR, 10% sample |
| **BLK-AUTO-ARCHIVE** Automated Case Archiver | S13 | `autonomous` | CP-BLK-AUTO-ARCHIVE, exceptions only |

**Not automated** (by decision, from the agent prompts): S1, S2, S4, S6, S7, S10, S11, S12, S14 — including clinical risk assessment and final `underwriting_decision`.

INT_04 (screen scrape of the case queue for lab verification) has **no tool**. Verification uses INT_06 (document vault) only. See [ASSUMPTIONS.md](ASSUMPTIONS.md).

## Google ADK — do not start the project with `adk`

`spec/runtime.yaml` mentions ADK tracing. This workbench is a **FastAPI app**. It is **not** a Google ADK `adk create` project.

These commands will not start this app:

```bash
adk web
adk run
```

Use the commands below. Optional ADK Dev UI is documented at the bottom.

## Run locally

Python **3.11+**. From the **repository root**:

```bash
cd medrecs-uw-agent

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -e ".[dev]"

python -m pytest
python -m medrecs_uw eval
python -m medrecs_uw cases
python -m medrecs_uw run --agent BLK-REQS-CHASE --synthetic UW-REQ-01 --stage s3
python -m medrecs_uw serve --host 127.0.0.1 --port 8000
```

Always use `python -m …` (not the bare `medrecs-uw` name) if the virtualenv `bin` directory is not on PATH.

### Workbench URLs

After `serve` starts:

| | |
| --- | --- |
| Dashboard + agent tester | http://127.0.0.1:8000/ |
| Health | http://127.0.0.1:8000/health |
| Metrics | http://127.0.0.1:8000/metrics |
| Run agent | `POST /agents/BLK-REQS-CHASE/run` |

Default mode uses in-process mocks for Case Queue Workbench, PolicyCenter, mail, vault, and warehouse. You do **not** need a Gemini or Google API key.

Synthetic case ids: `UW-REQ-01`, `UW-REQ-02`, `UW-CHASE-03`, `UW-MAIL-04`, `UW-MAIL-05`, `UW-VAULT-06`, `UW-VAULT-07`, `UW-BOUND-08`, `UW-DECLINE-09`, `UW-FAIL-10`, `UW-2026-00042`.

### Suggested test path in the UI

1. Open the dashboard, then **Test agents**.
2. Run `BLK-REQS-CHASE` on `UW-REQ-01` / S3 — a request draft is held for approval.
3. Open **Checkpoints** and approve or escalate.
4. Run `BLK-INTAKE-MONITOR` on `UW-MAIL-04` / S5 and `UW-VAULT-06` / S9.
5. Run `BLK-AUTO-ARCHIVE` on `UW-BOUND-08` (archives) and `UW-DECLINE-09` (left open).
6. Open **Evals** and run the suite.

## Optional: Google ADK Dev UI

Use a **separate** virtualenv:

```bash
cd medrecs-uw-agent
python3 -m venv .venv-adk
source .venv-adk/bin/activate
python -m pip install -U pip
python -m pip install -e .
python -m pip install google-adk
adk web adk_app --port 8001
```

Then send `BLK-REQS-CHASE UW-REQ-01 s3`. This adapter calls the same deterministic runtime; it does not call Gemini.

## Layout

```
src/medrecs_uw/     FastAPI workbench, agents, tools, dashboard
adk_app/            optional Google ADK root_agent wrapper
tests/
fixtures/cases/
```
