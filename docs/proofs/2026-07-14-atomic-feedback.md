# Atomic Feedback Ledger Proof

Date: 2026-07-14

## Change

Local morning feedback now writes through a synced temporary file and atomic
replacement. If the replacement fails, the previous votes remain intact and
the temporary file is removed.

## Deterministic proof

```text
python3 -m unittest tests.test_night_shift.NightShiftQualityTests.test_feedback_ledger_preserves_rows_when_atomic_replace_fails
```

Result: `Ran 1 test ... OK`.

The full package gate passed 470 tests. This protects the learning signal's
durability; it does not turn a vote into an accepted outcome or raise the
learning score without real user-rated evidence.
