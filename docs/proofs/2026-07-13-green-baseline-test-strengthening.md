# Green-Baseline Test Strengthening Proof

Night Shift can now turn a deterministic missing-test signal into a bounded
local patch even when the repository's approved checks already pass. This is a
test-only exception, not general permission to patch green repositories.

## Real run

- Source revision: `370392d9c9858f08a77cb7b35300c1e6f910c92c`
- Parent ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T055957Z-autopilot`
- Child ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T055958Z-afterburner`
- Mission: add a behavioral test for `DraftEngine.cleanup` covering command
  order and both boolean outcomes.
- Planning lane: Mac local `qwen/qwen3-coder-next`, one call, about 3,314 tokens.
- Patch lane: Mac local model, with deterministic test-method materialization.
- Baseline: package checks passed before the patch.
- Result: `VERIFIED_DRAFT`; package checks passed after the patch in the real
  no-network Docker runner; changed paths were exactly
  `tests/test_night_shift.py`; the owner-aware AST check proved a call to
  `DraftEngine.cleanup`; the disposable worktree was removed.
- Patch: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T055957Z-autopilot/drafts/r3dbars--nightshift/mission-brief-cleanup-draft-pr-candidate-sandbox/applied.patch`

The patch proved call ordering and the successful return path. It did not prove
the requested failed-remove return path, so it remains a review candidate and
does not count as full mission completion. No branch or draft PR was published.

## Safety and failure evidence

Earlier bounded rehearsals rejected malformed evidence, invented patch anchors,
invalid Python, a semantically wrong Windows patch, a local context-window
overflow, and an owner-call proof the old scanner could not establish. Those
rejections caused no source-checkout changes. The final path requires all of:

1. one complete Python AST invocation index with zero calls;
2. an existing Python test file and pinned source declaration;
3. a zero-call recheck at the execution boundary;
4. an AST-valid test method with no new import or dependency;
5. deterministic patch generation and `git apply --check`;
6. exact changed-path validation in a no-network tmpfs sandbox;
7. the approved full repository check passing;
8. a post-patch owner-aware invocation proof;
9. disposable worktree cleanup.

Claude's first adversarial review found scope-blind variable tracking and
lifecycle mislabeling. Both were fixed. The follow-up found no blocking issue:
`/Users/redbars/.codex/maestro/runs/20260713T052358Z-night-shift-green-baseline-final-review-claude`.

## Automated gate

`scripts/check-package.sh` passes 264 tests plus package and copied-install
checks. The suite covers forged/incomplete contracts, duplicate invocation
indexes, source-file exclusion, scope and reassignment attacks, missing owner
calls, non-applying patches, deterministic method materialization, Mac routing,
sandbox ownership, and the valid green-baseline promotion path.
