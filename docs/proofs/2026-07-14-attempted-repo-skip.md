# One Draft Attempt Per Repo Per Shift

Date: 2026-07-14

## What Changed

PR #239 makes autopilot stop spending model calls on a repository after one
draft attempt during the current shift. This applies to verified drafts,
rejected drafts, and unavailable execution providers. A rejected repository is
marked with a clear retry-next-shift reason; the in-memory gate resets when a
new shift starts.

## Real Launchd Reproduction

The live Mac launch used merged revision `ee739c8` with:

```text
com.redbars.nightshift.final95.v3
scope=github-recent max-repos=3 privacy=mac-and-lan
permission=draft-local execute-drafts=true poll-minutes=1
```

Parent ledger:

`/Users/redbars/.codex/maestro/overnight/night-shift-20260714T182107Z-autopilot`

Cycle 1 visited BetterFeedback and suckscancer.com without model calls. The
Night Shift repository produced one grounded candidate, made one local model
call, and safely rejected a malformed patch:

```text
status=REJECT
reason=patch hunk contains an invalid line; patch appears to bypass a check or policy
tokens=3777
```

Cycle 2 then visited all three repositories without dispatching another model
call. Each row recorded:

```text
draft attempt already made for this repo during this shift; retry next shift
```

The source checkout stayed clean. The live health check remained GREEN with
Mac LM Studio, the Windows worker, Docker/Colima, and the repo profile all
reachable.

## Proof Boundary

This proves repeated model-call waste is stopped after a terminal draft
attempt. It does not claim that the rejected patch was useful, that a draft PR
was opened, or that a human accepted the morning result.

## Verification

- `bash scripts/check-package.sh` passed 449 tests plus package checks.
- Hosted Ubuntu and macOS package checks passed on PR #239.
- `bin/night-shift health --repo /Users/redbars/code/night-shift` returned `GREEN`.
