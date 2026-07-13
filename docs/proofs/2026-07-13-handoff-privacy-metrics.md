# Handoff Privacy And Effort Metrics

Date: 2026-07-13

## Real bounded-pack exercise

Night Shift rebuilt the handoff pack for the real pinned ledger
`night-shift-20260712T191935Z-quiet` without invoking a cloud agent. Saved cloud
consent was false, so no data was sent.

The local exercise materialized only the two allowlisted committed files:

- `tests/test_night_shift.py`
- `bin/night_shift_patch_protocol.py`

Measured payload:

```json
{
  "materialized_bytes": 215728,
  "materialized_file_count": 2,
  "prompt_bytes": 1993,
  "privacy_reasons": [],
  "redaction_markers": 10
}
```

## New boundary

Before a cloud call, Night Shift now rejects a bounded pack if the redacted
prompt exposes the source checkout path or if any prompt/materialized file still
matches a supported secret format. Completed review metadata records prompt
bytes, materialized bytes/files, redaction markers, review output bytes, and
elapsed review seconds.

## Verification

Focused tests prove surviving secrets fail closed and metrics count only the
bounded payload. `scripts/check-package.sh` passed 311 tests and package checks.

## Proof boundary

Prior proofs already cover three varied real pinned cloud reviews. This run
adds deterministic leakage and effort measurement without overriding disabled
cloud consent. It does not yet prove low review effort over a larger repeated
sample or accepted implementations downstream.
