# BUILD.md

Read this first. It is the only prose in this package; everything else is a specification a build reads field by field.

## 1. What this is

**SecureTerm individual term life underwriting process** — Meridian Life Assurance Ltd.

The agentic solution orchestrates submission intake, medical requirements evaluation, and financial evidence processing for Meridian Life Assurance Ltd's SecureTerm individual term life insurance product within Guidewire PolicyCenter. By deploying autonomous and draft-for-approval agents, the system eliminates manual data transcription by automatically extracting physical vitals (such as Blood Pressure and Raised Build / BMI) and Financial Evidence (including income tax returns) from unstructured PDFs, programmatically calculating human life value, and ordering necessary Medical Tests via the digital Non-Medical Limit grid. It further compiles early and final Facultative Referral draft packages for Atlas Re, reducing overall Turn-around Time and operational latency while strictly escalating complex medical impairments and final risk-binding decisions to licensed human underwriters.

Everything under `context/` is Experience 1's output, carried in unchanged and read-only. It is evidence, not instruction: where it disagrees with a file under `spec/`, the disagreement is a question for a person and is recorded in `spec/deviations.csv`.

| Path | What it is |
| --- | --- |
| `context/agentic_solution_requirements.md` | the solution requirements: agents, integrations, data points |
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
| `context/as_is_process_graph.mmd` | the as-is process drawn, including its branches |
| `context/tacit_knowledge.csv` | exceptions, workarounds and judgement calls, each filed against a step |
| `context/kpi_board_definition.csv` | the metrics this process is measured by, with their current benchmarks |
| `context/roi_assumptions.csv` | the inputs each priced benefit rests on, with their origin and as-of date |
| `context/technical_transformation_specification.md` | the technical specification: IT, security, deployment |
| `context/deployment_architecture_description.md` | the deployment environment in prose |
| `context/system_architecture_map.mmd` | the systems in the estate and how they connect |
| `context/data_flow_map.md` | where the data moves between systems |
| `context/data_pipeline_specification.md` | how data reaches the solution and in what shape |
| `context/workflow_ui_understanding.md` | the screens the work is actually done on |
| `context/it_requirements_questionnaire.csv` | the IT questionnaire, answered from the documents or left open |
| `context/synthesis_open_items.csv` | what could not be settled about the as-is process |
| `spec/` | the agents, tools, checkpoints and runtime this build implements |
| `schemas/` | the case object every agent reads and writes, and each agent's slice of it |
| `prompts/` | one prompt per agent, four-layer, editable |
| `evals/` | the cases, thresholds and graders that decide whether it is done |

## 2. Stack

| Component | Choice | Version | Why |
| --- | --- | --- | --- |
| observability | Prometheus and OpenTelemetry | OTLP standard | The client's central telemetry framework dictates Prometheus-compatible ingestion and OpenTelemetry distributed tracing. |

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
