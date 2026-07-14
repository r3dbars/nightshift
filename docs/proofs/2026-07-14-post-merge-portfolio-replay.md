# Post-Merge Portfolio Replay

This is a fresh isolated replay from merged main after PR #241. It checks the
three-repository selection, deterministic pre-model filtering, isolated draft
verification, and honest rejection accounting without opening a PR or sending
anything to the cloud.

## Live run

- Parent ledger: `/tmp/night-shift-portfolio-main.omwzhr/maestro/overnight/night-shift-20260714T185736Z-autopilot`.
- Scope: `github-recent`, three repositories, 30-day activity window, one task per repository.
- Repositories visited: `r3dbars/BetterFeedback`, `r3dbars/suckscancer.com`, and `r3dbars/nightshift`.
- BetterFeedback: one `VERIFIED_DRAFT`, baseline and after checks passed, isolated worktree removed, 3,525 estimated local tokens.
- suckscancer.com: no model-ready task; zero model tokens.
- Night Shift: one candidate was rejected by the patch policy after baseline passed; the worktree was removed, 3,550 estimated local tokens.
- No draft PR, merge, deploy, or cloud handoff occurred; the source checkout stayed clean.

After the reason fix, a fresh read-only GitHub signal check produced these
current classifications:

- `r3dbars/BetterFeedback`: 2 actionable PRs, 1 draft PR, 1 issue -> `pull requests need review or fixes`.
- `r3dbars/suckscancer.com`: 1 failed run -> `recent failing checks`.
- `r3dbars/nightshift`: no PRs, failed runs, or issues -> `recent activity`.

The score and the reason now use the same PR-state classification instead of
turning all open PRs into one generic label.

## Honest boundary

This is one fresh mixed-repository replay with one independently verified draft.
It strengthens the repeatability evidence for portfolio selection and token
accounting, but it does not prove accepted user value, a hosted-green draft PR,
or a multi-night learning lift.
