# Live Mac + Podman Repair Proof

Date: 2026-07-12

This bounded rehearsal used the Mac-local `qwen/qwen3-coder-next` model and
the real rootless ARM64 Podman runner. The Windows endpoint was excluded.

## Result

- Baseline verification: exit 1 with `AssertionError: 1 != 2`.
- Mac-local patch calls: 2 (one strict formatting correction), about 440 tokens total.
- Approved changed path: `src/app.py` only.
- Isolated verification: exit 0.
- Guard reasons: none.
- Lifecycle: `DISCOVERED -> REPRODUCED -> DIAGNOSED -> PATCHED -> VERIFIED`.
- Final status: `PROVEN_REPAIR` with `patch_lane: local`.
- Original source after verification: unchanged (`return 1`).
- Original source `git status --short`: empty.
- Disposable worktree removed: yes.

Local proof artifacts were written under:

```text
/tmp/night-shift-live-mac-proof.json
/tmp/night-shift-live-mac-proof/ledger/drafts/proof--live-mac/
~/.codex/maestro/runs/20260712T233142Z-repair-answer-patch-local/
~/.codex/maestro/runs/20260712T233144Z-repair-answer-retry-patch-local/
```

## Boundaries

This proves one tiny Python repair in a disposable repository. It does not
prove usefulness on a real project, unattended overnight reliability, Docker,
draft PR creation, merging, or deployment.

Publication behavior is proven separately so these evidence boundaries stay explicit.
