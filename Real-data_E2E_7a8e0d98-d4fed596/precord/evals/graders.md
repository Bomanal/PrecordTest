# Graders

How a case is judged. Deterministic checks run first and are exact; a rubric is only reached where no check can decide, and a rubric that duplicates a check below is a slower way of getting the same answer less reliably.

## Deterministic checks

No surface validation rules are on record for this process, so every case below is judged by rubric. That is a thinner corpus than it looks — say so before the pilot.

## Rubrics

Reached only where no deterministic check decides. Each states what a passing answer does *and* what a failing one does; a rubric with only the first is read two ways by two graders.

### general_case_completion · *

**Judges** Correct identification of medical records and complete underwriting assessment

- **Passes** — The agent correctly extracts all medical data, flags duplicates, and provides a clear processing decision.
- **Fails** — The agent misses key medical records, fails to identify duplicate requests, or provides an incomplete or ungrounded decision.

## What these cannot cover

Deterministic checks cannot evaluate the semantic correctness and quality of underwriting decisions or the adequacy of the reasoning behind manual chases. These qualitative aspects must be assessed using rubrics once test cases are provided.

## Coverage

0 case(s) in `evals/cases/`, 0 deterministic check(s), 1 rubric(s).
