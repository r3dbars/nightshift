# Actionable Repository Ranking Proof

Date: 2026-07-12

## Claim

Portfolio ranking favors actionable default/open-branch work over raw backlog
volume, while always retaining the repo the user explicitly launched from.

## Live Baseline

A real authenticated 30-day, ten-repo discovery produced:

- BetterFeedback: score 1,355, 28 open PRs, 14 failed branch/workflow pairs.
- Draft: score 166, 2 PRs, 14 issues.
- Transcripted: score 160, 2 PRs.
- Night Shift primary: score 120.

BetterFeedback's score was inflated by many green draft PRs and failed workflows
on stale closed branches.

## Live Regrade

The same discovery after the deterministic policy change produced:

1. BetterFeedback: 555, with only three default-branch failures retained.
2. Transcripted: 145.
3. Night Shift primary: 120.
4. Steadytype: 115.
5. Draft: 111.

BetterFeedback remains first for a valid reason: current default-branch failures.
Its 27 green draft PRs contribute only the capped draft-backlog bonus. Draft's
large issue backlog no longer outranks fresher review work by volume alone.

## Policy

- Failed runs count only on the default branch or a currently open PR branch.
- Failed run, actionable PR, ready PR, draft PR, and issue bonuses are capped.
- Failed checks and requested changes remain strongly weighted.
- The explicit primary repo always occupies one selected slot, even when its
  score is lower than the backlog cutoff.
- No model calls are used for ranking.

## Deterministic Gate

The package gate passes 181 tests. Focused coverage proves stale-branch failure
filtering, every signal-family cap, failed-run priority, primary-repo retention,
and primary fallback branch filtering.
