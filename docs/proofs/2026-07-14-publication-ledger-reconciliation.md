# Publication Ledger Reconciliation

Date: 2026-07-14

## What Changed

Published draft PR records now include the `DRAFT_PR_OPENED` status that the
read-only `night-shift reconcile-drafts` command requires. Before this fix,
publication succeeded but reconciliation skipped the record because the
status field was absent.

## Verification

- The focused publisher suite passed: `15 tests, OK`.
- The regression publishes a verified draft through a scripted GitHub boundary,
  reads the recorded ledger, then reconciles it with a read-only status query.
- The regression confirms the reconciled record is still a draft and reports
  explicit hosted-check success.
- The full package gate passed: `483 tests, OK`.
- No real GitHub write, merge, deploy, or source-checkout edit occurred during
  this proof.

## Honest Score Boundary

Draft PR creation remains **92/95** and GitHub usefulness remains **94/95**.
The ledger path is now reliable, but varied independently useful draft PRs and
repeated accepted hosted outcomes still require real user-authorized runs.
