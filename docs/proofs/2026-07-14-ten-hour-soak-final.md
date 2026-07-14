# Ten-Hour Soak Final Proof

Date: 2026-07-14

## Run

The durable soak harness ran for the full requested 36,000 seconds from the
current Night Shift checkout. It injected repeated controller kills and
required each next controller to reclaim the stale process before continuing.

## Result

```text
TEN_HOUR_SOAK_PROOF: GREEN
duration_seconds=36000
controller_rounds=599
controllers_killed=599
crash_recoveries=599
ledgers=824
maximum_ledger_count=822
minimum_free_bytes=11964284928
active_state_remaining=False
```

The final JSON artifact is:

```text
/Users/redbars/.codex/night-shift/soak-proof-20260714-final-2.json
```

Independent validation confirmed `status=GREEN`, the exact ten-hour
duration, one recovery for every injected kill, no active controller state,
and more than 10 GB of minimum free space. The source checkout stayed clean.

This is real controller/recovery/resource evidence. It does not count as a
useful patch or accepted user outcome.
