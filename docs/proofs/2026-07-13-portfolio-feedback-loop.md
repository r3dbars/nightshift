# Portfolio Feedback Loop Proof

Night Shift now binds each parent portfolio morning number to the exact child
candidate the user saw. Feedback no longer depends on guessing which child
ledger or raw queue row the parent meant.

## Real run

- Source revision: `48dc613423a5bfcd8a4f19e43af6787d93e83a71`
- Parent ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T064655Z-autopilot`
- Child ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T064656Z-afterburner`
- Parent morning item 1 recorded the canonical repo path, child ledger, source
  revision, fingerprint, family, score, and summary.
- The printed `night-shift feedback --ledger ... --item 1 --useful` command was
  run twice with isolated local state at
  `/tmp/night-shift-feedback-proof.qDrb6q`.
- The first call wrote one event. The second returned GREEN but explicitly said
  the vote was already saved; the JSONL remained one line.
- No real user feedback or production ranking state was changed by this proof.

## Safety and correctness

- Changed verdicts remain in history, but only the latest verdict for an exact
  repo, family, and candidate affects scoring.
- Portfolio checkout paths are canonicalized before persistence, preventing
  macOS `/tmp` or cached-repo symlink aliases from silently missing the child
  run's canonical repo identity.
- Rejected model output creates no fake morning choice. A separate real run at
  `night-shift-20260713T064600Z-autopilot` produced an empty
  `morning-items.json` after its only candidate was rejected.

## Review and gate

- Initial review found the cached-checkout identity blocker:
  `/Users/redbars/.codex/maestro/runs/20260713T064749Z-night-shift-portfolio-feedback-review-claude`
- Final adversarial review returned MERGE:
  `/Users/redbars/.codex/maestro/runs/20260713T065206Z-night-shift-portfolio-feedback-final-review-claude`
- `scripts/check-package.sh`: 272 tests plus package and copied-install checks
  pass.

This proves exact same-morning capture and idempotency. It does not prove that
feedback improves accepted outcomes over multiple nights; that remains required
before the learning loop can approach 95.
