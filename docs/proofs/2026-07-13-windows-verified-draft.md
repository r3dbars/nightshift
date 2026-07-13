# Windows Verified Draft Proof: 2026-07-13

This is a live Windows-lane proof, not a model-only claim.

## Run

- Repository: `r3dbars/BetterFeedback`
- Source revision: `c8160e7109e496e7048498e667275d309a986678`
- Worker: private LAN Ollama at `192.168.7.201:11434`
- Model: `qwen3-coder:30b`
- Patch lane: Windows
- Mode: `draft-local`
- Permission: explicit saved draft consent
- Tokens: about 11,010 across 3 Windows calls
- Parent ledger: `/Users/redbars/.codex/night-shift-bf-windows-proof-Cb5hHH/maestro/overnight/night-shift-20260713T211209Z-autopilot`
- Child ledger: `/Users/redbars/.codex/night-shift-bf-windows-proof-Cb5hHH/maestro/overnight/night-shift-20260713T211211Z-quiet`

## Deterministic result

Night Shift selected the zero-invocation `formatPercent` test gap, created a
one-file patch in `tests/unit/lib/analytics-metrics.test.ts`, and recorded:

- `baseline_rc=0`
- `patch_worker_rc=0`
- `sandbox_rc=0`
- `after_rc=0`
- `guard_reasons=[]`
- `status=VERIFIED_DRAFT`
- semantic contract: at least one invocation of the target
- temporary worktree removed: `true`

The isolated sandbox ran the repository's real `npm run test:unit:vitest`
command. The source checkout remained unchanged. No PR was opened, merged, or
published by this run.

## Why it counts

The worker response is only a draft. The score-bearing evidence is the
immutable source revision, exact changed-path record, passing baseline and
post-patch repository checks, passing isolated sandbox, semantic invocation
proof, and cleanup record above.

