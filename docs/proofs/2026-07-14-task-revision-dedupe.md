# Task revision dedupe proof

Date: 2026-07-14

Parent ledger:

`/Users/redbars/.codex/maestro/overnight/night-shift-20260714T173533Z-autopilot`

## Live result

The run used merged commit `f3e6951` with the task-file revision dedupe fix.
The same three-repository portfolio was visited in ranked order. The current
Night Shift repo produced:

- Cycle 1: one `VERIFIED_DRAFT` for
  `changed-file-proof-01-bin-night-shift-drafts-py`, 3,416 estimated tokens,
  and a clean disposable worktree.
- Cycle 2: a different
  `changed-file-proof-02-bin-night-shift-portfolio-reporting-py` candidate,
  3,572 estimated tokens, rather than reopening the cleanup task.

Both ledgers reported the same repository `HEAD`, and both task rows recorded
the file-scoped revision
`138a35f54103c15005f6057c3e3107e4987a7d1f`. The cleanup fingerprint was not
repeated in cycle 2. The second candidate remained candidate-only because its
verification did not produce a verified draft; no useful outcome was invented.

The two other portfolio repos were skipped before model calls because their
evidence was not specific enough. The source checkout stayed untouched, and
the run made no GitHub or cloud write.

## What this proves

- Unchanged task files are not reopened simply because the controller advances
  to another cycle.
- Different grounded tasks in the same repository can still proceed.
- A candidate-only result remains separate from a verified outcome.

This does not prove accepted user value, a full overnight accepted-outcome
bound, or a hosted draft PR. Those score requirements remain open.
