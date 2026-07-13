# Setup Policy Extraction Proof

Date: 2026-07-12

## Claim

Night Shift's first-run and repeat-run policy is independently testable without
changing the user-facing `night-shift start` behavior.

## Change

Pure setup behavior moved from the controller into `bin/night_shift_setup.py`:

- worker descriptions respect health and the saved privacy route;
- mode, autonomy, goal, permission, and stop labels;
- the WILL/WILL NOT preview contract;
- timestamp-insensitive saved-setup comparison.

The controller keeps small compatibility wrappers where runtime mode defaults
must be supplied. Its size fell from 4,785 to 4,661 lines. The new module is 138
lines and has four direct policy tests.

## Deterministic Gate

`scripts/check-package.sh` passed all 187 tests and package/install checks.

## Real Repeat Proof

A temporary blank `CODEX_HOME` received linked Night Shift executables. The real
first-run entry point saved setup only:

```sh
night-shift start --yes --setup-only --skip-smoke \
  --repo /Users/redbars/code/night-shift --mode quiet --stop-after 2h \
  --scope current --wake-goal chores --privacy mac-only --permission brief
```

The same home then ran:

```sh
night-shift start --yes --once --skip-smoke \
  --repo /Users/redbars/code/night-shift
```

Measured results:

- Exit code: 0.
- Questions on repeat: 0.
- Config SHA-256 before and after: identical.
- Setup runs after both commands: 1.
- Preview: Quiet, chores, read-only autonomy, two-hour stop, Mac-only.
- Preview references to another computer: 0.
- Child result: honest YELLOW because no grounded task survived.
- Portfolio result: YELLOW, not a false failure.

An initial harness used an empty `CODEX_HOME` without linking executables and
correctly failed the startup gate. Linking the same executables a real install
provides made the proof pass; that failure was retained as evidence that the
startup gate detects an incomplete installation.

## Regrade

Maintainability moves from 64 to 68. Setup policy now has a clear tested owner,
but queue construction, dispatch, and lifecycle still remain in the 4,661-line
controller, so a high score is not yet justified.
