# Native Eight-Hour Repeat Proof

Date: 2026-07-14

## Run

Night Shift was launched with the normal saved-setup command shape and an
explicit `--yes` repeat:

```sh
/Users/redbars/code/night-shift/bin/night-shift start \
  --repo /Users/redbars/code/night-shift --scope current \
  --mode quiet --permission draft-local --execute-drafts \
  --guidance scan --privacy mac-only --stop-after 8h \
  --local-url http://localhost:1234/v1 \
  --local-model qwen/qwen3-coder-next --skip-smoke --yes
```

The run used an isolated temporary `CODEX_HOME`, so it could not touch the
user's saved setup or source checkout.

## Result

- Parent controller completed its full eight-hour deadline and exited.
- 8/8 child cycles completed with `rc=0`.
- Every child startup gate was `GREEN`.
- Every child used Mac-only routing, with 0 local/Windows model calls because
  the unchanged revision had no model-ready work.
- No repeat setup question was asked and no second setup ledger was created.
- No source checkout, GitHub branch, PR, merge, release, or deployment was
  changed.

The honest morning result was: “nothing was strong enough to work on safely
tonight.” This is a repeat-use and healthy-stop proof, not a useful-patch
proof. The raw parent ledger is:

```text
/Users/redbars/.codex/night-shift-native-8h-current-GbVhKG/.codex/maestro/overnight/night-shift-20260713T204326Z-autopilot
```
