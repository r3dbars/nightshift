# Remote Publication Dedupe

Date: 2026-07-13

## Gap fixed

Publication previously used a timestamp plus patch fingerprint for each branch
and relied on a local publication ledger for duplicate prevention. Losing that
local file could give the same verified patch a new branch name and permit a
second draft PR.

Future publication branches are now deterministic:

```text
night-shift/<12-character verified-patch fingerprint>
```

Before creating a worktree or pushing, Night Shift queries all GitHub PR states
for that exact branch. An open, closed, or merged PR rejects the publication and
reports its URL. An unreadable GitHub result also rejects; absence must be
proven. The local ledger remains a faster first boundary.

## Existing live proof

The prior real rehearsal remains GitHub PR #24. GitHub currently confirms it is
a closed, unmerged draft with one approved documentation file. Its isolated
worktree was removed and replay was rejected. Saved publication authorization
is currently off, so this change did not push a branch or open another PR.

## Verification

The new regression deletes the local-ledger assumption, returns existing remote
PR history, and proves there is no worktree creation or push. Existing tests
still cover fresh sandbox verification, ambiguous push cleanup, non-draft PR
closure, branch collision, timeout recovery, ownership, and exact default-branch
ancestry. `scripts/check-package.sh` passed 317 tests and package checks.

## Proof boundary

This closes a duplicate-publication failure mode without exercising a new
GitHub write. Draft PR creation remains 78 until independently useful tested
draft PRs are opened across varied repositories during authorized unattended
runs.
