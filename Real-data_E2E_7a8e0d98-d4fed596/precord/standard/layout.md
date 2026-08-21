# Specificity standard — layout

The directory shape of a Precord. A coding assistant opens this repository.
`precord_layout.py` is the single definition of these paths; this file is the
copy that ships so a builder who never sees the platform still has the map.

```
precord-<process>/
├── BUILD.md                      ← read first. §1–§2 instance; §3–§6 from this standard
├── manifest.json                 ← assembly record. Written by the bundler
├── standard/                     ← S, pinned bytes (this folder)
│   ├── VERSION
│   ├── protocol.md
│   ├── layout.md
│   ├── tools.defaults.yaml
│   ├── runtime.defaults.yaml
│   ├── agents.defaults.yaml
│   └── prompts.platform.md
├── context/                      ← I, 22 E1 artifacts, read-only
├── spec/                         ← C
│   ├── agents.yaml
│   ├── tools.yaml
│   ├── checkpoints.yaml
│   ├── runtime.yaml
│   ├── open_items.csv
│   ├── deviations.csv
│   └── baseline.csv
├── prompts/
│   └── <agent_id>.md
├── schemas/
│   ├── case.schema.json
│   └── <agent_id>.{in,out}.schema.json
├── evals/
│   ├── cases.csv
│   ├── cases/<case_id>.json
│   ├── thresholds.csv
│   └── graders.md
└── workflow/                     ← Scenario B only
    └── skeleton.md
```

`manifest.json` sits outside S, I and C. No claim about the solution is read
out of it.

`workflow/` is present only when there is no core workflow system (Scenario B).
A builder in Scenario A must not see this folder.
