# Queue Assembly Extraction Proof

Date: 2026-07-12

## Claim

Night Shift's complete deterministic queue assembly now has a directly tested
module owner, while the controller preserves its existing callable API and
injects all command execution explicitly.

## Change

`bin/night_shift_queue.py` now owns the complete queue pipeline:

- task file narrowing and ladder priorities;
- bounded repository evidence indexing;
- immutable Git revision validation;
- mission, coverage, test-command, docs, TODO, failed-CI, issue, PR, test-map,
  and source-map item construction;
- slug deduplication, stable evidence-first ordering, and mode limits.

The controller retains a 12-line compatibility wrapper that injects `run_cmd`
and `detect_test_commands`. It fell from 4,439 to 4,151 lines. No hidden command
runner or circular import was introduced.

## Multi-Signal Exact Parity

The pre-change controller and current controller were loaded side by side
against the same real temporary Git repository and one fixed scan containing:

- explicit mission guidance;
- a complete coverage lead;
- a test command, docs file, and TODO;
- an exact-symbol issue;
- a changes-requested pinned PR;
- a failed-CI run and failed-step log pinned to the same commit.

Complete queue JSON was compared byte for byte:

- Quiet: parity yes, 10 items.
- Normal: parity yes, 12 items.
- Afterburner: parity yes, 12 items.
- Failed-CI and PR source refs: exact temporary commit SHA in both versions.
- Ordering, priorities, commands, evidence, lanes, and executability: identical.

## Real CLI Proof

A fresh linked temporary home ran setup once and then a real Mac-only Quiet
cycle through `night-shift start --yes --once --skip-smoke`.

- Questions on repeat: 0.
- Exit code: 0.
- Ready tasks: 0.
- Weak tasks skipped before inference: 10.
- Mac/Windows calls: 0/0.
- Child and portfolio status: honest YELLOW no-work.
- Saved setup: reused unchanged.

This is wiring and efficiency proof, not useful overnight output.

## Deterministic Gate

`scripts/check-package.sh` passed all 202 tests and package/install checks.
Direct module tests cover ranking, limits, stable ties, dedupe, mission priority,
failed-CI injection, Git safety, evidence bounds, and binary rejection.

## Regrade

Maintainability moves from 77 to 82. Queue construction is now cohesive and
directly tested, but dispatch and lifecycle orchestration remain in the
4,151-line controller, so 95 is not yet justified.
