# Behavioral coverage utility gate

Date: 2026-07-12

## Problem

A real Night Shift handoff initially recommended an import/signature test for
`DraftEngine.cleanup`. That would increase a textual coverage signal without
proving useful behavior.

## Change

Coverage candidates and cloud handoffs now reject test plans whose proposed
proof is limited to signatures, imports, existence, identifiers, or textual
references. A ready implementation must assert observable behavior such as a
return value, error, response, state change, or side effect.

Validated learning is utility-schema versioned. Older review rows cannot affect
ranking because they never passed this gate. A `CONFIRMED` verdict receives a
bounded boost only when the same valid review also says
`READY_FOR_IMPLEMENTATION: yes`.

## Real proof

The exact saved Night Shift candidate was sent again to ephemeral read-only
Codex with one-time `--allow-cloud` consent. The revised review cited the pinned
implementation and proposed a behavioral test that mocks `run_cmd`, verifies
worktree remove and prune calls, asserts the cleanup return value, and runs the
repository's detected unittest command.

The review passed utility schema 2 with `valid_review=true`,
`utility_valid=true`, and `ready_for_implementation=true`. Its exact fingerprint
and pinned revision were written to local review history. No code or GitHub
write occurred.

## Automated proof

- Presence-only coverage output is rejected before it can score MAYBE.
- A presence-only cloud review with READY=yes is invalid.
- Behavioral failure-path and return-value plans remain valid.
- Old utility schemas are ignored.
- CONFIRMED plus READY=no remains neutral.
- Legacy REJECTED reviews remain conservative suppressions; legacy CONFIRMED
  reviews remain neutral until they pass utility schema 2.
- All accepted plain and Markdown citation forms are excluded from proposal
  language classification.
- `scripts/check-package.sh`: 246 tests plus package/install checks passed.

Claude's detailed review found the legacy-rejection and Markdown-citation
compatibility issues before merge. Proof:
`/Users/redbars/.codex/maestro/runs/20260713T042755Z-night-shift-behavioral-coverage-review-details-claude`.
Final re-review found no remaining correctness or security blocker:
`/Users/redbars/.codex/maestro/runs/20260713T043427Z-night-shift-behavioral-coverage-rereview-claude`.

## Boundary

This proves higher-quality filtering and one real implementation-ready
behavioral plan. It does not yet prove an accepted patch or draft PR, so useful
output remains scored conservatively.
