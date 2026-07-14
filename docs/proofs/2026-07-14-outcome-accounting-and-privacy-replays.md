# Outcome Accounting and Privacy Replays

These replays exercise the merged candidate-versus-verified accounting on
clean Night Shift revisions. They use local Mac inference only. No cloud
handoff, Windows worker, GitHub write, commit, or pull request was enabled.

## Verified Local Draft

- Run: `/Users/redbars/.codex/maestro/overnight/night-shift-20260714T155242Z-autopilot`
- Source: `r3dbars/nightshift` at `63e4cad`
- Result: one `VERIFIED_DRAFT`
- Model calls: one local call
- Estimated tokens: `3428`
- Outcome metrics: `verified_drafts=1`, `verified_outcome_rate=1.0`,
  `tokens_per_verified_draft=3428.0`
- Verification: `bash scripts/check-package.sh`, baseline `0`, after `0`
- Changed candidate file: `tests/test_night_shift.py`
- Disposable worktree: removed
- Source checkout: unchanged

The parent morning brief reported `Model candidates: 1 (0 candidate-only)`
and `Verified drafts: 1`.

## Clean Three-Repo Mac-Only Replay

- Run: `/Users/redbars/.codex/maestro/overnight/night-shift-20260714T160233Z-autopilot`
- Source: `r3dbars/nightshift` at `c938508`
- Repositories prepared: `r3dbars/BetterFeedback`,
  `r3dbars/suckscancer.com`, and `r3dbars/nightshift`
- Ranking: BetterFeedback first for `3` failed checks, then
  `suckscancer.com`, then the primary Night Shift repo
- Routing: explicit `--privacy mac-only`; `windows=0`
- No-work filtering: the first two repos spent `0` model tokens
- Night Shift result: one candidate, `REJECT` after isolated verification,
  `3413` estimated tokens, `0` verified drafts
- Source checkout: unchanged

The portfolio brief reported `3` repositories visited and separated
`Model candidates: 1 (1 candidate-only)` from `Verified drafts: 0`.

## Varied TypeScript Rejection

- Run: `/Users/redbars/.codex/maestro/overnight/night-shift-20260714T160603Z-autopilot`
- Repo: `r3dbars/BetterFeedback`
- Goal: an exact `getDeltaLabel` unit-test mission
- Result: `REJECT`; the worker returned a malformed patch hunk
- Model calls: one local call, `3428` estimated tokens
- Disposable worktree: removed
- Source checkout: unchanged

This is counted as a safe rejection, not a useful or verified outcome.
