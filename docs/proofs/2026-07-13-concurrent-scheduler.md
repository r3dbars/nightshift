# Concurrent scheduler proof

Date: 2026-07-13

Command:

```bash
scripts/prove-concurrent-scheduler.sh
```

The integration proof exercised the real `night-shift nightly` entry point with
the production active-state and directory-lock paths in a disposable Codex
home:

1. A fresh setup was saved against a clean Git repository.
2. A real process acquired the autopilot lock and wrote active controller state.
3. `night-shift nightly --once` detected that controller, returned GREEN with a
   clear `skipped` result, and wrote `SKIPPED_ACTIVE` to `last-nightly.json`.
4. The proof counted overnight directories before and after the overlap. The
   losing scheduler launch created no empty ledger.
5. The active controller received `SIGKILL` and left its lock and state behind.
6. The next real `night-shift nightly --once` reclaimed the stale lock, wrote
   crash-recovery evidence for the old ledger, created its own unattended run,
   completed one portfolio cycle, and cleaned its lock and active state.
7. `last-nightly.json` no longer reported the earlier skip, proving the later
   launch was attempted rather than silently suppressed.

The CLI also handles the narrower race where two schedulers both pass the first
active-state check: the production autopilot lock chooses one winner, the loser
creates no ledger, and nightly converts that contention into a truthful clean
skip. The lock is now a kernel-backed nonblocking file lock, so process death
releases ownership automatically; an eight-process synchronized fanout proves
one owner and seven clean losers, and a focused test proves migration from the
old stale directory-lock format. This is one real overlap-and-recovery
sequence, not a multi-hour repeated scheduler soak.
