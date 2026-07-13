# First-Run UX Proof: 2026-07-13

This is a fresh-home observation of the normal Night Shift flow.

## Fresh first run

- `HOME=/tmp/night-shift-new-user-run-20260713`
- `CODEX_HOME=/tmp/night-shift-new-user-run-20260713/.codex`
- No saved Night Shift setup
- No GitHub login in the isolated home
- Local Mac AI reachable
- Current repo had unsaved changes

The command was:

```text
night-shift start --repo /Users/redbars/code/night-shift --stop-after 2h --once
```

The user-facing flow showed the project, the safe plan, the no-push/no-merge
boundary, the saved setup path, and one final question:

```text
Start Night Shift now? [Y/n]:
```

After answering `y`, the run returned a truthful YELLOW result because no task
had enough evidence for model dispatch. It created a morning brief and made no
source checkout changes.

## Repeat run

The same isolated home then ran:

```text
night-shift start --repo /Users/redbars/code/night-shift --stop-after 2h --once --yes
```

It reused the saved setup unchanged, asked no setup questions, created a new
ledger, and returned the same honest no-work result. This proves the intended
one-consent first run and zero-question repeat behavior. It does not replace
the separate full eight-hour repeat-use proof.

