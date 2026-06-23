# Maestro Night Shift

Put idle AI compute to work while you sleep.

Maestro Night Shift is a simple overnight launcher for repo work. Point it at a
project, point it at the compute you have, pick a mode, and wake up to a morning
brief with artifacts, safe draft ideas, token totals, and next actions.

It is not an autonomous release bot. Local and Windows models can think, sort,
review, and draft. Codex still reviews, edits, tests, opens PRs, merges, and
ships.

## Quick Start

```bash
maestro-nightshift doctor --repo /path/to/project
maestro-nightshift plan --repo /path/to/project --mode night-shift
maestro-nightshift run --repo /path/to/project --mode night-shift
maestro-nightshift report --latest
```

Stop a run:

```bash
maestro-nightshift stop --latest
```

## The Mental Model

There are two things to point at:

1. Compute: Mac local model, Windows GPU worker, Claude CLI, Codex.
2. Project: the repo you want improved.

Then choose one mode:

- `quiet`: low heat, low noise, small useful scans.
- `night-shift`: normal overnight run.
- `afterburner`: tokenmaxx mode. Use the hardware hard until morning.

The run writes everything under:

```text
~/.codex/maestro/overnight/night-shift-<timestamp>/
```

Useful files:

- `startup-gate.md`: what compute was reachable.
- `board.md`: the work queue.
- `context-pack.txt`: repo context used for prompts.
- `artifacts/`: local and Windows worker outputs.
- `proofs.tsv`: proof paths from `maestro-delegate`.
- `token-report.txt`: estimated tokens by lane.
- `morning.md`: the morning brief.

## Setup

Required:

- Git repo on this machine.
- `~/.codex/bin/maestro-delegate`
- `~/.codex/bin/maestro-token-report`

Recommended:

- LM Studio running at `http://localhost:1234`.
- A loaded chat model, usually `phi-4-mini-instruct`.
- Windows worker on the LAN at `http://192.168.7.201:11434/v1`.
- Claude CLI installed if you want the reasoning lane.
- GitHub CLI signed in if you want PR state included in the context pack.

Check it:

```bash
maestro-nightshift doctor --repo /path/to/project
```

Point it at different compute:

```bash
maestro-nightshift doctor --repo /path/to/project \
  --local-model phi-4-mini-instruct \
  --windows-url http://192.168.7.201:11434/v1 \
  --windows-model qwen3-coder:30b
```

If something is missing, the doctor output should tell you exactly what to start.

## Modes

### Quiet

Use this for a laptop on battery, a small repo, or a short evening pass.

Defaults:

- Mac local loops: 6
- Windows loops: 2
- Parallel local: 1
- Parallel Windows: 1
- Token target: 50k estimated local/Windows tokens

### Night Shift

Use this as the normal overnight setting.

Defaults:

- Mac local loops: 40
- Windows loops: 20
- Parallel local: 3
- Parallel Windows: 2
- Token target: 500k estimated local/Windows tokens

### Afterburner

Use this when you want to maximize idle hardware.

Defaults:

- Mac local loops: 120
- Windows loops: 80
- Parallel local: 4
- Parallel Windows: 2
- Token target: 2M estimated local/Windows tokens

## What It Will Do

Good overnight work:

- Find missing tests.
- Map risky files.
- Cluster TODOs and bug smells.
- Review stale PRs.
- Create release-readiness briefs.
- Compare user stories to tests and analytics.
- Mine PostHog/Sentry gaps.
- Draft small patch plans.
- Produce morning-ready issues.

What it will not do by itself:

- Merge PRs.
- Cut releases.
- Publish, tag, notarize, deploy, update appcasts, or update casks.
- Touch credentials or billing.
- Move or delete user files.
- Claim hardware, audio, Bluetooth, camera, or manual QA proof.

## Twenty Common Scenarios

1. **Mac-only solo dev**
   - Compute: LM Studio only.
   - Mode: `quiet` or `night-shift`.
   - Best work: TODO mining, test gaps, docs drift, small patch plans.

2. **Mac plus Windows GPU worker**
   - Compute: LM Studio + Windows worker.
   - Mode: `night-shift` or `afterburner`.
   - Best work: Mac local does triage, Windows drafts deeper review and patch plans.

3. **Windows-only worker available**
   - Compute: Windows endpoint only.
   - Mode: `quiet`.
   - Best work: draft implementation plans, review notes, test ideas.

4. **Codex plan user**
   - Compute: Codex for execution and verification.
   - Mode: `night-shift`.
   - Best work: local/Windows generate artifacts, Codex turns the best few into PRs later.

5. **Claude Code plan user**
   - Compute: Claude CLI for hard reasoning.
   - Mode: `night-shift`.
   - Best work: one or two architecture or risk calls, not every small task.

6. **Codex plus Claude user**
   - Compute: Codex as cockpit, Claude as second-opinion lane.
   - Mode: `night-shift`.
   - Best work: risky refactor reviews, release risk review, hard bug hypotheses.

7. **No local models installed yet**
   - Compute: none local.
   - Mode: `doctor`.
   - Best work: setup checklist and project plan. Do not call it a real run yet.

8. **Private repo with sensitive data**
   - Compute: local only.
   - Mode: `quiet`.
   - Best work: keep prompts coarse and avoid private text, secrets, paths, or content.

9. **Open-source repo**
   - Compute: any lane.
   - Mode: `night-shift`.
   - Best work: issue triage, docs, tests, stale PR analysis.

10. **Messy PR queue**
    - Compute: local + Windows.
    - Mode: `night-shift`.
    - Best work: classify PRs as merge, close, superseded, cherry-pick, or hold.

11. **Release prep**
    - Compute: Codex verifies, local/Windows summarize.
    - Mode: `quiet`.
    - Best work: release-readiness brief, not publishing.

12. **Test coverage push**
    - Compute: local for gaps, Windows for draft tests.
    - Mode: `night-shift`.
    - Best work: find missing tests and propose exact fixtures.

13. **PostHog analytics audit**
    - Compute: local for taxonomy scan, Windows for dashboard questions.
    - Mode: `night-shift`.
    - Best work: events missing, properties missing, dashboards to add.

14. **Sentry reliability audit**
    - Compute: local for issue clustering.
    - Mode: `quiet`.
    - Best work: issue families, suspected files, repro ideas.

15. **Docs maintenance**
    - Compute: local.
    - Mode: `quiet`.
    - Best work: stale docs, missing setup steps, release doc drift.

16. **Refactor exploration**
    - Compute: local + Claude for hard calls.
    - Mode: `night-shift`.
    - Best work: rank candidates. Do not rewrite overnight.

17. **Issue triage backlog**
    - Compute: local + Windows.
    - Mode: `night-shift`.
    - Best work: classify, dedupe, and draft clean issue text.

18. **Multi-repo founder mode**
    - Compute: local + Windows.
    - Mode: one repo per run.
    - Best work: separate ledgers so morning review stays sane.

19. **Low-heat laptop overnight**
    - Compute: Mac local only, one worker.
    - Mode: `quiet`.
    - Best work: read-only scans and a short morning brief.

20. **Full tokenmaxx**
    - Compute: Mac local + Windows worker.
    - Mode: `afterburner`.
    - Best work: huge artifact generation, maps, audits, rankings, and morning triage.

## Morning Workflow

In the morning:

```bash
maestro-nightshift report --latest
```

Then review:

1. `morning.md`
2. `harvest.md`
3. `token-report.txt`
4. high-signal files in `artifacts/`

The right next action is usually one of these:

- Ask Codex to turn one `KEEP` artifact into a PR.
- Ask Codex to launch a focused review/merge thread.
- Rerun in `quiet` mode with a narrower target.
- Stop because the project is ready for manual QA or release.

## Naming

Product name: `Maestro Night Shift`

Short command: `maestro-nightshift`

Friendly phrases:

- "Start Night Shift on this repo."
- "Run Afterburner tonight."
- "Morning brief."
- "Stop Night Shift."
