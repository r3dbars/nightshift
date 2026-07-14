# Explicit Compute-Lane Disable Proof

This proof checks that a user can run a bounded Windows-only shift without a
saved Mac model or Mac environment variable silently reactivating local work.

## Live run

- Command: isolated `autopilot --scope current --mode quiet --permission brief --no-local --privacy mac-and-lan --once`.
- Repository: `r3dbars/BetterFeedback`, clean approved checkout at `c8160e7`.
- Parent ledger: `/tmp/night-shift-windows-only.chIb6k/maestro/overnight/night-shift-20260714T184820Z-autopilot`.
- Child ledger: `/tmp/night-shift-windows-only.chIb6k/maestro/overnight/night-shift-20260714T184822Z-quiet`.
- Result: `NIGHTSHIFT_AUTOPILOT: YELLOW | cycles=1`; the candidate remained a draft and no patch or PR was opened.

## Evidence

- Parent cycle recorded `local=0` and `windows=1` with 4,712 estimated tokens.
- `processes.tsv` contains one `maestro-delegate windows` process and no local process.
- `startup-gate.md` records `SKIPPED local-models` and `SKIPPED local-chat`, while the Windows worker and Windows chat are GREEN.
- The source checkout stayed clean; no GitHub write, merge, deploy, or cloud handoff occurred.

A mirrored Mac-only replay used `--no-windows` with the same repository and a
real LM Studio call:

- Parent ledger: `/tmp/night-shift-mac-only.4yyBSM/maestro/overnight/night-shift-20260714T185024Z-autopilot`.
- Child ledger: `/tmp/night-shift-mac-only.4yyBSM/maestro/overnight/night-shift-20260714T185027Z-quiet`.
- Result: `local=1`, `windows=0`, 3,548 estimated tokens; `processes.tsv` contains only a local worker process.
- The Windows worker was disabled for the shift even though the privacy route allowed LAN compute.

## Boundary

This proves explicit lane routing and disabled-lane health behavior. It does not
prove that the MAYBE candidate is a useful accepted change; it still requires
deterministic verification and human review.
