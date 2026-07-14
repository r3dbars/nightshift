# Mac-Only Routing Proof

Date: 2026-07-14

## Goal

Verify that a new-user `night-shift start --privacy mac-only` run cannot call
the Windows worker, even when the machine has an older Windows URL or model
setting available.

## Reproduction Before PR #194

A clean BetterFeedback run was started with `--privacy mac-only`, but its
morning brief reported `Windows loops: 2`. The saved config said
`privacy_route=mac-only`, so the route was being recorded but not enforced by
the scheduler.

## Fix

PR #194 closes the Windows scheduler lane for every route except the explicit
`mac-and-lan` choice. The run ledger also records the effective route and lane
cap so the result can be checked without trusting the terminal summary.

## Fresh Current-Main Replay

Command:

```sh
CODEX_HOME=/Users/redbars/.codex/night-shift/betterfeedback-mac-only.MfwjWT \
  /Users/redbars/code/night-shift/bin/night-shift start \
  --repo /Users/redbars/.codex/night-shift/repos/r3dbars--BetterFeedback \
  --scope current --mode night-shift --permission draft-local \
  --execute-drafts --guidance scan --privacy mac-only --stop-after 2h \
  --local-url http://localhost:1234/v1 \
  --local-model qwen/qwen3-coder-next --skip-smoke --yes --once
```

Observed result:

```text
NIGHTSHIFT_RUN: YELLOW | mode=night-shift | local=2 | windows=0 | tokens=9481
MAC_ONLY_PROOF: GREEN | privacy_route=mac-only | windows_calls=0 | local_calls_present=yes
```

The ledger recorded `max_windows=0` and `privacy_route=mac-only`. The token
report contained local calls only and no Windows lane entry. The clean source
checkout stayed unchanged; no GitHub write occurred.

## Package Gate

PR #194 passed the Ubuntu and macOS hosted package checks. The local package
gate passed 412 tests.
