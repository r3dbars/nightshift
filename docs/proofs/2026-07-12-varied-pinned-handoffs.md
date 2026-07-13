# Varied pinned-revision handoff proof

Date: 2026-07-12

## Claim

Night Shift can independently review a saved morning candidate after the live
checkout has moved, while sending only allowlisted files from the candidate's
exact committed revision to an ephemeral read-only Codex process.

## Real runs

The handoff command ran with explicit one-time `--allow-cloud` consent against
three existing ledgers and three different repositories:

| Repository | Pinned revision | Files | Valid review | Verdict |
| --- | --- | ---: | --- | --- |
| Night Shift | `29e4ae657efe1a54226b65e2adfadf7ea08d84d4` | 2 | yes | CONFIRMED |
| Draft | `23403c7aa58bb7f5cfa5300e4bcb6e0d8f7dbf7a` | 2 | yes | CONFIRMED |
| BetterFeedback | `69a08846e76b86e91a0ab518414ec3b24085098e` | 2 | yes | REJECTED |

Each exact commit existed locally, while each repository's current checkout was
free to differ. `git show <source_ref>:<path>` materialized only the listed files
into a temporary directory. Codex ran with `--ephemeral --sandbox read-only` and
`--skip-git-repo-check`. The temporary directory was removed afterward.

The BetterFeedback rejection was useful: the supplied test covered a different
route and could not prove the candidate claim. No implementation or GitHub write
was attempted for any item.

## Automated and independent checks

- `scripts/check-package.sh`: 236 tests plus package/install checks passed.
- Focused tests prove moved-checkout success, missing-commit rejection, exact-SHA
  rejection, allowlisted materialization, and read-only invocation.
- Claude found no correctness or security bug and confirmed that checkout
  equality was unnecessary because review files are revision-addressed.
- Claude proof: `/Users/redbars/.codex/maestro/runs/20260713T040459Z-night-shift-pinned-handoff-review-claude`.

## Boundary

This proves three varied, pinned, read-only review handoffs. It does not prove
that the underlying candidates become accepted patches or draft PRs, and it does
not establish a measured user-feedback learning lift.
