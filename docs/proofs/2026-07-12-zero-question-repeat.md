# Zero-Question Repeat Run Proof

Date: 2026-07-12

## Claim

After one saved setup, a healthy repeat `night-shift start --yes` launches a
real bounded cycle with zero questions, preserves config byte-for-byte, and
reports privacy/routing truthfully.

## Blank-Home Setup

A linked install under a fresh temporary Codex home ran:

```sh
night-shift start --repo /Users/redbars/code/night-shift \
  --mode quiet --scope current --permission brief --guidance scan \
  --privacy mac-only --stop-after 2h --setup-only --yes --skip-smoke
```

It detected the repo, GitHub, Mac local AI, and available hardware, then saved
one setup config and one setup ledger without launching work.

## Real Repeat

The same home then ran:

```sh
night-shift start --yes --once --skip-smoke
```

Measured results:

- Questions asked: 0.
- Runtime: about 7 seconds.
- Exit code: 0.
- Config SHA-256 before/after: identical.
- Setup ledgers after both commands: 1.
- Preview LAN references under `mac-only`: 0.
- Child routing: `mac-only`, Quiet, chores, scan, brief, 2h.
- Model calls/tokens: 0/0 because ten weak signals were skipped before dispatch.
- Portfolio status: YELLOW for no grounded work, without treating that as a
  command failure.
- Morning brief: one repo visited, no unsupported finding, nothing published.

The source checkout had unrelated in-progress changes and Night Shift left them
untouched, as promised.

## Fixes Proven

- Preview tool/mode text respects the saved privacy route.
- A repeat with unchanged semantic config does not rewrite `updated_at` or make
  another setup ledger.
- Healthy no-work cycles remain visibly YELLOW but return success.
- Empty portfolios or checkout failures still require action and return failure;
  only a successfully visited repo with no grounded task is healthy no-work.
- Child ledgers inherit wake goal, privacy route, and configured stop label from
  the parent instead of writing defaults.

## Deterministic Gate

The package gate passes 183 tests. Focused coverage protects privacy-aware
preview text, timestamp-insensitive setup equality, and no-work action status.
