# Live Touch Audit

Snapshot: 2026-07-15T11:49:03Z

This is a factual audit of the active Mac run, not a claim that Night Shift
completed useful code work.

## What The Run Selected

The parent portfolio ledger is:

```text
/Users/redbars/.codex/maestro/overnight/night-shift-20260715T110755Z-autopilot
```

It selected three repositories from live GitHub signals, in this order:

1. `r3dbars/BetterFeedback`: score 1210, with failed workflows and active PR
   work.
2. `r3dbars/transcripted-webapp`: score 359, with weak recent activity.
3. `r3dbars/transcripted`: score 175, with one active PR and no failed
   workflow signal at the scan time.

The launch configuration is Mac-only, local-first, draft-local, and bounded to
10 hours. Windows is disabled for this run with `--no-windows`.

## What It Read

Night Shift prepared disposable repository checkouts and read a bounded recent
surface from each one:

| Repository | Branch and revision | Recent files listed | E2E inventory |
| --- | --- | ---: | --- |
| BetterFeedback | `master` at `727f6944` | 80 | Playwright, 1 config, 5 detected commands |
| transcripted-webapp | `main` at `308c5360` | 62 | None detected |
| transcripted | `main` at `7557e94a` | 80 | None detected |

The recent-file list is a bounded scan surface, not an operating-system read
trace. The durable scan artifacts are `repo-scan.json` and `repo-scan.md` in
each child ledger.

## What It Wrote

The run wrote Night Shift state and evidence under
`~/.codex/maestro/overnight/`, including portfolio snapshots, child ledgers,
repo scans, queue files, worker artifacts, E2E proof files, and morning briefs.

The three inspected working checkouts were clean when audited. No canonical
source checkout was changed. No patch, branch push, draft PR, merge, release,
deployment, credential change, billing change, or user-file cleanup was
performed by this run.

## What It Executed

- Local model work ran for bounded health-audit tasks in the BetterFeedback
  child. Its harvested artifacts were rejected because they did not meet the
  proof bar.
- Windows model work ran zero times because the parent was launched Mac-only.
- E2E execution ran zero times. BetterFeedback exposed Playwright commands,
  but no command was approved in `.night-shift.json`; Night Shift recorded
  `SKIPPED` rather than inventing permission or treating discovery as proof.
- The current model circuit is open after repeated rejected revisions. Fresh
  recurring audit tasks can still be inspected, but stale coding work is held.

The strongest current child evidence is:

```text
/Users/redbars/.codex/maestro/overnight/night-shift-20260715T114306Z-afterburner/
```

Its artifacts contain E2E, dependency, and workflow health reviews, but no
surviving `KEEP` or `MAYBE` item and no patch proof.

## What This Means

Night Shift is currently a read, rank, test, and report system. It is not
silently editing repos. Useful code changes require all of these steps:

1. A grounded candidate names an exact file and behavior.
2. An isolated disposable worktree receives the patch.
3. Deterministic checks and semantic evidence pass.
4. Explicit draft-PR consent exists before any GitHub draft is opened.
5. A human or Codex reviews the result before merge or release.

The current run is healthy and honest, but it is not yet producing a useful
patch because the candidates have not cleared those gates.

## Future Touch Audit Contract

Every parent and child ledger should make these fields easy to answer in the
morning brief:

| Field | Allowed meaning |
| --- | --- |
| Repositories inspected | Exact owner/repo and pinned revision |
| Files read | Bounded path list plus count; never imply a full read trace |
| Files changed | Exact paths, or `none` |
| Commands run | Verification and E2E commands with exit status |
| AI calls | Lane, count, approximate tokens, and whether output survived |
| GitHub activity | Read signals, draft PRs, and writes separated |
| Network activity | Endpoint class and whether repo content left the machine |
| Proof outcome | `KEEP`, `MAYBE`, `REJECT`, `SKIPPED`, `BLOCKED`, or `none` |
| Stop reason | Deadline, circuit, weak evidence, missing approval, or clean stop |

The rule for future reports is simple: if a row cannot point to an artifact,
it stays `UNKNOWN`; it never becomes a positive claim from inference.

