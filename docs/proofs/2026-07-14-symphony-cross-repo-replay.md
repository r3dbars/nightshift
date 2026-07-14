# Symphony Cross-Repo Replay

Date: 2026-07-14

## Run

I ran a fresh isolated Night Shift setup against `/Users/redbars/code/symphony`
with a new `CODEX_HOME`, local Mac AI routing, quiet mode, and a bounded
behavioral-test goal. The repository was detected as `openai/symphony`.

The checkout already had an unsaved change in `elixir/WORKFLOW.md`. Night Shift
reported that state and left the checkout untouched. No Windows or cloud lane
was used.

## Result

The run exited successfully with an honest YELLOW brief:

- repositories visited: 1
- pre-model weak-signal skips: 10
- model attempts: 0
- estimated model tokens: 0
- accepted candidates: 0
- source checkout changes caused by Night Shift: 0
- morning brief: no work was strong enough to put on the review list

The skipped work included PRs without requested changes or failed checks,
coverage signals without deterministic gap evidence, a failed workflow without
a named candidate file and broad mapping work reserved for Afterburner. This
shows the arbitrary-repo path can decline to spend local compute when the
available evidence is weak.

## Artifact

The raw run ledger is under:

```text
/Users/redbars/.codex/night-shift/symphony-current-goal.Vro8M7/maestro/overnight/night-shift-20260714T125507Z-autopilot
```

No code, branch, commit, PR, or GitHub write was created.
