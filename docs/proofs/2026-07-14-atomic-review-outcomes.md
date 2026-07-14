# Atomic Review Outcome Proof

Date: 2026-07-14

## Change

Validated cloud-review outcomes now use a bounded, synced temporary file and an
atomic replacement. If replacement fails, the previous review rows remain
intact and the temporary file is removed.

## Deterministic proof

The regression test patches the replacement operation to fail after a prior
row exists and verifies that the prior row is unchanged:

```text
python3 -m unittest tests.test_night_shift.NightShiftQualityTests.test_review_outcome_ledger_preserves_rows_when_atomic_replace_fails
```

Result: `Ran 1 test ... OK`.

This improves learning-state durability. It does not count a review outcome as
useful unless a real review and user feedback occurred.
