# Night Shift

![Night Shift hero image: local AI workers running overnight and producing a morning brief](assets/night-shift-hero.png)

[![license: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
[![local-first](https://img.shields.io/badge/local--first-by_default-2ea44f)](SAFETY.md)
[![drafts-not-deploys](https://img.shields.io/badge/drafts-not_deploys-6f42c1)](#what-it-will-never-do)
[![morning-brief](https://img.shields.io/badge/output-morning_brief-0969da)](#what-you-wake-up-to)

**Put your idle AI hardware to work while you sleep.**

Here's the problem Night Shift solves: you already own AI hardware — a
MacBook with unified memory, a gaming GPU, a spare desktop — and every night
it sits idle. Those are free tokens. The hardware is paid for; the
electricity costs cents. Night Shift collects them: overnight, your machines
read your repo, find small safe work, and draft. You wake up to a short
ranked brief with the few things worth looking at first.

It never pushes, merges, releases, or touches credentials. Drafts, not
deploys. Free and open source under the [MIT License](LICENSE).

## Execution Safety

The normal overnight mode is analysis and planning. It never runs a repository's
`package.json`, Makefile, or shell script just because it discovered one.

Optional sandboxed verification is deliberately a separate owner action. A repo
must contain a reviewed [`.night-shift.json.example`](.night-shift.json.example)
profile with an `owned` trust class, a pinned pre-installed runner image, explicit
argv command arrays, allowed paths, protected verifier files, and resource limits. Night Shift also requires Docker
in rootless mode or Podman's rootless local engine and uses a read-only, no-network container. Without every one
of those checks, it stays in planning mode.

## What You Wake Up To

```text
Portfolio brief — status: GREEN

BetterFeedback
  PROVEN_REPAIR: focused route regression test
  Verify: npm test -- route.test.ts
  Patch: ~/.codex/night-shift/.../route-regression.patch

Transcripted
  CANDIDATE: recent import path needs deterministic proof
  Evidence: Sources/Import.swift:84 | exact source line

Night Shift
  INDEXED: CLI tests mapped to their command handlers

Repositories visited: 3 · New unique tasks: 18 · Repeated tasks skipped: 42
Nothing pushed or merged.
```

Model findings are candidates, never proof. A failing-before/passing-after fix
becomes `PROVEN_REPAIR`; a bounded patch whose checks pass both before and after
is a `VERIFIED_DRAFT`. Repeated tasks are remembered across nights and skipped
until the code or GitHub signal changes.

## Quick Start

```bash
git clone https://github.com/r3dbars/nightshift.git
cd nightshift
./install.sh
night-shift start        # friendly guided setup, then the overnight run
```

Normal setup detects the current project, GitHub, local AI, and a configured
LAN worker, then asks one question: start the safe eight-hour plan? Use
`night-shift start --advanced` only when you want to customize the defaults.

Next morning:

```bash
night-shift report --latest
```

At any point, get the small operational readout instead of hunting through
ledgers:

```bash
night-shift health
```

It shows whether the controller is live, whether both AI lanes answer, whether
the selected repo is analysis-only or sandbox-ready, the latest outcome totals,
and how much local ledger storage Night Shift is using.

When you are ready to enable sandboxed verification, check the provider and
build the reviewed local runner with `night-shift sandbox --build-runner`. It
prints the exact immutable image ID to put in the repo profile.

Every selected task also has a durable lifecycle: `DISCOVERED`, `REPRODUCED`,
`DIAGNOSED`, `PATCHED`, `VERIFIED`, then human-only `REVIEWED` and `PROMOTED`.
An overnight run cannot skip from a hunch to a patch.

Old run artifacts stay until you review them. Preview safe reclamation with
`night-shift clean`; only `night-shift clean --apply` removes completed,
reviewed ledgers older than 21 days.

**Works with:** LM Studio, Ollama (auto-detected), or any OpenAI-compatible
local model server · a second GPU box on your LAN as a heavy draft lane ·
optionally the Claude CLI for one or two hard questions a night and the
GitHub CLI for open-PR context.

Night Shift starts generic scans on your Mac's local model. It only routes a
task to the second machine when a pinned failed CI run or active PR signal gives
that heavier lane a concrete problem to solve.

If a model keeps producing unsupported findings for one unchanged repo revision,
Night Shift opens a small rejection circuit breaker and switches back to the
factual brief rather than burning the rest of the night on retries.

**No local models yet?** `night-shift start` still works: it makes a read-only
planning brief and tells you exactly what to set up.

## Make It Automatic

You shouldn't have to remember Night Shift exists. Arm it once and your
hardware clocks in every night by itself:

```bash
night-shift schedule --nightly 23:30   # runs every night with your saved setup
night-shift schedule --status          # when it runs, what happened, how to stop
night-shift snooze --days 7            # vacation switch
```

The standing shift looks after itself: it **pauses when three morning briefs
pile up unread** (no zombie automation making reports nobody reads — reading
one resumes it), drops to quiet mode on battery, and turns off with one
command. Optionally, `night-shift deliver --latest --github-issue` keeps a
single digest issue in your repo updated with each morning's brief — the only
thing Night Shift ever writes to a repo, and never code. The full design:
[docs/autopilot.md](docs/autopilot.md).

## How It Works

```text
+--------------+     +----------------------+     +---------------+
| Your repo    | --> | Night Shift          | --> | Morning brief |
| Your compute | --> | local / GPU / cloud  | --> | KEEP / MAYBE  |
+--------------+     +----------------------+     +---------------+
```

1. **Scan** live signals: recent diffs, tests, TODOs, issues, PRs, and failed workflows.
2. **Rank** recently active GitHub repos and start with repair or unfinished work.
3. **Work down the ladder:** Repair, Finish, Strengthen, Understand, then Index.
4. **Ground** every task with numbered source, relevant diffs, and real repo commands.
   Failed CI work pins the exact GitHub `headSha`, including its files and package scripts.
5. **Remember** task fingerprints across nights so unchanged work never repeats.
6. **Draft safely** in disposable worktrees when that option is enabled.
7. **Prove** drafts with tests, diff limits, and forbidden-file checks.
8. **Stay on duty** until morning, rescanning GitHub only after new work is exhausted.

Teach it what matters after you review a choice:

```bash
night-shift feedback --latest --item 1 --useful
night-shift feedback --latest --item 2 --not-useful --note "too generic"
```

Feedback stays on your machine and shapes later prompts and rankings for that repo.

You choose how much it may prepare:

| Autonomy | What you get |
| --- | --- |
| `brief` (default) | read-only repo scan, ranked work queue, morning brief |
| `draft-local` | + exact patch plans, issue candidates, and test ideas |
| `draft-prs` | + local patch candidates after a reviewed repo profile and sandbox are installed; still no push or merge |

And how hard it runs:

| Mode | Use it for | Rough shape |
| --- | --- | --- |
| `quiet` | battery, small repos, short evenings | one repo, small unique batches, low heat |
| `night-shift` | the normal overnight run | up to three active repos, finish-first work |
| `afterburner` | maximizing idle hardware | deeper unique indexing and draft work across more repos |

## What It Will Never Do

- Push commits or merge PRs from an overnight run.
- Release, deploy, publish, tag, or notarize.
- Touch credentials, billing, or repository visibility.
- Move or delete your files.
- Pretend an unverified draft is the truth.

Night Shift may prepare an uncommitted patch only when `draft-prs` and
`--execute-drafts` are both enabled. It uses an isolated worktree, limits the
files and diff size, and preserves test output. A human or Codex still reviews,
commits, pushes, and opens the PR. The full boundary lives in
[SAFETY.md](SAFETY.md).

## Learn More

- **[Autopilot design](docs/autopilot.md)** — how the standing nightly run
  stays trustworthy: attention-aware pausing, battery awareness, snooze, and
  opt-in morning delivery.
- **[User guide](docs/guide.md)** — the setup wizard walkthrough, every file a
  run produces, advanced recipes, and full mode details.
- **[20 use cases](docs/use-cases.md)** — from "solo Mac with LM Studio" to
  "messy PR queue" to full tokenmaxx nights.
- **[Copy-paste examples](skills/night-shift/examples)** — including a fake
  [sample morning brief](skills/night-shift/examples/sample-morning-brief.md).
- **[Safety and privacy](SAFETY.md)** — what each worker lane can see and why
  the boundaries exist.
- **[Troubleshooting](docs/troubleshooting.md)** ·
  **[Contributing](CONTRIBUTING.md)** · **[Changelog](CHANGELOG.md)**

## Mascot

<img src="assets/night-shift-mascot.png" alt="Night Shift mascot: a tiny robot helper with coffee and a clipboard" width="180">

The Night Shift helper: tiny, caffeinated, and only allowed to make drafts
until a human checks the work.

---

MIT © r3dbars · [LICENSE](LICENSE)
