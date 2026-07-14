# Review Feedback Reconciliation Proof

Date: 2026-07-14

## Change

If a user records morning feedback before the independent handoff review
finishes, the later valid `CONFIRMED` or `REJECTED` review now upgrades the
same feedback event and repo-outcome row in place. The match requires the
canonical ledger, displayed item, candidate fingerprint, and pinned source
revision. Missing identity, mismatched candidates, and `NEEDS_INFO` remain
unverified.

## Deterministic proof

```text
python3 -m unittest \
  tests.test_night_shift.NightShiftQualityTests.test_later_review_reconciles_feedback_recorded_first_without_duplicate_vote \
  tests.test_night_shift.NightShiftQualityTests.test_feedback_links_exact_valid_handoff_review_to_verified_outcome \
  tests.test_night_shift.NightShiftQualityTests.test_review_outcome_history_preserves_verdict_transitions
...
Ran 3 tests ... OK

bash scripts/check-package.sh
Ran 473 tests ... OK
package checks passed
```

## Boundary

This repairs the order of local learning records. It does not create a review,
claim user acceptance, send cloud data, or perform a GitHub write.
