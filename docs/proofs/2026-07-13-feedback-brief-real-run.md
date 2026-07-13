# Feedback Brief Real-Run Proof

This proof checks the shipped feedback UX in a real two-lane Night Shift run,
not only in unit tests.

## Run

- Repository: `/Users/redbars/code/night-shift`
- Source revision: `9699d07`
- Mode: `afterburner`
- Permission: `brief` (analysis-only)
- Local calls: 1, about 3,421 estimated tokens
- Windows calls: 1, about 4,728 estimated tokens
- Ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260713T222946Z-afterburner`
- Result: `YELLOW`, with two `MAYBE` candidates and no patch or PR

## What was proven

The real `morning.md` included:

- ranked choices with evidence, files, verification commands, and proof paths;
- an exact copy-ready useful command;
- an exact copy-ready not-useful command with a concrete note example;
- a repo-scoped learning snapshot showing one prior useful signal;
- explicit safety language that no merge, deploy, credential, or user-file action
  happened.

The source checkout stayed clean. The two model suggestions remain unproven
until deterministic execution and human usefulness review; this run does not
raise the useful-output or learning-loop scores by itself.
