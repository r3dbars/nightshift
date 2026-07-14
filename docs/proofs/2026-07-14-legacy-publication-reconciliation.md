# Legacy Publication Reconciliation

Date: 2026-07-14

## What Changed

The read-only `reconcile-drafts` command now recognizes publication rows from
older Night Shift versions that have a PR URL but no explicit status. It
normalizes those rows to `DRAFT_PR_OPENED` while refreshing draft and hosted
check evidence, so existing local ledgers are not stranded by the newer
status field.

## Verification

- The focused publisher suite passed: `16 tests, OK`.
- A legacy publication row was reconciled to `DRAFT_PR_OPENED`, `draft`, and
  explicit hosted-check `passed` state in a temporary ledger.
- The full package gate passed: `485 tests, OK`.
- The reconciliation path remains read-only with respect to GitHub; no create,
  edit, close, push, merge, deploy, or source-checkout write occurred.

## Honest Score Boundary

Draft PR creation remains **92/95**. This improves compatibility for existing
users, but varied independently useful draft PRs with passing hosted checks
are still required for a higher score.
