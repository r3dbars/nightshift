# Semantic Test Contract Proof

Night Shift now rejects test-strengthening drafts unless it can derive and
audit an explicit behavioral contract from the user's mission. Passing tests
alone are not enough.

## Successful bounded repair

- Source revision: `ebb1a9c0280311c24d1c5e594e965033e593c111`
- Ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T062801Z-autopilot`
- Result: `VERIFIED_DRAFT`, `after_rc=0`, no guard reasons, worktree removed.
- Local model: Mac `qwen/qwen3-coder-next`.
- Behavior required: two `DraftEngine.cleanup` calls, ordered remove then prune
  assertions, and assertions for both boolean outcomes.
- The first generated patch failed the real package check. One bounded repair
  used that failure, produced an applyable test-only patch, and passed all 270
  tests in the no-network Docker runner.

## Auditable fail-closed run

- Source revision: `9fee62a2720aabc9f2b7da7c2300a34659849f9f`
- Ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T063333Z-autopilot`
- Result: `REJECT`, `after_rc=1`, worktree removed.
- The result JSON and lifecycle both preserve the exact semantic contract.
- Exactly two verification repair artifacts and two repair sandboxes exist.
- The final patch still failed verification and ordered-assertion evidence, so
  Night Shift stopped without publishing or touching the source checkout.

## Review and gate

- Initial adversarial review:
  `/Users/redbars/.codex/maestro/runs/20260713T062933Z-night-shift-semantic-contract-adversarial-claude`
- Final adversarial review, no merge blockers:
  `/Users/redbars/.codex/maestro/runs/20260713T063508Z-night-shift-semantic-contract-final-review-claude`
- `scripts/check-package.sh`: 269 tests plus package and copied-install checks
  pass.

This proves one successful semantic repair and one honest bounded rejection on
one Python repository. It does not prove varied-repository usefulness, draft PR
quality, or overnight outcome rates.
