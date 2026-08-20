# Assumptions and deviations

BUILD.md: a value in `spec/open_items.csv` is not inferred. Context that disagrees with `spec/` is recorded here rather than silently preferred.

## Blocking open items — not invented

| Item | What was needed | What this build does |
| --- | --- | --- |
| OI-01 Per-life Retention Limit | Compare Sum Assured to Retention Limit for Facultative Referral | Calls `GET /reinsurance/treaty-limits`. Mock returns `retention_limit: null`. Agent records OI-01 and does not invent a crore figure. |
| OI-02 Non-Medical Limit bands | Age × Sum Assured NML grid | Calls `GET /underwriting/medical-grid`. Mock fixture is labelled `source=synthetic_fixture` and `open_item=OI-02`. Notes tell the reviewer not to treat it as client NML. |
| OI-03 Sequencing of reinsurance referral | When the provisional vs facultative package is sent | Follows `context/reimagined_process_graph.mmd`: early provisional at S4, facultative at S9. Not a second sequence. |
| OI-04 LUW-1010 Sum Assured discrepancy | Which figure is the case Sum Assured | If `sum_assured`, `applied_sum_insured` and `header_sum_insured` disagree, the agent halts. |
| OI-05 AHT discrepancy | Operational handling time | Unused. No SLA minutes are configured (`checkpoints.yaml` has `sla_minutes: null`). |
| Q1 Cloud region | Hosting region | Deployment target remains unknown (`spec/runtime.yaml`). AWS is evidenced in `deployment_architecture_description.md` and contradicted as "not stated" in the technical specification — see deviations. |

## Stated (non-inferred) thresholds

These are cited from committed artifacts, not guessed:

| Value | Use | Source |
| --- | --- | --- |
| Rs 2.5 Cr (25,000,000 INR) | Early provisional alert trigger at S4 only | `opportunity_table.csv` OPP-03. This is **not** used as Retention Limit (OI-01). |
| Extra Mortality > 150% | S9 Facultative Referral trigger | `process_step_table.csv` S9; `prompts/BLK-02.md` |
| Hazardous Occupation cues: aviation crew, merchant navy | Occupation trigger | `ontology_nodes.csv` T6e72ae80 |
| BMI deviation > 1% vs PolicyCenter auto-calc | Flag for review | `opportunity_table.csv` OPP-02 |
| Override reason length ≥ 8 and not generic (`override`, `n/a`, …) | VAL-03-01 | `surface_validations.csv` VAL-03-01; tacit_knowledge TK-08 |

## Spec vs context disagreements

| Topic | `spec/` | `context/` | This build |
| --- | --- | --- | --- |
| S9 automation | `agents.yaml` BLK-02 serves S8 and S9 | `reimagined_process_graph.mmd` paints S9 as manual; OPP-05 `selected` is empty | Implements BLK-02.2 as **draft_for_approval** (spec). Does not bind a decision. |
| Tool catalog | `spec/tools.yaml` is empty | Agents name six endpoints; inventory has IP_01–IP_06 | Tools are implemented in `src/secureterm_uw/tools/catalog.py`. IP_05 stays unavailable. |
| Agent names in requirements vs spec | BLK-01 / BLK-02 with the names in `agent_specifications.csv` | `agentic_solution_requirements.md` uses three SR-A0x names | Spec / `agent_specifications.csv` names are used. |
| Cloud | `runtime.yaml` target `unknown` | deployment description says AWS evidenced | Runtime keeps `unknown`. |
| BLK-01 output schema | Empty object | Agents write tests and vitals via APIs | Writes go through tools, not the empty output schema. |

## Synthetic fixtures

Cases `LUW-FAST-01`, `LUW-REF-04`, `LUW-MER-06`, `LUW-EM-08`, `LUW-EM-OK`, `LUW-1010` are Synthetic Test Data. They are not Case LUW-1010 production figures.
