# Autopilot: The Design Of The Standing Night Shift

Night Shift exists because of a simple observation: **developers own AI
hardware that sits idle every night, and idle hardware is free tokens.** The
machine is paid for. Electricity is cents. A 24 GB gaming GPU running a
30B-class coder model overnight produces on the order of a million tokens of
analysis — every night, for roughly the price of leaving a light on. Multiply
by a MacBook with unified memory doing triage beside it, and most developers
are sitting on tens of millions of free monthly tokens they never collect.

Manually collecting them has a fatal flaw: you have to remember. A tool you
must summon every evening gets used three times and forgotten. So the real
product is not "a command that runs overnight" — it is **a standing
arrangement your hardware keeps on your behalf**, designed so you can trust
it while unconscious and ignore it without consequences.

This document explains how that arrangement works, and the design principles
behind every mechanism. If you just want the commands, see the
[user guide](guide.md#run-it-every-night).

## The One Principle Everything Follows From

**Compute is abundant at night. Repetition and morning attention are not free.**

Every design decision below optimizes for morning attention, not overnight
throughput. A run that produces 60 artifacts is worthless if the morning
brief takes 20 minutes to read. Automation that keeps producing briefs nobody
opens is worse than worthless — it trains you to ignore the product. So the
loop is:

```text
run (cheap, all night) → deliver (where you already look)
      ↑                                       ↓
   adapt (next night)  ←  observe (did the human actually engage?)
```

The worker stays on duty until morning. It uses idle time continuously while
new, grounded work remains, but never repeats an unchanged task merely to keep
a GPU busy.

## The Mechanisms

### 1. The standing shift — set once, never summon again

```bash
night-shift schedule --nightly 23:30
```

This installs a launchd agent (macOS) or cron entry (Linux) that fires
`night-shift nightly` at the chosen time. Two deliberate choices:

- **The schedule stores no settings — only a time.** `nightly` reads the
  saved config at fire time, so changing your mode, repo, or autonomy today
  changes what runs tonight. The schedule is a timer, not a snapshot; there
  is never a stale copy of your preferences hiding in a plist.
- **The scheduled command is inspectable.** `schedule --status` prints the
  exact command line, when it last ran, what happened, and how to stop it.
  Automation you cannot inspect is automation you eventually fear.

### 2. Portfolio discovery and the usefulness ladder

Each cycle ranks recently active GitHub repositories from pushes, failed
workflows, pull requests, review state, and issues. Work proceeds in order:

```text
Repair -> Finish -> Strengthen -> Understand -> Index
```

When immediate repair work runs out, local compute builds reusable test maps,
source maps, and docs checks. Every task is fingerprinted with its repository
revision and live signal. Completed fingerprints stay skipped until something
actually changes.

Normal mode defaults to a 14-day activity window and at most three
repositories. `--active-days` and `--max-repos` change those limits. Dedicated
checkouts live under `~/.codex/night-shift/repos/`. Configurations created
before portfolio mode remain single-repo until the user explicitly widens the
scope in setup.

### 3. The attention-aware pause — automation that notices it's ignored

The classic failure of scheduled automation is the zombie: it keeps running,
output piles up, the human tunes it out, and six months later it's a folder
of 180 unread reports and a bad taste. Night Shift refuses to become that:

**After 3 unread morning briefs, the nightly run pauses itself.** It writes a
one-line explanation instead of a new brief, and `schedule --status` says
exactly why. Reading any brief (`night-shift report`) marks it reviewed and
re-arms the next night. No settings, no nagging — the system simply matches
its output rate to your demonstrated attention.

This is the single most important mechanism in the design. It converts "the
user must remember to run it" into "the user must merely glance at results
sometimes," which is the correct direction for the obligation to flow.

### 4. Machine respect — guards for unattended hardware

An unattended run must be a considerate house guest:

- **On battery, it drops to `quiet` mode** — a laptop unplugged at midnight
  should not spin fans for six hours.
- **Every run honors the stop timer** (`--stop-after`, default 8h in
  unattended runs) and the existing thermal and failure limits.
- **Snooze is a first-class state**, not a hack:
  `night-shift snooze --days 7` for a vacation, `--until 2026-07-14` for a
  date, `--off` to resume early. A snoozed night logs itself as skipped so
  status never lies about what happened.

### 5. Isolated, test-gated drafts

With `draft-prs --execute-drafts`, Night Shift may use the Windows Ollama coder
through Aider inside a disposable Git worktree. The original checkout remains
untouched. The controller limits approved files and diff size, blocks secrets,
lock-file changes, and release actions, and reruns an exact detected test
command. Failed drafts remain rejected artifacts. A failing-before and
passing-after change is a `PROVEN_REPAIR`; an otherwise clean bounded patch is
a `VERIFIED_DRAFT`. Both remain local and uncommitted for morning review.
If the isolated check cannot run, the morning brief includes the short redacted
runner cause, such as a missing test executable, so the next setup step is clear.

Night Shift makes at most one draft attempt per repository during a shift. A
verified draft is skipped because the repo already produced useful work. A
rejected or unavailable attempt is also skipped, with a clear retry-next-shift
note, so a temporary failure cannot turn into repeated model calls. The next
shift can try that repository again.

For failed GitHub Actions runs, source, package scripts, evidence validation,
and the disposable worktree all use the run's exact `headSha`. A PR-only file
is never analyzed or edited as though it came from the default branch.

### 6. Morning delivery — results where you already look

A brief on disk requires remembering to look. Optional delivery closes the
gap:

```bash
night-shift deliver --latest --github-issue
```

This keeps **exactly one** open issue per repo — "🌙 Night Shift morning
brief" — updated in place each morning via the `gh` CLI. Design constraints,
all deliberate:

- **One issue, edited in place.** Never a second issue, never a nightly
  flood. The issue is a dashboard, not a feed.
- **It is the default remote write.** Code stays local unless the owner has
  separately authorized test-passed draft PRs.
- **Opt-in only.** Delivery happens when you pass the flag or set
  `"deliver": "github-issue"` in config through consented setup. Silence is
  local-only.

The AI-assistant skill adds a second delivery surface for free: whenever the
Night Shift skill is invoked for anything, it checks for unreviewed briefs
and leads with one line — "you have a brief from last night" — before doing
whatever was asked. Your assistant becomes the morning courier.

### 7. The safety envelope does not bend at 3 a.m.

Nothing about automation loosens the rules: no merges, releases, credential or
visibility changes. Without explicit saved authorization, there are no code
pushes. With it, Night Shift may push one unique isolated branch and open a
draft PR only after the approved sandbox check passes again. Humans still
decide what merges. An unattended night has *less* authority than an attended
one.

## What This Adds Up To

| Old obligation | New reality |
| --- | --- |
| Remember to run it every night | `schedule --nightly` once |
| Remember to check results | Digest issue + assistant surfacing |
| Remember to stop it for vacation | `snooze --days 7` |
| Worry it's running amok unattended | Attention pause + `schedule --status` |
| Worry it will touch my checkout | Disposable worktrees only; original checkout untouched |

The end state: your hardware clocks in every night, your repo gets a little
smarter every morning, and the only thing you ever *have* to do is read the
brief when you feel like it — because when you stop reading, it stops
writing.

## Roadmap: Where This Design Goes Next

Useful next improvements, in priority order:

1. **Taste memory.** The morning review records which brief items you acted
   on versus ignored (`~/.codex/night-shift/memory/<repo>/verdicts.jsonl`).
   The queue builder downweights categories you never touch and upweights
   what you act on. Run N+1 should always be more *yours* than run N.
2. **Continuity briefs.** The morning brief opens with "since yesterday:
   item 1 was fixed (PR #23 merged), items 2–3 still open, here's what's
   new" — a narrative thread across nights instead of disconnected reports.
3. **Outcome learning.** Observe whether proven drafts were committed, opened
   as PRs, or ignored, and tune portfolio/task ranking from those outcomes.
4. **More delivery surfaces.** A morning desktop notification when a brief
   is ready; an optional shell-greeting one-liner. Same rules as the digest
   issue: one artifact, updated in place, opt-in.

Contributions to any of these are welcome — see
[CONTRIBUTING.md](../CONTRIBUTING.md).
