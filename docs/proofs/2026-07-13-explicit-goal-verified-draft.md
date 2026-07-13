# Explicit Goal Verified Draft Proof

This run proves the current Night Shift main branch can turn a plain-language
behavioral goal into a bounded, locally verified draft without touching the
source checkout.

## Run

- Source revision: `d5053c4d0e...` (current merged `main`).
- Fresh install and trust home:
  `/Users/redbars/.codex/maestro/overnight/night-shift-python-proof-12`.
- Parent ledger:
  `/Users/redbars/.codex/maestro/overnight/night-shift-python-proof-12/.codex/maestro/overnight/night-shift-20260713T193102Z-autopilot`.
- Mission: add a focused behavioral test for `DraftEngine.cleanup` that proves
  it invokes Git worktree removal and pruning.
- Local model: `qwen/qwen3-coder-next` through the Mac-local server.

## Result

- Result: `VERIFIED_DRAFT`.
- Baseline check: `bash scripts/check-package.sh`, exit 0.
- After check: `bash scripts/check-package.sh`, exit 0.
- Sandbox check: exit 0; the candidate suite ran 383 tests and package checks
  passed.
- Changed path: `tests/test_night_shift.py` only.
- Semantic contract: at least one `DraftEngine.cleanup` invocation, with two
  ordered Git command assertions.
- Worktree cleanup: completed; the source checkout remained untouched.
- Guard reasons: none.

The worker first produced the focused test patch, and the deterministic
protocol validated the changed path, source revision, semantic invocation, and
real repository gate before accepting the draft. No branch, commit, or GitHub
PR was created in this run because it used local-draft permission.

## What this proves

This is direct evidence for task specificity and deterministic proof on the
Night Shift repository itself. Together with the separate BetterFeedback
TypeScript run, it shows the same goal-to-proof path working across two
repositories and two language families. It is not evidence for repeated
accepted PR volume, multi-repo overnight usefulness, or the unfinished long
soaks.
