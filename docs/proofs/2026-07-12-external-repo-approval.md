# External Repo Approval Proof

Date: 2026-07-12

## Claim

An owner can enable isolated verification with one explicit consent without
editing the target repository.

## Real Draft Preview

A blank Night Shift home previewed approval for the real `r3dbars/Draft` repo:

```sh
night-shift trust-repo --repo /tmp/.../r3dbars--Draft-...
```

The command proved the authenticated GitHub owner, detected
`bash run-tests.sh`, showed the disposable-worktree path allowlist, stated that
the original checkout is read-only and GitHub writes stay disabled, and saved
nothing. The Draft checkout remained clean.

## Real Apply Rehearsal

A disposable fresh clone used the existing owned `r3dbars/nightshift` remote at
an advertised commit and exposed the detected unittest command.
The real command ran with `--apply --yes`:

- GitHub ownership proof passed.
- The immutable Docker runner built successfully.
- Approval was stored under the blank Night Shift home, not the repo.
- Approval file mode was `0600`; its parent directory was private.
- The approval was bound to the exact Git remote hash, and loading requires the
  current commit SHA to be advertised by that remote.
- `night-shift doctor` reported the repo profile, Colima provider, and sandbox
  as `GREEN`.
- GitHub writes remained disabled.
- The repo checkout remained clean.

The apply rehearsal used a disposable repo because granting execution consent
for Draft requires the owner's direct approval. No project repo was modified.

## Fail-Closed Rules

- Local `.night-shift.json` policy still takes precedence for advanced users.
- Missing, changed, tampered, or spoofed Git remotes do not load an external
  approval; the current commit must exist on an advertised remote branch or tag.
- Invalid profile data does not execute.
- Approval writes are atomic and reject symlinked targets.
- The full protected-path policy remains active.

## Deterministic Gate

The package gate passes 174 tests. Focused tests cover advertised-revision
binding, spoof/tamper rejection, local-profile precedence, private permissions,
and target/directory symlink refusal.
