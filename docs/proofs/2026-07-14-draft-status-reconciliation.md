# Draft PR Status Reconciliation

Date: 2026-07-14

## What Changed

Night Shift now has `night-shift reconcile-drafts --repo /path/to/project`.
It reads the local `published-drafts.jsonl` ledger, asks GitHub for the current
`isDraft` and `statusCheckRollup` values of each recorded draft PR, and replaces
the local ledger atomically. It never creates, edits, closes, pushes, or merges
a GitHub object. Unknown GitHub responses remain `unknown` instead of becoming
a pass.

## Verification

- Publisher tests: 14 passed.
- Full package gate: `481 tests, OK`.
- The suite proves both hosted-success refresh and read-failure preservation.
- This Mac currently has no local publication ledger, so no hosted result was
  fabricated and no GitHub write was performed.

## Score Boundary

Draft PR creation remains **92/95**. Reconciliation improves the evidence path,
but the score still needs varied independently useful draft PRs with passing
hosted checks. This change does not claim that outcome.
