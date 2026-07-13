# Explicit Goal Routing Proof

This proof records the local-model behavior for one explicit mission against
the merged Night Shift repository at `35fca2758512090813eca6872f0d8097a7c268ac`.

## What changed

An explicit behavioral-test mission now carries a minimum target-invocation
contract. When immutable source and invocation evidence are complete, the
mission prompt also permits `ACTION_TYPE: draft-pr-candidate`; otherwise the
worker must stay analysis-only.

## Live outcomes

The same cleanup mission was run from fresh Night Shift homes:

1. The first run returned `patch-plan`, so no patch was attempted.
2. After the contract fix, the worker returned a draft candidate. The patch
   had wrong context and reversed arguments, so deterministic patch validation
   rejected it before verification. The disposable worktree was removed and
   the source checkout stayed clean.
3. The separate BetterFeedback TypeScript mission produced a real
   `VERIFIED_DRAFT` with `baseline_rc=0`, `after_rc=0`, and
   `npm run test:unit:vitest` passing in the isolated runner.

The first two outcomes are intentionally not counted as useful patches. They
prove that Night Shift is routing an explicit mission into the right bounded
lane while refusing unsupported or malformed output.

Artifacts:

```text
/Users/redbars/.codex/maestro/overnight/night-shift-python-proof-3/maestro/overnight/night-shift-20260713T184420Z-autopilot/morning.md
/Users/redbars/.codex/maestro/overnight/night-shift-python-proof-4/maestro/overnight/night-shift-20260713T184602Z-autopilot/cycles.json
/Users/redbars/.codex/maestro/overnight/night-shift-betterfeedback-rerun-codex/maestro/overnight/night-shift-20260713T182522Z-autopilot/cycles.json
```
