# Assumptions and deviations

BUILD.md: a value in `spec/open_items.csv` is not inferred. No stack was chosen in the Precord package; the user asked for a runnable solution plus a dashboard, so this build follows the sibling FastAPI workbench pattern already in the repository.

`context/` is listed in BUILD.md and `manifest.json` but is **not shipped** in `Real-data_E2E_7a8e0d98-d4fed596/precord`. Ontology names come from `schemas/case.schema.json` and the prompt domain packs. The never-automate set comes from the “Never automate these” sections in the three agent prompts.

## Open items — not invented

No row in `spec/open_items.csv` is marked `blocking`. Non-blocking items are carried as follows:

| Item | What was needed | What this build does |
| --- | --- | --- |
| HR-306:INT_04 | Screen-scrape tool on the case queue for lab verification | **No tool.** Vault verification uses INT_06 (`T-05`). |
| Q1 | Cloud environment and region | `spec/runtime.yaml` `deployment.target` stays `unknown`. |
| Q4 | Security / compliance controls | Guardrails from `runtime.yaml` only: drafted emails always reviewed; extraction failures go to the workbench; autonomous execution is archive-only; alerts at 2% error rate and 99% API live status. |
| Q5 | Telemetry stack | Dismissed in the register. Prometheus + OpenTelemetry are used because `runtime.yaml` asks for ADK-style traces with a correlation id. |
| OI-01 … OI-06 | Synthesis gaps (status discrepancy, initiator of records request, activity list, field name for policy value, …) | Not filled in. Agents report unknowns and escalate. |

## Stated (non-inferred) behaviour

| Value | Use | Source |
| --- | --- | --- |
| Aging chase threshold | S8 follow-up | Prompt: unknown — escalate, do not invent a rule. S7 stays human. |
| Review 10% | CP-BLK-INTAKE-MONITOR | `spec/checkpoints.yaml` |
| Always review | CP-BLK-REQS-CHASE | `spec/checkpoints.yaml` + `draft_for_approval` |
| Exception review | CP-BLK-AUTO-ARCHIVE | `spec/checkpoints.yaml` |
| Status `In Review` | Successful vault match | Prompt BLK-INTAKE-MONITOR |
| Status `Closed` | Successful bind archive | Prompt BLK-AUTO-ARCHIVE (recorded on INT_07 payload; INT_03 is not on this agent) |
| Status `Manual Record Request Required` | Chase / request failure | Prompt BLK-REQS-CHASE |
| `cycle_time` hours | Archive metrics | Deterministic difference of `application_received_at` and `bound_at` |

## Spec vs prompt disagreements

| Topic | `spec/` | Prompt | This build |
| --- | --- | --- | --- |
| Tool verbs | Endpoints are mostly GET, but `kind: write` | Agents must send mail, update the workbench, and archive | Declared GET is used for reads. Writes use POST/PATCH on the same systems, held when autonomy is `draft_for_approval`. Documented here, not invented as new `tool_id`s. |
| INT_03 PATCH status | Present as `T-03` | Archive agent should set Closed | Agent tools are INT_02 + INT_07 only. Closed is written on the warehouse payload. INT_03 is not called. |
| IT Operations ticket | No ITSM tool | On archive API failure, open a ticket | Ticket is a draft on the result. No undeclared ITSM endpoint. |
| Agent in/out schemas | Empty objects | Agents read/write case fields and communications | Writes go through tools and `drafts`. Extra case keys are synthetic (see below). |
| Models | `agents.yaml` says gpt-4o; `runtime.yaml` says gemini-3.5-flash | Deterministic process | Default runtime is deterministic code. `MEDRECS_LLM_ENABLED` stays false. |
| Evals | `evals/cases.csv` is empty; thresholds have blank values at `monitor` | Graders.md has one rubric | Synthetic deterministic checks cover the rubric. Monitor thresholds are reported, not gated with invented numbers. |

## Synthetic fixtures

Cases `UW-REQ-01` … `UW-FAIL-10` and `UW-2026-00042` are Synthetic Test Data. They are not production files. Extra fields (`documents_received`, `inbound_email`, `vault_documents`, `policy_bound`, …) are not in `schemas/case.schema.json`; the schema does not forbid additional properties, and the per-agent in/out slices are empty because the surface registers are absent.
