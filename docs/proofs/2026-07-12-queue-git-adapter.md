# Queue Git Revision Adapter Proof

Date: 2026-07-12

## Claim

Queue construction now resolves immutable Git evidence through one strict,
directly tested adapter. Ordinary pinned PR queue output is unchanged; invalid
non-SHA refs and parent-directory paths are deliberately rejected earlier.

## Change

`RepoRevisionAdapter` now owns:

- exact 40-hex commit validation;
- safe relative path validation;
- PR-number and branch-name allowlists;
- local commit availability checks;
- bounded PR/branch fetches followed by immutable commit rechecks;
- ref-scoped file existence and file listing;
- deduped source paths extracted from failed-step logs.

Command execution remains dependency-injected. The controller fell from 4,491
to 4,439 lines and no longer contains nested Git fetch/ref helpers.

## Adversarial Tests

Direct tests prove:

- `HEAD` and other non-SHA refs are rejected;
- malicious PR numbers and option-like/traversing branches never fetch;
- `.git/config` and parent-directory paths never reach `git cat-file`;
- valid PR fetches use the literal `refs/pull/<number>/head` target;
- fetch timeout remains 120 seconds;
- a fetched ref is accepted only after its exact commit becomes available;
- invalid file-list refs never execute Git.

The old nested file-existence helper accepted any non-empty ref and did not
explicitly reject `..` path components. The adapter now requires the same
40-hex immutable SHA used by real queue callers and rejects traversal. This is
an intentional safety tightening, not a universal behavior-parity claim.

## Exact Pinned-PR Parity

The pre-change and current controllers were loaded side by side against the
same real temporary Git repository and fixed pinned PR signal.

- Complete serialized queue parity: yes.
- Items: 6 before and after.
- PR item: `pr-7-review`.
- PR source ref: the exact temporary repository commit SHA in both queues.
- Item ordering and payloads: identical.

## Deterministic Gate

`scripts/check-package.sh` passed all 198 tests and package/install checks.

## Regrade

Maintainability moves from 74 to 77. Queue evidence and Git revision behavior
now have tested module owners, but task assembly, dispatch, and lifecycle still
remain in the controller.
