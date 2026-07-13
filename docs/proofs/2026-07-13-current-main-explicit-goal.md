# Current Main Explicit Goal Proof

This run exercised a fresh local setup against the merged `main` revision
after the malformed-diff retry fix.

## Run

- Source revision: `aa7164959671437f7c48f719c7a648eb6d9be019`.
- Fresh setup root:
  `/Users/redbars/.codex/night-shift-explicit-current-eYw61U`.
- Parent ledger:
  `/Users/redbars/.codex/night-shift-explicit-current-eYw61U/maestro/overnight/night-shift-20260713T202145Z-autopilot`.
- Goal: add a focused behavioral test for `DraftEngine.cleanup` that proves
  it invokes Git worktree removal and pruning.
- Local model: `qwen/qwen3-coder-next` through the Mac-local server.

## Result

- Result: `VERIFIED_DRAFT`.
- Baseline check: `bash scripts/check-package.sh`, exit 0.
- After check: `bash scripts/check-package.sh`, exit 0.
- Sandbox check: exit 0; the isolated package gate passed with 385 tests.
- Changed path: `tests/test_night_shift.py` only.
- Semantic contract: at least one `DraftEngine.cleanup` invocation.
- Worktree cleanup: completed; the source checkout remained untouched.
- Guard reasons: none.
- Local model usage: 1 call, about 3,370 estimated tokens.

The run used local-draft permission, so it created no branch, commit, or
GitHub PR. The morning brief correctly kept the item as a human-review choice
instead of claiming that a model-generated test was automatically useful.

## What this proves

This is direct current-main evidence for fresh setup, explicit-goal routing,
bounded local patch generation, isolated verification, semantic proof, and
cleanup. Together with the separate BetterFeedback proof, it covers two
repositories and two language families. It does not prove repeated useful
outcomes across a portfolio, accepted draft-PR volume, or a completed long
soak.
