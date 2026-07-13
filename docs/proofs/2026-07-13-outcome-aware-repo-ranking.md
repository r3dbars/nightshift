# Outcome-Aware Repository Ranking

Date: 2026-07-13

## Change

GitHub urgency remains the main portfolio signal. Night Shift now also keeps a
bounded local `repo-outcomes.jsonl` ledger containing only repository slug,
completion time, source revision, estimated tokens, surviving candidate count,
and verified-draft count.

The latest eight runs can adjust a repository by at most -40 to +50 points:

- a verified draft adds 25;
- a surviving grounded candidate adds 10;
- a run that spends at least 1,000 estimated tokens and produces neither
  subtracts 10;
- a zero-token empty run is neutral.

Urgent failed-workflow signals can add up to 420 points, so learning cannot hide
an active repair need. The bounded adjustment helps choose between similarly
urgent repositories rather than overriding live GitHub truth.

## Real neutral-run proof

A real one-cycle controller run completed at parent ledger
`night-shift-20260713T094152Z-autopilot`. Weak signals were skipped before model
dispatch. The durable row recorded zero accepted candidates, zero tokens, and
zero verified drafts. Reloading the real ledger produced adjustment 0 with one
recent run, zero productive runs, and zero wasted-token runs.

## Verification

Tests cover positive and negative caps, neutral zero-token behavior, and bounded
latest-row retention. `scripts/check-package.sh` passed 316 tests and package
checks.

## Proof boundary

This proves durable measurement and neutral handling on a real run. It does not
yet prove that productive and wasteful real repositories reorder correctly or
that the reordered portfolio improves user-accepted outcomes. Repository
prioritization therefore remains 78.
