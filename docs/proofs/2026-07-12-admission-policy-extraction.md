# Pre-Model Admission Policy Extraction Proof

Date: 2026-07-12

## Claim

Night Shift's pre-model admission rules now have one directly tested owner and
still reject weak work before spending local or LAN inference.

## Change

The following pure policy moved from the controller into
`bin/night_shift_selection.py`:

- explicit test/coverage goal detection;
- multi-item issue tracker detection;
- failed-CI evidence and revision requirements;
- actionable PR requirements;
- incomplete coverage-index rejection;
- Normal-mode broad-work suppression;
- stable ready/skipped partitioning.

The controller imports the same function names, preserving its internal API.
It fell from 4,661 to 4,592 lines. The selection module is now 184 lines.

## Deterministic Gate

`scripts/check-package.sh` passed all 191 tests and package/install checks.
Direct tests cover malformed signals, tracker gating, failed-CI evidence,
coverage intent, and stable skip records. Existing controller integration tests
continue to exercise the imported policy through real queue construction.

## Real CLI Proof

A fresh linked temporary home saved a Mac-only Quiet setup and then ran:

```sh
night-shift start --yes --once --skip-smoke \
  --repo /Users/redbars/code/night-shift
```

Measured results:

- Exit code: 0.
- Model-ready tasks: 0.
- Pre-model skips: 10.
- Mac model calls: 0.
- Windows model calls: 0.
- Skip reasons: broad mapping reserved for Afterburner and coverage-index-only
  work reserved for Afterburner or an explicit coverage goal.
- Child and portfolio status: honest YELLOW no-work.
- Saved setup: reused unchanged.

This proves behavioral wiring and efficiency, not overnight usefulness.

## Regrade

Maintainability moves from 68 to 71. Setup and admission policy now have clear,
directly tested module owners, but the controller still contains the 416-line
queue builder plus dispatch and lifecycle orchestration.
