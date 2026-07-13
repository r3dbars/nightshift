# Portfolio Refresh Proof

Date: 2026-07-13

## Live discovery baseline

A read-only 30-day GitHub discovery selected five owned repositories:

| Repository | Score | PRs | Issues | Failed runs |
| --- | ---: | ---: | ---: | ---: |
| r3dbars/BetterFeedback | 560 | 1 | 1 | 3 |
| r3dbars/transcripted | 144 | 2 | 0 | 0 |
| r3dbars/nightshift | 120 | 0 | 0 | 0 |
| r3dbars/steadytype | 115 | 3 | 0 | 0 |
| r3dbars/Draft | 110 | 2 | 14 | 0 |

The explicit Night Shift primary repository remained selected even though
three other repositories had higher live scores.

## Controller defect fixed

The controller previously cached the prepared portfolio after a productive
cycle. It could run another cycle against stale repository rankings before a
no-work cycle cleared that cache. Every cycle now rediscovers live GitHub
signals and revalidates each checkout before assigning task capacity.

Each cycle also appends a compact `portfolio-snapshots.jsonl` row with selected
repository, score, primary status, checkout readiness, and PR/issue/failure
counts. Full GitHub payloads are not duplicated into this history.

## Verification

Snapshot tests prove two changing cycles remain independently visible, and
`scripts/check-package.sh` passed 312 tests and package checks.

## Proof boundary

The live discovery and deterministic refresh path are proven separately. A
real two-cycle controller run that observes a changing GitHub signal is still
required, so Multi-repo operation remains 76 rather than moving from code and
one-cycle evidence alone.
