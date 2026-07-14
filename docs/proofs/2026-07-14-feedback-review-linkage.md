# Feedback Review Linkage Proof

Date: 2026-07-14

## Change

Morning feedback now links only to the latest valid terminal handoff review for
the exact ledger, item, candidate fingerprint, and source revision. Mismatched
revisions and `NEEDS_INFO` reviews remain unverified.

## Deterministic proof

```text
python3 -m unittest \
  tests.test_night_shift.NightShiftQualityTests.test_latest_verified_review_requires_exact_candidate_identity \
  tests.test_night_shift.NightShiftQualityTests.test_latest_valid_review_verdict_controls_exact_candidate \
  tests.test_night_shift.NightShiftQualityTests.test_feedback_links_exact_valid_handoff_review_to_verified_outcome
...
Ran 3 tests ... OK

bash scripts/check-package.sh
Ran 472 tests ... OK
package checks passed
```

## Boundary

This makes the learning ledger more accurate. It does not count a review as
user acceptance without actual morning feedback.
