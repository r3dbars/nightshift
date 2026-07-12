# Live Windows + Podman Repair Proof

Date: 2026-07-12

This bounded rehearsal used the configured Windows `qwen3-coder:30b` worker
and the real rootless ARM64 Podman runner against a disposable Git repository.

## Result

- Baseline verification: exit 1 with `AssertionError: 1 != 2`.
- Windows patch calls: 2 (one strict formatting correction), about 440 tokens total.
- Approved changed path: `src/app.py` only.
- Isolated verification: exit 0.
- Guard reasons: none.
- Lifecycle: `DISCOVERED -> REPRODUCED -> DIAGNOSED -> PATCHED -> VERIFIED`.
- Final status: `PROVEN_REPAIR` with `failing-before and passing-after` proof.
- Original source after verification: unchanged (`return 1`).
- Original source `git status --short`: empty.
- Disposable worktree removed: yes.

Local proof artifacts were written under:

```text
/tmp/night-shift-live-windows-proof.json
/tmp/night-shift-live-windows-proof/ledger/drafts/proof--live-windows/
~/.codex/maestro/runs/20260712T231809Z-repair-answer-patch-windows/
~/.codex/maestro/runs/20260712T231810Z-repair-answer-retry-patch-windows/
```

## Boundaries

This proves one tiny Python repair in a disposable repository. It does not
prove usefulness on a real project, Docker behavior, Podman restart recovery,
draft PR creation, merging, deployment, or unattended overnight reliability.
