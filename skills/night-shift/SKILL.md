---
name: night-shift
description: Run and supervise Night Shift, a bounded local-first overnight repo workbench that uses idle Mac, LM Studio, Ollama, Windows GPU, and optional coding subscriptions to produce evidence-backed repo tasks and a short morning brief. Use for first-time setup, hardware/model detection, "run tonight," "good morning," automatic nightly schedules, snooze/vacation, tuning another computer, or testing the overnight workflow.
---

# Night Shift

Turn idle AI hardware into useful, compounding repo work while the user sleeps.
Watch recently active GitHub repos, work down the Repair-to-Index ladder,
remember completed tasks, reject weak output, and leave a short portfolio brief.

Keep this promise: workers draft; deterministic checks prove; Codex or a human
reviews. Night Shift never edits the target checkout, merges, releases,
deploys, changes credentials or billing, changes repository visibility, or
moves user files. It may push one isolated branch and open a draft PR only
after the owner saves explicit consent and the fresh patch passes approved
sandbox checks again.

## Route The Moment

Check silently:

```bash
command -v night-shift || ls ~/.codex/bin/night-shift 2>/dev/null
cat ~/.codex/night-shift/config.json 2>/dev/null
night-shift schedule --status 2>/dev/null
```

| User signal | Flow |
| --- | --- |
| First use, setup, missing config | First Night |
| Run tonight, goodnight | Bedtime |
| Good morning, complete, what happened | Morning |
| Every night, automatically | Autopilot |
| Vacation, pause, skip | Snooze |
| Stop now | Stop |
| New model, GPU, or computer | Tune-Up |
| Test or rehearse | Rehearsal |

On any invocation, if `schedule --status` shows an unread brief, lead with:
"You have a Night Shift brief from last night - want the summary?" Then handle
the current request.

## ClaudeBrain Raw Intake

When the user asks Night Shift to help ClaudeBrain, use the local-only raw
intake lane:

```bash
night-shift brain-intake --vault /Users/redbars/Documents/claudebrain
```

It triages new text files from `raw/` and writes one source-linked packet to
`raw/scraps/`. The ClaudeBrain nightly agent must verify the original source
before changing `memory.md`, people, projects, notes, or archive state. Night
Shift never moves raw files or writes those authoritative pages. The default
batch is bounded and skips audio, images, protected templates, and
`raw/_legacy/`.

Preserve any repo, mission, mode, or privacy choice the user already supplied.
Never ask for information a read-only check can detect.

## First Night

Auto-detect the repo, GitHub login, local model servers, configured LAN worker,
and safe defaults. Show one plain-English preview and ask only whether to start.
Use `night-shift start --advanced` only when the user asks to customize scope,
privacy, permissions, models, mode, or runtime.

Open briefly:

```text
Hey - welcome to Night Shift.

Your AI hardware sits idle every night. Night Shift puts it to work reading
your recent projects and preparing small, safe, reviewable work. Tomorrow you
get a few useful outcomes with evidence, exact files, and verification commands.

Drafts, not deploys. Setup takes about a minute.
```

### 1. Detect Local Hardware

Run the read-only scan in
[`references/hardware-scan.md`](references/hardware-scan.md). Report what the
machine can do in plain language. Prefer the strongest downloaded coder or
instruct model that answers a chat probe; never select an embedding model.

If a model server is installed but stopped, offer the one-line start command.
If no model exists, continue with a planning brief instead of treating setup
as failed.

### 2. Add Another Computer

If the user has a Windows or LAN machine, verify its model endpoint. Keep repo
context on the private network unless the user explicitly chooses cloud.
Continue Mac-only if the other machine is unavailable.

### 3. Detect Optional Tools

Detect Claude, Codex, and GitHub CLI. Explain only what matters:

- Mac local AI handles private triage and grounded scans.
- The LAN worker handles longer code and test drafts.
- GitHub adds live issue, PR, and failed-workflow context.
- Cloud reasoning is optional and requires explicit permission.

Default to this Mac. Reuse a previously approved private LAN worker when it is
healthy. Ask about LAN or cloud routing only in advanced setup or when the user
explicitly requests it.

### 4. Choose Safe Defaults

Detect the current repo and GitHub login. Default to recently active GitHub
repos when authenticated, ranked chores, local draft plans, Normal mode, and
an eight-hour stop. Keep context on the Mac unless a configured LAN worker is
already healthy. Do not ask about these defaults in the normal flow.

A good mission names an outcome and proof:

```text
Find the highest-value evidence-backed missing test or small bug related to
recent changes. Name exact files, quote repo evidence, and give exact
verification commands.
```

Avoid broad missions such as "find anything" or "improve the app."

### 5. Preview And Launch

Assemble the saved setup:

```bash
night-shift start --repo <repo> \
  --scope <current|github-recent> \
  --mode <quiet|night-shift|afterburner> \
  --wake-goal <brief|chores|draft-prs> \
  --guidance <scan|goal|issues> \
  [--goal "<specific mission>"] \
  --permission <brief|draft-local|draft-prs> \
  --privacy <mac-only|mac-and-lan|cloud-ok> \
  --stop-after <2h|6h|8h|10h|morning> \
  [--execute-drafts] \
  [--run-e2e] \
  --local-url <url> --local-model <model> \
  [--windows-url <url> --windows-model <model>] \
  --yes
```

If the user skips, save with `--setup-only` and stop without nagging. Never
overwrite existing setup unless the user asks to reset it.

First Night ends with a run, followed by one optional Autopilot offer.

## Bedtime

Do not repeat onboarding. Check the schedule. If already armed, say when it
will run. Otherwise recap one line:

```text
Same as last night? <repo> - Normal - draft-local - 8 hours - Mac + Windows
```

On yes, run `night-shift start --yes`. Apply only requested overrides. Before
Normal or Afterburner, follow the startup gate in
[`references/operations.md`](references/operations.md).

## Morning

```bash
night-shift stop --latest   # only when still active
night-shift report --latest
```

Lead with the best one to three choices, not logs. For each choice state:

- the claim;
- exact repo evidence;
- files involved;
- verification command;
- whether it is KEEP, MAYBE, or REJECT;
- the proof artifact path.

Keep worker drafts separate from verified truth. Treat hardware, audio,
telemetry, and manual QA as unknown unless actually checked.

Ask for feedback after review:

```bash
night-shift feedback --latest --item 1 --useful
night-shift feedback --latest --item 1 --not-useful --note "too generic"
```

Feedback stays local and changes future selection for that repo before model
calls. Useful families rise; repeated not-useful families are skipped in Normal
mode. Feedback never bypasses evidence requirements.

For a surviving KEEP/MAYBE item, prepare the bounded coding-agent handoff:

```bash
night-shift handoff --latest --item 1
```

This writes a redacted local review pack and sends nothing. Run it with
`--run` only when cloud reasoning was approved during setup, or after the user
explicitly asks for the one-time `--allow-cloud` path. The coding agent must
run read-only and return a validated verdict before implementation begins. Use
`--agent claude` when the user wants their Claude subscription to do the
independent read; the default Codex path remains unchanged.

End with one choice: verify and implement the best item, rerun with a narrower
mission, or stop. Do not turn the brief into homework.

## Quality Contract

Every worker finding must include an exact repo-relative path, supplied
evidence, why it matters now, a verification command, and an expected result.
Never invent paths, line numbers, issues, failures, or command output.

Night Shift must:

1. Rank recently active repositories from live pushes, PRs, issues, failed
   workflows, and the user's mission.
2. Give workers numbered excerpts and relevant diffs, not filenames alone.
3. Work down Repair, Finish, Strengthen, Understand, and Index tasks in order.
4. Require an exact copied source line; treat model findings as candidates, not proof.
5. Retry one schema-valid but ungrounded answer with the exact missing fields.
6. Fingerprint every task and skip it until the repository or live signal changes.
   Safe health checks may use a daily or weekly fingerprint so a quiet repo
   still gets a fresh bounded review instead of going silent forever.
7. Promote a draft only after isolated edits and deterministic checks pass.
8. Pin failed CI source, commands, validation, and draft worktrees to its exact commit SHA.
9. Rank verified usefulness above token volume.
10. Use local useful/not-useful feedback to avoid repeating bad suggestions.

## End-To-End Checks

Night Shift notices Playwright, Cypress, and repo E2E folders during the scan.
That creates an E2E review task with the exact files and detected scripts; it
does not invent a browser command or run one automatically.

To approve and run one existing E2E script:

```bash
night-shift trust-repo --repo /path/to/project --include-e2e
night-shift autopilot --repo /path/to/project --run-e2e --once
```

The command must already be in the repo's approved profile. It runs once in the
rootless, no-network sandbox, saves `e2e-proof.json`, and reports PASS, FAIL, or
SKIPPED in the morning brief. Night Shift never starts a server, grants network
access, changes the repo checkout, or treats a skipped check as proof.

Read [`references/worker-prompts.md`](references/worker-prompts.md) when
changing or manually dispatching worker prompts.

## Autopilot And Snooze

Ask for a bedtime, then show exactly what was armed:

```bash
night-shift schedule --nightly 23:30
night-shift schedule --status
```

Explain once: it pauses after three unread briefs, drops to quiet on battery,
and stops with `schedule --off`. Use `night-shift snooze --days 7`,
`--until YYYY-MM-DD`, or `--off` for vacations.

Offer `deliver --latest --github-issue` only with explicit consent. It updates
one digest issue and never writes code.

## Rehearsal, Tune-Up, And Stop

- Rehearsal: follow the two-lane no-edit test in
  [`references/operations.md`](references/operations.md). Call it GREEN only
  when both outputs obey the evidence schema.
- Tune-Up: verify only the changed model or machine, then persist with
  `start --yes --setup-only`. Use `--reset` only on request.
- Stop: run `night-shift stop --latest`, then report any partial artifacts.

## Safety

- No direct push to a user's branches. After explicit consent and passing checks,
  it may push one isolated branch to open a draft PR; it never merges, releases,
  deploys, publishes, tags, notarizes, or changes a cask.
- No credentials, billing, visibility changes, destructive cleanup, or user
  file reorganization.
- No private user data, raw transcripts, or secrets in worker prompts.
- Only deduped KEEP items may become implementation candidates, and Codex or a
  human must independently verify them in an isolated worktree.

Read [`SAFETY.md`](SAFETY.md) for the full boundary.

## References

- Hardware and LAN setup: [`references/hardware-scan.md`](references/hardware-scan.md)
- Modes, startup gate, rehearsal, and stop: [`references/operations.md`](references/operations.md)
- Worker schemas and scoring: [`references/worker-prompts.md`](references/worker-prompts.md)
