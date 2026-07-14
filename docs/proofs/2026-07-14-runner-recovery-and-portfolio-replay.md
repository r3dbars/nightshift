# Runner recovery and portfolio replay

Date: 2026-07-14

This proof covers a real local dependency-recovery path and a current-main
portfolio replay. No cloud handoff, GitHub write, draft PR, commit, or merge was
enabled by either replay.

## Dependency recovery

- Repository: `r3dbars/BetterFeedback`
- Initial local run: `/Users/redbars/.codex/maestro/overnight/night-shift-20260714T164140Z-autopilot`
- Result: rejected honestly because the isolated runner returned `rc=127` and
  `vitest` was unavailable.
- Recovery: `night-shift trust-repo --repo <checkout> --apply --yes
  --prepare-dependencies` prepared the Linux-native cache at
  `/Users/redbars/.codex/night-shift/dependency-cache/e5b5d2bf6563f50c9ad5460bc938f270/node_modules`.
- Replay: `/Users/redbars/.codex/maestro/overnight/night-shift-20260714T164448Z-autopilot`
- Result: one `VERIFIED_DRAFT`, `npm run test:unit:vitest` passed, 3,710
  estimated local tokens, and the canonical checkout stayed untouched.

The failed run is retained as a useful boundary: the runner did not call a
missing tool a passing test. The recovery path now leaves a clear cause in the
morning brief instead of only saying that verification failed.

## Portfolio replay

- Parent ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260714T164616Z-autopilot`
- Scope: three current GitHub repositories, Mac-only routing, one cycle.
- Repositories visited: `r3dbars/BetterFeedback`, `r3dbars/suckscancer.com`,
  and `r3dbars/transcripted`.
- Weak-signal behavior: the first two repos were inspected and skipped before
  model dispatch; the third produced one unproven candidate that stayed
  rejected from the morning result.
- Spend: two local calls, 5,264 estimated tokens, zero Windows calls.

This is selection, privacy, and honest rejection evidence. It is not counted as
an accepted outcome or a passing hosted draft PR.
