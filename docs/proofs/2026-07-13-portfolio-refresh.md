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

The controller previously refreshed the prepared portfolio only after a
no-work cycle. A long productive stretch could therefore keep stale repository
rankings. Refresh now follows an independent wall-clock deadline: at most once
per configured polling interval, regardless of whether the previous cycle
found work. Productive cycles between deadlines reuse safe prepared checkouts,
avoiding a GitHub API and fetch storm.

Each cycle also appends a compact `portfolio-snapshots.jsonl` row with selected
repository, score, primary status, checkout readiness, and PR/issue/failure
counts. Full GitHub payloads are not duplicated into this history, and the
history retains only the latest 256 cycle snapshots.

## Verification

Snapshot tests prove two changing cycles remain independently visible. After a
review caught a misplaced cache declaration, a real bounded controller smoke
completed one current-repo cycle, wrote `portfolio-snapshots.jsonl`, skipped
weak signals at zero model calls, produced an honest YELLOW brief, and exited
zero. Its parent ledger is
`night-shift-20260713T093121Z-autopilot`. `scripts/check-package.sh` then passed
313 tests and package checks.

## Proof boundary

The live discovery and deterministic refresh path are proven separately. A
real two-cycle controller run that observes a changing GitHub signal is still
required, so Multi-repo operation remains 76 rather than moving from code and
one-cycle evidence alone.
