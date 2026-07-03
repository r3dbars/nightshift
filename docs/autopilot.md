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

**Compute is free at night. Your attention is not.**

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

### 2. The attention-aware pause — automation that notices it's ignored

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

### 3. Machine respect — guards for unattended hardware

An unattended run must be a considerate house guest:

- **On battery, it drops to `quiet` mode** — a laptop unplugged at midnight
  should not spin fans for six hours.
- **Every run honors the stop timer** (`--stop-after`, default 8h in
  unattended runs) and the existing thermal and failure limits.
- **Snooze is a first-class state**, not a hack:
  `night-shift snooze --days 7` for a vacation, `--until 2026-07-14` for a
  date, `--off` to resume early. A snoozed night logs itself as skipped so
  status never lies about what happened.

### 4. Morning delivery — results where you already look

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
- **It is the only repo write Night Shift is allowed, ever.** Never code,
  never a branch, never a PR. The safety envelope (`run` never pushes)
  survives automation intact.
- **Opt-in only.** Delivery happens when you pass the flag or set
  `"deliver": "github-issue"` in config through consented setup. Silence is
  local-only.

The AI-assistant skill adds a second delivery surface for free: whenever the
Night Shift skill is invoked for anything, it checks for unreviewed briefs
and leads with one line — "you have a brief from last night" — before doing
whatever was asked. Your assistant becomes the morning courier.

### 5. The safety envelope does not bend at 3 a.m.

Nothing about automation loosens the rules: no pushes, no merges, no
releases, no credential or visibility changes, workers draft and never
decide, and draft PRs only ever come from a reviewed morning decision. An
unattended night has *less* authority than an attended one (battery
downgrade, attention pause), never more.

## What This Adds Up To

| Old obligation | New reality |
| --- | --- |
| Remember to run it every night | `schedule --nightly` once |
| Remember to check results | Digest issue + assistant surfacing |
| Remember to stop it for vacation | `snooze --days 7` |
| Worry it's running amok unattended | Attention pause + `schedule --status` |
| Worry it will touch the repo | One opt-in digest issue, never code |

The end state: your hardware clocks in every night, your repo gets a little
smarter every morning, and the only thing you ever *have* to do is read the
brief when you feel like it — because when you stop reading, it stops
writing.

## Roadmap: Where This Design Goes Next

These are specified but not yet built, in priority order:

1. **Taste memory.** The morning review records which brief items you acted
   on versus ignored (`~/.codex/night-shift/memory/<repo>/verdicts.jsonl`).
   The queue builder downweights categories you never touch and upweights
   what you act on. Run N+1 should always be more *yours* than run N.
2. **Cross-night dedupe.** Fingerprints of every suggestion ever surfaced
   (`seen.jsonl`) so a rejected idea does not reappear Tuesday, Thursday, and
   Sunday. Within-run dedupe already exists; memory should span nights.
3. **Continuity briefs.** The morning brief opens with "since yesterday:
   item 1 was fixed (PR #23 merged), items 2–3 still open, here's what's
   new" — a narrative thread across nights instead of disconnected reports.
4. **Nothing-new detection.** If the repo HEAD and signals are unchanged
   since the last run, say "nothing new tonight" in one line instead of
   re-running the full queue — respect for both electricity and attention.
5. **More delivery surfaces.** A morning desktop notification when a brief
   is ready; an optional shell-greeting one-liner. Same rules as the digest
   issue: one artifact, updated in place, opt-in.

Contributions to any of these are welcome — see
[CONTRIBUTING.md](../CONTRIBUTING.md).
