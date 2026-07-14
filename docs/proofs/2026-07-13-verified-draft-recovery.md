# Verified Draft Recovery

This proof compares two fresh, isolated local-draft runs against the same
BetterFeedback repository and candidate family after PR #185.

## First run: safe rejection

- Proof home: `/Users/redbars/.codex/night-shift/draft-retry-proof.20260713`
- Local tokens: 3,516
- The worker returned a valid one-file patch.
- The sandbox caught a wrong assertion: JavaScript `Math.round(-12.5)` is
  `-12`, while the generated test expected `-13%`.
- Result: `REJECT`, `sandbox_rc=1`, `worktree_removed=true`.

Night Shift did not promote the plausible-looking but incorrect test.

## Second run: bounded recovery

- Proof home: `/Users/redbars/.codex/night-shift/draft-retry-2.20260713`
- Local tokens: 3,480
- Source revision: `c8160e7109e496e7048498e667275d309a986678`
- Changed file: `tests/unit/lib/analytics-metrics.test.ts`
- Baseline check: `rc=0`
- Isolated after-patch check: `rc=0`
- Semantic contract: at least one target invocation
- Result: `VERIFIED_DRAFT`
- Worktree removed: yes
- GitHub writes: none

The correction prompt told the worker that a failing expected value can be its
own mistake, then required source/runtime-grounded correction without deleting
the target test. This is useful local autonomy with the deterministic sandbox
still making the final decision.

## Boundary

This proves a verified local draft, not an accepted human change or a hosted
passing PR. No GitHub branch or PR was created by either run.
