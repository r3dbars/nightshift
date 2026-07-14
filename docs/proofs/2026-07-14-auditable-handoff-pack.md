# Auditable Local Handoff Pack

Date: 2026-07-14

## What Changed

PR #235 keeps the already-redacted, explicitly allowlisted review files in the
ledger so a person can inspect the exact bounded pack before any optional
cloud review. It also writes a small JSON manifest with file hashes, byte
counts, redaction count, privacy result, source revision, and send status.
PR #236 adds the conversational local feedback path, but it does not change
the handoff consent boundary.

## Real Reproduction

The active Mac-plus-Windows portfolio ledger was:

`/Users/redbars/.codex/maestro/overnight/night-shift-20260714T173533Z-autopilot`

The current morning item was a `MAYBE` candidate for a behavioral test around
`utc_now()`. The local-only command was:

```text
bin/night-shift handoff --ledger /Users/redbars/.codex/maestro/overnight/night-shift-20260714T173533Z-autopilot --item 1
```

It returned:

```text
NIGHTSHIFT_HANDOFF: GREEN | prepared item=1 | agent=codex
Handoff pack: files=2 bytes=9561 prompt_bytes=1737 redactions=0 privacy=GREEN
Nothing was sent. Review the saved pack, then add --run for one explicitly approved review.
```

The saved manifest recorded:

- source revision: `750411b2ccf75d7c4e4d604921ae6d1ecb2a59e5`;
- files: `bin/night_shift_state.py` and `tests/test_night_shift_state.py`;
- two SHA-256 file hashes and 9,561 materialized bytes;
- `privacy=GREEN`, no privacy reasons, and `sent=false`.

The agent path still copies those redacted files into a fresh temporary
read-only review directory. The durable saved pack is not used as a writable
agent workspace.

## Honest Result

This proves a person can inspect exactly what would be sent, and that preview
mode sends nothing. It does not prove that a cloud review was authorized,
useful, or accepted by a human. Cloud handoff remains 88/95 and learning
remains 90/95 until those separate outcomes exist.

## Verification

`bash scripts/check-package.sh` passed 447 tests plus package checks for PR
#235. The follow-up PR #236 passed 448 tests plus package checks and added the
local interactive feedback regression.
