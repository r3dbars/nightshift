# Handoff Citation Allowlist Proof

Date: 2026-07-14

## Change

The read-only cloud-agent handoff validator now rejects a review when any cited
repository path is outside the files materialized into the bounded review pack.
A review cannot pass by mixing one allowed citation with an unrelated
out-of-pack citation.

## Deterministic proof

Command:

```text
python3 -m unittest tests.test_night_shift.NightShiftQualityTests.test_handoff_review_rejects_citation_outside_materialized_allowlist
```

Result: `Ran 1 test ... OK`

The full package gate also passed:

```text
bash scripts/check-package.sh
```

Result: `Ran 464 tests ... OK` and `package checks passed`.

## Boundary

This strengthens review integrity only. It does not count as a real cloud
review, a user acceptance, or a draft PR. The cloud-agent handoff score stays
conservative until those real outcomes are explicitly authorized and observed.
