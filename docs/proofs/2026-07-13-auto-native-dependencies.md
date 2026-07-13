# Automatic Native Dependency Proof

This run verifies the normal macOS trust path for a Node repository that will
be checked inside the Linux Colima runner.

## Run

- Night Shift revision: `509a638`.
- Clean GitHub clone:
  `/Users/redbars/.codex/night-shift-bf-clone-k89FpE/BetterFeedback`.
- Fresh setup root:
  `/Users/redbars/.codex/night-shift-auto-deps-bf-kOY8vV`.
- Command: `night-shift trust-repo --repo <clone> --apply --yes`.
- No `--prepare-dependencies` flag was supplied.

## Result

- macOS detected a lockfile-based Node repo and prepared runner-native
  dependencies in the disposable networked container.
- The isolated `npm run test:unit:vitest` preflight passed.
- Approval was saved outside the repo; the clone remained unchanged.
- The following explicit autopilot cycle stayed honest and produced no draft
  because its model candidate did not meet the proof bar.

The earlier control run with host macOS dependencies reproduced the real
failure: Vitest could not load the Linux `rolldown` native binding. The
automatic native-cache path removed that environment mismatch without mounting
host `node_modules` into the Linux runner.

## What this proves

This is direct evidence for the first-run portability path on this Mac and for
safe dependency preparation. It does not prove a useful patch, repeated
portfolio value, or a fresh-machine installation study.
