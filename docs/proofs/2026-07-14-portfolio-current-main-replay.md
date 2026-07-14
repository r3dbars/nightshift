# Current-Main Portfolio Replay

Date: 2026-07-14

## Run

The current `main` revision ran from a fresh temporary `CODEX_HOME` with the
normal user-facing command shape:

```sh
night-shift start --repo /Users/redbars/code/night-shift \
  --scope github-recent --mode night-shift --permission draft-local \
  --execute-drafts --guidance scan --privacy mac-only --stop-after 2h \
  --local-url http://localhost:1234/v1 \
  --local-model qwen/qwen3-coder-next --skip-smoke --yes --once
```

Observed result:

```text
NIGHTSHIFT_AUTOPILOT: YELLOW | cycles=1
Repositories visited: 3
Repository batches completed: 3
local: calls=4 ... total=9342
windows=0
```

## Ranking And Decisions

1. `r3dbars/BetterFeedback` ranked first: recent failing checks; two
   unproven candidates were kept in its child ledger.
2. `r3dbars/transcripted` ranked second: active GitHub work; no task met the
   evidence and verification bar.
3. `r3dbars/nightshift` ranked third: the current project; no task met the
   evidence and verification bar.

The portfolio brief explained each selection reason, named each child proof
ledger, and clearly said that no item was safe to put on the review list. No
checkout was edited, no Windows call was made, and no GitHub write occurred.

This is evidence for ranking, multi-repo coverage, and honest no-work
behavior. It is not counted as an accepted patch or a useful-outcome win.
