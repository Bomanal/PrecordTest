# BUILD.md

Read this first. It is the only prose in this package; everything else is a specification a build reads field by field.

## 1. What this is

**life insurance underwriting process**.

This solution automates the manual medical-records bottleneck within the client's life insurance underwriting process, specifically targeting the collection, tracking, and intake of critical clinical evidence. The agentic blocks automatically draft initial requests and execute follow-up vendor chasing for the attending_physician_statement, extract timeline updates from emails to update the underwriting_workbench, and automatically verify incoming laboratory_report files uploaded to the document_repository. By offloading these repetitive administrative tasks and database status updates to automated agents, the system dramatically reduces the overall case cycle_time for each underwriting_case_id across all levels of requested face_amount and product_type. This leaves human underwriters free to focus their expertise strictly on clinical risk evaluation, determining the correct risk_classification, and executing final underwriting_decision actions inside the policy_administration_system under rigorous human-in-the-loop oversight.

Everything under `context/` is Experience 1's output, carried in unchanged and read-only. It is evidence, not instruction: where it disagrees with a file under `spec/`, the disagreement is a question for a person and is recorded in `spec/deviations.csv`.

| Path | What it is |
| --- | --- |
| `context/agentic_solution_requirements.md` | the solution requirements: agents, integrations, data points |
| `context/opportunity_table.csv` | the designed automation opportunities, what each agent does, and which are selected |
| `context/reimagined_process_graph.mmd` | the reimagined process drawn, with automation on the selected steps |
| `context/agent_specifications.csv` | what each agent block may do unattended, who reviews it, where a case escalates |
| `context/not_automated_register.csv` | what is deliberately left with a person, and why |
| `context/integration_point_inventory.csv` | each place an agent would have to reach a system, and whether it can |
| `context/surface_inventory.csv` | field-grain detail behind the screens: inventory, data points, actions, validations — this file is the inventory |
| `context/surface_data_points.csv` | field-grain detail behind the screens: inventory, data points, actions, validations — this file is the data points |
| `context/surface_actions.csv` | field-grain detail behind the screens: inventory, data points, actions, validations — this file is the actions |
| `context/surface_validations.csv` | field-grain detail behind the screens: inventory, data points, actions, validations — this file is the validations |
| `context/surface_step_mapping.csv` | field-grain detail behind the screens: inventory, data points, actions, validations — this file is the step mapping |
| `context/ontology_nodes.csv` | the client's vocabulary — what they call each concept and what else they call it |
| `context/process_step_table.csv` | the as-is process, one row per step, with actor, system and branch conditions |
| `context/tacit_knowledge.csv` | exceptions, workarounds and judgement calls, each filed against a step |
| `context/kpi_board_definition.csv` | the metrics this process is measured by, with their current benchmarks |
| `context/roi_assumptions.csv` | the inputs each priced benefit rests on, with their origin and as-of date |
| `context/technical_transformation_specification.md` | the technical specification: IT, security, deployment |
| `context/deployment_architecture_description.md` | the deployment environment in prose |
| `context/system_architecture_map.mmd` | the systems in the estate and how they connect |
| `context/data_flow_map.md` | where the data moves between systems |
| `context/data_pipeline_specification.md` | how data reaches the solution and in what shape |
| `context/workflow_ui_understanding.md` | the screens the work is actually done on |
| `spec/` | the agents, tools, checkpoints and runtime this build implements |
| `schemas/` | the case object every agent reads and writes, and each agent's slice of it |
| `prompts/` | one prompt per agent, four-layer, editable |
| `evals/` | the cases, thresholds and graders that decide whether it is done |

## 2. Stack

No stack was chosen. Stop and ask; do not pick one, because every file under `spec/` was written against a stack somebody agreed.

## 3. Build order

Build in this order. Each step depends on the one before it, and skipping ahead
is how a package acquires an agent that reads a field nothing defines.

1. **`schemas/`** — the case object first, then each agent's input and output.
   Everything else names these fields.
2. **`spec/tools.yaml`** — the integrations, read and write kept apart. A tool
   that is not in this file does not exist; an integration that needs one and
   has none is a row in `spec/open_items.csv`.
3. **Single agents** — one at a time, each against its own schemas and its own
   prompt under `prompts/`.
4. **Composition** — only where `spec/agents.yaml` declares `sub_agents[]`. A
   block that declares none is one agent, however large its purpose reads.
5. **`spec/checkpoints.yaml`** — the human loop. Every `shown[]` field is a
   property of the case object and every `agent_id` is a top-level agent.
6. **`evals/`** — the cases, then the thresholds, then the graders.

## 4. Rules

- **`context/ontology_nodes.csv` is the naming authority.** Where the code
  needs a name for a concept, it is the canonical name in that file. The
  variants column is what the client's screens say; it is not a second set of
  names to implement.
- **All arithmetic is deterministic code, never a model call.** Rates,
  totals, ages, limits and eligibility are computed in the language, not asked
  for in a prompt.
- **Every write tool is idempotent.** `spec/tools.yaml` gives each write an
  `idempotency_key`; a retry that creates a second case is the failure this
  rule exists for.
- **Nothing in `context/not_automated_register.csv` gets automated.** Those
  steps stay with a person by decision, not by omission, and an agent placed
  on one contradicts a sign-off somebody gave.
- **`_provenance` is machine-readable provenance, not a comment.** Every
  generated YAML and JSON file carries a sibling `_provenance` map keyed by
  field path, whose values are `<artifact_key>@<locator>` citations into
  `context/`. A field with no entry was written by hand. Keep the map when you
  edit the file; it is how a reader six months from now finds out why a value
  is what it is.
- **A few citations name files this package does not carry.**
  `it_requirements_questionnaire` and `synthesis_open_items` are the registers
  `spec/open_items.csv` is distilled from, and they are deliberately absent:
  shipping both the raw registers and the distillation would give the same
  unknown two homes and no rule about which one is current. The citation is
  kept so the trace survives — if you need the original row, it is in the
  platform, not here. `as_is_process_graph` is absent for a different reason:
  it describes what must *not* be built.
- **An endpoint that does not exist is an open item, not a tool.** If
  `context/integration_point_inventory.csv` `needs` is not `existing endpoint`,
  emit a row in `spec/open_items.csv` and **no tool**. Silence means do not
  invent an API.
- **The case object is the shared schema.** `schemas/case.schema.json` is the
  object every agent reads and writes; per-agent in/out files are slices of it.
- **Evals are the acceptance tests.** Case JSON is fanned out from
  `evals/cases.csv`; every threshold traces to a priced assumption or a KPI;
  graders name how each threshold is checked.

## 5. Stop conditions

**If a value you need is in `spec/open_items.csv`, stop and ask. Do not infer
it.** That register exists because silence becomes invention: an unknown left
blank gets filled in confidently and wrongly, and the wrong value is
indistinguishable from a right one by the time anybody looks.

Rows marked `blocking` stop the build. The rest can be carried as a stated
assumption, written down where the assumption is used.

Stop also when a file under `spec/` names something that does not exist — an
agent, a tool, a checkpoint, a schema property. That is a broken cross-reference
rather than a gap, and guessing which end is wrong is how the two halves of a
package drift apart.

## 6. Definition of done

The evals in `evals/thresholds.csv` pass at the gate tier each one states.

Not "the tests pass" and not "it runs": every threshold in that file traces to a
`roi_assumptions` row or a `kpi_id`, which is to say somebody priced the
transformation on it. A build that runs and misses them has not delivered what
was sold.
