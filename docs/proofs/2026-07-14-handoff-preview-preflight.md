# Handoff Preview Preflight

Date: 2026-07-14

## What Changed

The morning brief now gives the user a safe local handoff-preview command first.
It no longer presents `--run --allow-cloud` as the default copied action. The
preview builds the same bounded, redacted pack as before, sends nothing, and
prints a deterministic `CLOUD_PREFLIGHT` result.

The preflight is `GREEN` only when the pack contains committed files, the
candidate has an exact 40-character commit SHA, the selected review agent is
available, and privacy validation passed. Otherwise it lists the blocking
reasons without making a cloud call. A user must still add both `--run` and
`--allow-cloud` for one explicit review.

## Real Preview

Against the completed local ledger
`/Users/redbars/.codex/maestro/overnight/night-shift-20260714T174404Z-night-shift`,
the preview prepared two committed files and returned:

```text
CLOUD_PREFLIGHT: GREEN | exact revision pinned, agent available, bounded pack passed privacy checks
Nothing was sent. Review the saved pack first; add --run --allow-cloud only if you explicitly approve this one review.
```

The saved pack and manifest remain under that ledger's `handoff/` directory.
No cloud call was made.

## Verification

- Focused handoff/reporting tests: 5 passed.
- Full package gate: `479 tests, OK`.
- No cloud handoff, GitHub write, draft PR, merge, or deployment occurred.
- The scorecard remains conservative: Cloud-agent handoff stays **88/95** and
  Morning UX stays **94/95** because user-approved review volume and
  comprehension evidence are still missing.

## Files

- `bin/night_shift_handoff.py`
- `bin/night-shift`
- `bin/night_shift_reporting.py`
- `bin/night_shift_portfolio_reporting.py`
- `tests/test_night_shift.py`
- `tests/test_night_shift_reporting.py`
