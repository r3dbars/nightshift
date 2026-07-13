# Automatic Python Test Draft Proof

Night Shift can now reach a verified healthy-repo test draft from automatic
scanning, without goal text naming the target method.

## Baseline failure

A live three-repo scan visited BetterFeedback, Transcripted, and Night Shift:

- Parent ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T071022Z-autopilot`.
- Six planned tasks consumed about 34,491 local tokens.
- Zero worker results survived the evidence gate.
- Automatic coverage used textual absence, while green-repo drafting required
  complete owner-aware AST evidence. No draft was attempted.

## Successful no-goal run

- Source revision: `7019240551d89a303cd8a4f02e320677d77bf765`.
- Parent ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T072440Z-autopilot`.
- Child ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T072441Z-afterburner`.
- Guidance: automatic scan; no explicit goal text.
- Selected target: `PortfolioReportEngine.morning_items`.
- Result: `VERIFIED_DRAFT`, baseline and after checks passed, no guard reasons,
  exact test-only changed path, semantic minimum invocation satisfied, and
  disposable worktree removed.
- The no-network sandbox passed all 283 tests plus package/install checks.
- The parent morning brief truthfully called it a verified local draft requiring
  human usefulness review. No branch or PR was published.

## Safety boundaries

- Automatic drafting requires Python class ownership, complete Python AST
  analysis, zero owner-aware calls, a pinned source declaration, an existing
  test file, approved verification, and a semantic invocation contract.
- Top-level Python, non-Python, incomplete indexes, and textual-only gaps remain
  analysis-only.
- Same-name methods are scoped to their exact class for both call absence and
  source citations. A test covers a top-level `save`, tested `Alpha.save`, and
  untested `Beta.save` collision.
- Same-class test factories count only when they have exactly one return and it
  directly constructs the required owner; a factory returning another type is
  rejected.

## Review

- Initial review found owner-unspecific source citations:
  `/Users/redbars/.codex/maestro/runs/20260713T072614Z-night-shift-automatic-python-drafts-review-claude`.
- Final adversarial review returned MERGE:
  `/Users/redbars/.codex/maestro/runs/20260713T073041Z-night-shift-automatic-python-drafts-final-review-claude`.
- Host gate: 283 tests plus package and copied-install checks pass.

This proves automatic useful drafting for one Python repository. It does not
prove varied-language or varied-repository usefulness, accepted draft PRs, or
multi-night outcome rates.
