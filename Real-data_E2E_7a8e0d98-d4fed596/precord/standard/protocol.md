# Specificity standard — protocol

This file is how any Specificity agentic solution is built. It does not vary
by client. `BUILD.md` §3–§6 are generated from the four numbered sections
below so those sections cannot silently disagree with this file.

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
