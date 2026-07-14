# Zero-Token Repeat Proof

Date: 2026-07-14

## Run

A fresh temporary `CODEX_HOME` was configured once for the current Night Shift
repo with Mac-local AI, quiet mode, current-repo scope, brief permission, and a
two-hour stop label. The same home then ran:

```sh
night-shift start --yes --once --skip-smoke
night-shift start --yes --once --skip-smoke
```

## Result

- Both commands exited successfully with zero questions.
- Both cycles reported `NIGHTSHIFT_RUN: YELLOW` because deterministic filters found no model-ready task.
- Both token reports said `No delegate proof paths captured.`
- Each cycle created its own ledger and a complete morning brief.
- The source checkout stayed untouched.

This proves repeated zero-token filtering on an unchanged revision without
pretending that no-work is a useful patch outcome. It does not prove a strong
tokens-per-accepted-patch rate; that still needs repeated healthy runs that
produce independently accepted work.

