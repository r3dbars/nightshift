# Lifecycle And Cancellation Proof

Date: 2026-07-12

## Claim

Night Shift deadlines, worker cancellation, reviewed-ledger cleanup, and active
controller detection now have one directly tested lifecycle owner. Real process
groups are terminated when pending work is cancelled.

## Change

`bin/night_shift_lifecycle.py` now owns:

- bounded stop-deadline calculation and idempotent STOP-file creation;
- graceful then forced termination of process groups recorded in a run ledger;
- pending-future cancellation and bounded wait;
- storage measurement;
- cleanup eligibility requiring completed, reviewed, old Night Shift ledgers;
- stale versus live controller PID state.

The CLI preserves existing callable signatures, including a zero-argument
`active_autopilot()` wrapper bound to its configured state path. The controller
fell from 3,998 to 3,923 lines.

## Real Cancellation Integration

The integration test performed real operating-system work:

1. Started `sleep 30` in a new process session.
2. Recorded its process-group PID in `processes.tsv`.
3. Occupied one executor worker so a second future remained queued.
4. Called `cancel_pending_workers`.
5. Verified the process exited nonzero in under two seconds.
6. Verified the queued future was cancelled.
7. Ran final cleanup and confirmed no process remained.

The integration test passed five consecutive runs. This proves the current
cancellation path, not controller crash restart or long-soak recovery.

## Additional Lifecycle Coverage

Direct tests also prove:

- morning/unknown stop modes have no automatic deadline;
- timed deadlines use exact configured durations;
- a reached deadline writes one STOP record and never rewrites it;
- malformed process rows are ignored and missing PIDs are counted;
- PID 0 and PID 1 ledger rows are rejected before any signal is sent;
- cleanup requires `morning.md`, `REVIEWED`, the ledger prefix, and age;
- missing or stale controller state is ignored while the current PID is live;
- directory sizing and empty cancellation are safe.

## Deterministic Gate

`scripts/check-package.sh` passed all 234 tests and package/install checks.

## Regrade

- Maintainability: 87 to 91. Queue, dispatch, and lifecycle policy now have
  cohesive tested owners; run/autopilot orchestration still remains in the
  3,923-line controller.
- Reliability: 86 to 89. Real process cancellation is repeatably proven, but
  controller crash restart and concurrent scheduler recovery are not.
- Ten-hour readiness: 86 to 88. Stop and cleanup behavior is stronger, but a
  clean ten-hour soak is still required.
