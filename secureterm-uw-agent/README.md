# SecureTerm UW agentic workbench

Agentic underwriting for **Meridian Life Assurance Ltd** SecureTerm individual term life, integrated with Guidewire PolicyCenter (Scenario A).

This folder is the implementation. The specification it implements lives in [`precord-TestLifeUW SecureTerm UW-candidate/`](../precord-TestLifeUW%20SecureTerm%20UW-candidate/BUILD.md) and is read at runtime.

## What runs

| Agent | Steps | Autonomy | Review |
| --- | --- | --- | --- |
| **BLK-01** Medical Processing & Referral Orchestration | S3, S4, S6 | `act_with_review` | CP-BLK-01, 100% |
| **BLK-02** Rating Compliance & Referral Dispatch | S8, S9 | `draft_for_approval` | CP-BLK-02, always |

**Not automated** (by decision): S2 financial underwriting rules, S11 final risk disposition, S15 policy issue.

## Google ADK — do not start the project with `adk`

The Precord runtime spec mentions ADK tracing. This workbench is still a **FastAPI app**. It is **not** a Google ADK `adk create` project.

These commands are the usual source of “Google ADK” errors and **will not** start this app:

```bash
adk web
adk run
adk run src/secureterm_uw
```

Why they fail:

1. There is no `root_agent` inside `src/secureterm_uw`. ADK walks `__init__.py` packages and errors.
2. A default ADK `LlmAgent` wants `GOOGLE_API_KEY` / Vertex credentials. This runtime does not.
3. `pip install google-adk` in the **same** virtualenv can downgrade OpenTelemetry and break `pytest` / `serve`.

Use the commands in the next section. Optional ADK Dev UI is documented at the bottom.

## Run locally (verified)

Python **3.11+**. From the **repository root**:

### macOS / Linux

```bash
cd secureterm-uw-agent

python3 -m venv .venv
source .venv/bin/activate

python -m pip install -U pip
python -m pip install -e ".[dev]"

python -m pytest
python -m secureterm_uw eval
python -m secureterm_uw cases
python -m secureterm_uw run --agent BLK-01 --synthetic LUW-FAST-01 --stage s3
python -m secureterm_uw serve --host 127.0.0.1 --port 8000
```

Always use `python -m …` (not the bare `secureterm-uw` or `pytest` names). Those console scripts live in `.venv/bin` and are missing from PATH if the venv is not active, or if pip dropped them in `~/.local/bin`.

### Windows (PowerShell)

```powershell
cd secureterm-uw-agent
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -U pip
python -m pip install -e ".[dev]"
python -m pytest
python -m secureterm_uw serve --host 127.0.0.1 --port 8000
```

### If `python -m venv` fails (`ensurepip` / `python3-venv` missing)

```bash
cd secureterm-uw-agent
python3 -m pip install -U pip
python3 -m pip install -e ".[dev]"
python3 -m pytest
python3 -m secureterm_uw serve --host 127.0.0.1 --port 8000
```

Or with [uv](https://docs.astral.sh/uv/):

```bash
cd secureterm-uw-agent
uv venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
uv pip install -e ".[dev]"
python -m pytest
python -m secureterm_uw serve --host 127.0.0.1 --port 8000
```

### Workbench URLs

After `serve` starts:

| | |
| --- | --- |
| UI | http://127.0.0.1:8000/ |
| Health | http://127.0.0.1:8000/health |
| Metrics | http://127.0.0.1:8000/metrics |
| Run agent | `POST /agents/BLK-01/run` |

Stop the server with Ctrl+C.

Default mode uses an in-process PolicyCenter mock. You do **not** need a Gemini or Google API key.

Synthetic case ids: `LUW-FAST-01`, `LUW-REF-04`, `LUW-MER-06`, `LUW-EM-08`, `LUW-EM-OK`, `LUW-1010`.

### If you already installed `google-adk` in this environment

Recreate the venv so OpenTelemetry is not left on the ADK-pinned older SDK:

```bash
deactivate
rm -rf .venv
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -U pip
python -m pip install -e ".[dev]"
```

## Optional: Google ADK Dev UI

Only if you want ADK's own chat UI. Use a **separate** virtualenv.

```bash
cd secureterm-uw-agent
python3 -m venv .venv-adk
source .venv-adk/bin/activate
python -m pip install -U pip
python -m pip install -e .
python -m pip install google-adk
# Point ADK at this folder — not the repo root, not src/secureterm_uw
adk web adk_app --port 8001
```

Then send `BLK-01 LUW-FAST-01 s3`. This adapter calls the same deterministic runtime; it does not call Gemini.

## Open items that still block production limits

See [ASSUMPTIONS.md](ASSUMPTIONS.md). Blocking Precord items are not invented at runtime.

## Layout

```
src/secureterm_uw/     FastAPI workbench, agents, tools
adk_app/               optional Google ADK root_agent wrapper
tests/
```
