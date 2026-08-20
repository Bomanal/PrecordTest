# Graders

How a case is judged. Deterministic checks run first and are exact; a rubric is only reached where no check can decide, and a rubric that duplicates a check below is a slower way of getting the same answer less reliably.

## Deterministic checks

Projected from `context/surface_validations.csv`. These are rules the client's own screens already enforce, so a build that fails one has produced something the current process would have refused.

| check_id | surface | rule | on failure | reviewer message | source |
|---|---|---|---|---|---|
| VAL-02-01 | SURF-02 | Manually check height, weight, and validated BMI metrics to bypass calculation system defects on non-metric entries | advisory | not stated | `surface_validations@row:1` |
| VAL-03-01 | SURF-03 | Override reason is mandatory when underwriter override EM rating is modified | blocking | not stated | `surface_validations@row:2` |

## Rubrics

Reached only where no deterministic check decides. Each states what a passing answer does *and* what a failing one does; a rubric with only the first is read two ways by two graders.

### R-EC-01 · EC-01

**Judges** Ability of the underwriter to make fast-track decisions immediately based on preliminary metrics before opening clinical or financial data.

- **Passes** — The underwriter immediately makes a fast-track decision during step S3 using only the five key preliminary cues without reviewing detailed medical or financial records.
- **Fails** — The underwriter either opens detailed clinical or financial records before making a decision or fails to identify fast-track eligibility from the preliminary cues.

### R-EC-02 · EC-02

**Judges** Ability to bypass standard stages and initiate early provisional summaries for reinsurer cases.

- **Passes** — The underwriter skips sequential steps and directly dispatches a provisional summary to Atlas Re for cases requiring reinsurer approval.
- **Fails** — The underwriter standardly walks through sequential steps or delays sending the summary instead of initiating an early referral.

## What these cannot cover

Deterministic checks cannot cover the qualitative decision-making process for fast-tracking in step S3, nor the compliance of early bypass protocols for reinsurer referrals in step S4.

## Coverage

2 case(s) in `evals/cases/`, 2 deterministic check(s), 2 rubric(s).
