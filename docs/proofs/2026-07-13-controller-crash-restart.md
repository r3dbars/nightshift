# Controller crash restart proof

Date: 2026-07-13

Command:

```bash
scripts/prove-controller-restart.sh
```

The integration rehearsal used real operating-system processes and the actual
`night-shift autopilot` command:

1. A disposable controller acquired Night Shift's real directory lock, wrote
   `active-autopilot.json`, launched a separate `sleep 300` process group, and
   recorded it in the old ledger's `processes.tsv`.
2. The controller received `SIGKILL`, which prevented normal `finally` cleanup.
   Its lock, state file, ledger, and live worker were all left behind.
3. A new `night-shift autopilot --once` invocation reclaimed the dead-PID lock.
4. Recovery accepted only the direct, non-symlinked `night-shift-*` ledger under
   the configured overnight root.
5. Recovery signaled the recorded worker group, wrote `STOP` and
   `crash-recovery.json`, changed the old morning status to YELLOW, and removed
   the stale active state.
6. The proof confirmed the worker PID was gone, the new controller completed a
   cycle, and its lock and active state were also cleaned up.

Focused tests reject live controller PIDs, state-file symlinks, ledger
symlinks, paths outside the configured ledger root, and worker rows outside a
recent 12-hour controller session. The time bound prevents an old ledger from
signaling an unrelated process after PID reuse. This proves one real
crash-and-restart sequence. It does not prove concurrent scheduler recovery or
a long soak with repeated crashes.
