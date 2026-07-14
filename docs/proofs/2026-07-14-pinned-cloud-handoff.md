# Pinned Cloud Handoff Proof

Date: 2026-07-14

## Change

Local handoff previews may still use the current checkout for convenience. A
review that would send a bounded pack to a coding agent now requires the
candidate's exact 40-character commit SHA. This prevents a moving checkout from
changing what a sent review is supposed to inspect.

## Deterministic proof

```text
python3 -m unittest \
  tests.test_night_shift.NightShiftQualityTests.test_handoff_prepares_locally_without_cloud_call \
  tests.test_night_shift.NightShiftQualityTests.test_handoff_cloud_run_is_explicit_and_read_only \
  tests.test_night_shift.NightShiftQualityTests.test_handoff_cloud_run_requires_pinned_revision \
  tests.test_night_shift.NightShiftQualityTests.test_handoff_reviews_pinned_revision_when_checkout_has_moved
```

Result: `Ran 4 tests ... OK`.

The full package gate remains required before merge. This proof is still not a
real cloud review, user acceptance, or draft PR.
