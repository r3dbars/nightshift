# GitHub Workflow Run Ordering

## Change

Portfolio signal collection now chooses the newest workflow run by its
`updatedAt` timestamp instead of trusting the order returned by `gh run list`.
An older failed run can no longer make a repo look broken when a newer run has
already passed.

## Evidence

- Focused portfolio tests: 3 passed, including an intentionally unsorted
  failed-then-passed response.
- Full package gate: `bash scripts/check-package.sh` passed **460 tests** and
  package checks.
- No GitHub write, cloud call, draft PR, merge, or deployment was performed.
- Scores remain conservative: GitHub usefulness and Repository prioritization
  stay below 95 until repeated accepted hosted outcomes are measured.
