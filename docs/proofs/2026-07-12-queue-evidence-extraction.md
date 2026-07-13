# Queue Evidence Extraction Proof

Date: 2026-07-12

## Claim

Repository evidence indexing now has a bounded, directly tested module owner,
while complete queue output remains identical to the pre-extraction controller.

## Change

`bin/night_shift_queue.py` now owns:

- bounded text reads with binary rejection;
- exact identifier matching;
- test-path classification;
- issue-symbol-to-source ranking;
- the 8 MiB bounded test corpus;
- complete/incomplete coverage-index evidence.

The controller uses `QueueEvidenceIndex` as its repository-read adapter. It fell
from 4,592 to 4,491 lines. Queue task assembly and Git revision/fetch validation
remain in the controller for the next extraction phase.

## Exact Parity

The controller from `origin/main` before this change and the current controller
were loaded side by side. Both received the same temporary repository and fixed
scan containing source, tests, a verification command, and a symbol-specific
GitHub issue.

The complete queues were serialized with sorted keys and compared byte for
byte:

- Parity: yes.
- Old items: 6.
- New items: 6.
- Order: coverage lead, changed-file proof, issue action, test-command proof,
  test-contract map, source map.

This protects item order, selection priorities, verification commands, and
coverage evidence, not merely the number of tasks.

## Deterministic Gate

`scripts/check-package.sh` passed all 195 tests and package/install checks.
Direct tests cover complete and incomplete corpus evidence, binary rejection,
exact issue symbol ranking, identifier boundaries, and test-path boundaries.

## Regrade

Maintainability moves from 71 to 74. Setup, admission, and repository evidence
policy now have tested owners, but queue task assembly, Git ref validation,
dispatch, and lifecycle remain in the controller.
