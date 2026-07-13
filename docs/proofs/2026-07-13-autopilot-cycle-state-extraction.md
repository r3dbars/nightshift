# Autopilot Cycle State Extraction Proof

The autopilot controller no longer owns its mutable transition policy inline.
`AutopilotCycleState` now owns cycle reset, status downgrade, work detection,
draft-once behavior, publish cleanup escalation, durable cycle rows, and final
action-required policy.

## Real parity run

- Source revision: `33185e7`.
- Parent ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T070447Z-autopilot`.
- Child ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T070447Z-afterburner`.
- One child completed with `rc=0` and one planned task.
- The parent truthfully remained YELLOW because the child had an unproven MAYBE
  candidate, wrote one canonical `cycles.json` row, rendered one exact morning
  choice, removed active-controller state, and left the source repo clean.

## Transition coverage

Direct tests cover:

1. child status/work transitions and per-row durable persistence;
2. one draft attempt per repo and remote-cleanup escalation;
3. clean, failed, and empty action-required outcomes;
4. multi-cycle work-signal reset;
5. draft execution requiring both execution enablement and draft permission.

`scripts/check-package.sh` passes 278 tests plus package and copied-install
checks. Claude traced the old and new transitions line by line and recommended
merge with no defects:
`/Users/redbars/.codex/maestro/runs/20260713T070533Z-night-shift-autopilot-cycle-state-review-claude`.

This reaches the maintainability promotion rule: policy and mutable controller
state have tested owners, while the CLI coordinates discovery, child execution,
drafting, and publishing as injected side effects.
