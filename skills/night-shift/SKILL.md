---
name: night-shift
description: Launch and supervise Night Shift, a bounded overnight local-compute workbench that turns idle AI hardware into useful repo work — scans, deduped work queues, and a ranked morning brief. Use when the user asks for Night Shift or first-time Night Shift setup, says goodnight / going to sleep / run overnight / tokenmaxx, wants their idle GPU, Apple Silicon, LM Studio, Ollama, or a Windows worker doing useful things overnight, asks to scan for local models or what their hardware can run, wants it scheduled automatically every night ("autopilot", "every night", "snooze", "vacation"), or returns in the morning with "Complete", "Good morning", "stop the night", or asks what happened overnight.
---

# Night Shift

The problem this exists to solve, in the user's own words: "I own AI hardware
that sits idle every night. Those are free tokens — the hardware is paid for
and electricity is cheap. How do I get it doing helpful things for me while I
sleep?"

Night Shift is the answer: point the idle hardware at a repo before bed, let
it scan, analyze, and draft all night, and wake up to a short ranked brief
with the few things worth looking at first. Once the user says yes to the
standing schedule, they never have to remember it again — the hardware just
clocks in every night.

Core rule, never bend it: local and Windows lanes may draft; Codex or a human
reviews and verifies; `night-shift run` does not edit the target repo; nothing
pushes branches, merges, releases, publishes, tags, notarizes, deploys, changes
repository visibility, changes credentials, or edits billing without the user
explicitly saying so after the morning review.

Zero-config floor: with no local models and no subscriptions at all, Night
Shift still works tonight — it reads the repo and produces a planning brief.
Everything else is unlocked, not required.

## Which Moment Is This?

Check silently — do not narrate these checks, and never announce "setup is
already complete" to a configured user:

```bash
command -v night-shift || ls ~/.codex/bin/night-shift 2>/dev/null
cat ~/.codex/night-shift/config.json 2>/dev/null
night-shift schedule --status 2>/dev/null
```

Route by what you find and what the user said:

| Signal | Moment |
| --- | --- |
| No config file, CLI missing, or the user asks to set up | **First Night** |
| Config exists and the user wants to run tonight | **Bedtime** |
| "Good morning", "Complete", "what happened overnight" | **Morning** |
| "Every night", "automatically", "schedule this", "autopilot" | **Autopilot** |
| "Vacation", "pause it", "skip this week", "stop for a while" | **Snooze** |
| "Stop", "stop the night", "kill it" | **Stop Now** |
| New hardware, "change settings", "use my other computer" | **Tune-Up** |
| "Test Night Shift", "rehearse" | **Rehearsal** — read `references/operations.md` |

Morning surfacing contract: on ANY invocation of this skill, if
`schedule --status` shows unreviewed overnight briefs, lead with one line —
"You have a Night Shift brief from last night — want the summary?" — then
continue with what the user actually asked. Never bury a finished night.

If the user's invocation already contains a repo, a mission, or a mode, keep
it. Setup runs first; their request runs immediately after. Never discard what
they actually asked for, and never re-ask a question their message already
answered.

## Onboarding Contracts (do not regress)

These are product commitments, not suggestions:

1. **Hardware before subscriptions, always.** Idle local AI hardware is the
   entire reason this product exists. Ask about it first, scan for it with
   consent, celebrate what is found. Cloud subscriptions are optional garnish.
2. **Detect, then confirm.** Never ask the user something a read-only command
   can answer. Scan, present findings in plain language, confirm the plan.
3. **One question at a time for decisions that depend on each other.** Each
   question carries a recommended default so the user can just say yes.
   Independent facts (energy level, stop time) may share one prompt.
4. **You are the conversational driver.** The CLI does mechanical work only.
   Consent happens in chat: ask, wait for the answer, then run the command.
   Running setup silently and reporting the result afterward is the
   silent-onboarding failure this section exists to prevent.
5. **Every question has a skip, and skipping never nags.** "Skip for now"
   still saves setup (`night-shift start --repo <repo> --yes --setup-only`)
   so the wizard never fires again uninvited.
6. **Never overwrite an existing config without `--reset`.** A configured user
   who says "start" gets the Bedtime fast path, not the wizard.
7. **First Night ends with the thing running**, not with reading material —
   and with one final offer to make it automatic forever.
8. **Automation must always be inspectable and reversible.** Any standing
   schedule must answer "when does it run, when did it last run, how do I
   stop it" via `night-shift schedule --status`, `snooze`, and
   `schedule --off`. Never arm a schedule without saying exactly what will
   run and when.

If the host supports an option-picker tool (such as `AskUserQuestion`), use it
for every choice below, with the recommended option first. Otherwise ask the
same questions in plain prose, one message at a time. In a headless or
scheduled session, skip all onboarding and run with `--yes` and saved config.

## First Night (one-time guided setup)

### Step 1 — Welcome

Open with a short, warm welcome in roughly this shape. Keep it under ten
lines; the guided questions are the feature, not a wall of text:

```text
Hey — welcome to Night Shift.

Here's the idea: you already own AI hardware, and every night it sits idle.
Those are free tokens — the hardware is paid for, electricity costs cents.
Night Shift collects them: while you sleep, your machines read your repo,
find small safe work, and draft. You wake up to a short ranked brief with
the few things worth looking at first.

It will never push, merge, release, or touch credentials. Drafts, not deploys.

Setup takes about a minute, and at the end you can make it automatic so you
never have to think about it again. First question is the fun one.
```

### Step 2 — The hardware question (always first)

Ask before anything else — before the repo, before goals:

> **What AI hardware do you own that's sitting idle at night?**
> Think: this Mac (Apple Silicon unified memory counts for a lot), a gaming
> PC with a real GPU, a spare desktop on your network.

Options:

1. **Scan this machine (recommended)** — read-only, takes ~10 seconds.
2. **I have other machines too** — scan here, then set up the network worker.
3. **I'll type in my setup myself** — for users who know their endpoints.
4. **No local AI hardware** — totally fine; subscriptions or read-only briefs.

### Step 3 — Scan and celebrate

With consent, run the quick scan. Every command is read-only and local; none
installs anything:

```bash
# What is this machine? (macOS)
sysctl -n machdep.cpu.brand_string
echo "$(( $(sysctl -n hw.memsize) / 1073741824 )) GB unified memory"

# (Linux / WSL)
free -g | awk '/^Mem:/ {print $2 " GB RAM"}'
nvidia-smi --query-gpu=name,memory.total --format=csv,noheader 2>/dev/null

# Who is already serving models?
curl -s --max-time 2 http://localhost:1234/v1/models    # LM Studio
curl -s --max-time 2 http://localhost:11434/api/tags    # Ollama

# Installed but not running?
command -v ollama >/dev/null 2>&1 && ollama list
ls /Applications 2>/dev/null | grep -i "lm studio"
```

Report findings like a friend who knows hardware, not like a diagnostic dump.
Lead with what the machine can do, and make the idle-token point concrete:

```text
Here's what I found:

  This Mac    Apple M3 Max, 64 GB unified memory
              → comfortably runs 30B-class models. Left idle 8 hours a night,
                that's on the order of a million tokens of thinking you
                already paid for — every single night.
  Ollama      running, 3 models: qwen2.5-coder:14b, llama3.2:3b, nomic-embed-text
  LM Studio   installed, server not running

  Best pick tonight: qwen2.5-coder:14b via Ollama — the biggest coder model
  you already have. With 64 GB you could also run qwen3-coder:30b; grabbing
  it is one command if you want it.
```

Honest capability tiers for the plain-language read (quantized models):

| Memory (unified or VRAM) | Comfortable overnight models |
| --- | --- |
| under 8 GB | 1–3B: light triage only |
| 8–16 GB | 3–8B: classification, TODO mining, summaries |
| 16–32 GB | 7–14B: solid repo analysts and review notes |
| 32–64 GB unified / 24 GB VRAM | 14B–32B: real drafting, patch plans (a 3090/4090 lives here) |
| 96 GB+ | 70B-class quantized |

Picking a model: prefer the largest coder or instruct chat model already
downloaded (`qwen*-coder`, `*-instruct`, `llama3*`, `phi-4`, `gemma*`). Never
pick an embedding model. Full probe details, install offers, and
troubleshooting: `references/hardware-scan.md`.

If a server is installed but not running, offer the one-line fix now
("open LM Studio and start the server" / "run `ollama serve`") rather than
deferring it to a doctor command later.

If nothing is found, reassure — this is not a failure state:

```text
No local models yet — no problem. Two easy paths if you want one later:
- Ollama: one install, then `ollama pull qwen2.5-coder:14b`
- LM Studio: a friendly app with a built-in model browser

Tonight still works without them: I can scan the repo and make a planning
brief, and we can add hardware any night. Want me to set up Ollama now, or
keep going?
```

### Step 4 — Other machines on the network

If the user mentioned another computer (a Windows gaming PC is the classic),
help them wire it up as the second lane — that GPU is the single biggest pile
of idle tokens most developers own:

- If it is already serving: verify with
  `curl -s --max-time 3 http://<host>:11434/api/tags` and confirm the model.
- If not set up yet: give the short version — on the Windows box, set
  `OLLAMA_HOST=0.0.0.0`, restart Ollama, allow port 11434 on the private
  network — and point to `references/hardware-scan.md` for the exact steps.
- If it cannot be reached right now, do not stall onboarding. Save it as
  "add later", continue with what works tonight, and mention `Tune-Up` can
  wire it in any evening.

A 24 GB gaming GPU runs 30B-class coder models (`qwen3-coder:30b` is the
default) — worth saying out loud; it is why that box joins the night shift.

### Step 5 — Subscriptions (after local, never before)

Now, and only now, detect the cloud lanes — silently, then confirm:

```bash
command -v claude >/dev/null 2>&1 && claude --version 2>/dev/null
command -v codex >/dev/null 2>&1 && codex --version 2>/dev/null
gh auth status 2>&1 | head -3
```

Frame them honestly: local lanes do the bulk thinking; Claude is for at most
one or two hard reasoning questions a night; the GitHub CLI adds open-PR
context to the repo scan; Codex (or this assistant) reviews the results in the
morning. Then ask the one real question:

> **Is repo context allowed to leave this machine tonight?**
> 1. Only this machine — safest and private *(recommended first night)*
> 2. This machine plus my other computer on my network
> 3. Cloud subscriptions are okay for hard questions

The answer maps to `--privacy mac-only | mac-and-lan | cloud-ok`. If steps
2–4 found no second machine and no subscriptions, skip the question and use
`mac-only`.

### Step 6 — Tonight's plan

Detect the repo first: if the conversation is already inside a git checkout,
propose it (`git rev-parse --show-toplevel`) instead of asking cold. Then walk
the remaining choices one at a time, each with a recommendation:

1. **Which project should Night Shift look at?** (confirm the detected repo)
2. **What would make tomorrow morning a win?**
   - A calm morning brief *(recommended first night)* → `--wake-goal brief`
   - A ranked hit list of bugs, tests, docs, chores → `--wake-goal chores`
   - Draft PR candidates, still nothing pushed → `--wake-goal draft-prs`
3. **What should it aim at?** Sharpest safe work (`--guidance scan`,
   recommended) / one mission tonight (`--goal "<sentence>"`) / open issues
   and PRs as the map (`--guidance issues`).
4. **How much is it allowed to prepare?** Read-only brief
   (`--permission brief`, recommended first night) / draft local patch plans
   (`draft-local`) / review-ready draft PR candidates (`draft-prs`). Say the
   ladder out loud: it can climb tomorrow after they see how tonight goes.
5. **How much energy, and when to stop?** (independent facts — one prompt is
   fine) Quiet / Normal *(recommended)* / Afterburner → `--mode`; stop after
   2h / 6h / 8h *(recommended first night)* / when I come back →
   `--stop-after`. If the machine is on battery, recommend Quiet and say why.

### Step 7 — Preview, save, launch

Assemble one command from every answer. The CLI prints the will / will-not
preview itself:

```bash
night-shift start --repo <repo> \
  --mode <quiet|night-shift|afterburner> \
  --wake-goal <brief|chores|draft-prs> \
  --permission <brief|draft-local|draft-prs> \
  --privacy <mac-only|mac-and-lan|cloud-ok> \
  --stop-after <2h|6h|8h|morning> \
  --local-url <detected, e.g. http://localhost:11434/v1> \
  --local-model <detected best model> \
  [--windows-url http://<host>:11434/v1 --windows-model <model>] \
  [--goal "<tonight's mission>"] \
  --yes
```

Ollama serves an OpenAI-compatible API at `/v1`, so
`--local-url http://localhost:11434/v1` wires it in directly; LM Studio is
`http://localhost:1234/v1`.

If the user chose "Skip for now" at any point: save what was gathered with
`night-shift start --repo <repo> --yes --setup-only`, tell them setup is saved
and they can say "start night shift" any evening, and stop. No nagging.

### Step 8 — Make it automatic (the last question)

After the run is launched, make the one offer that means they never have to
remember this skill again:

```text
Night Shift is on. One last thing: want this to happen every night
automatically? Pick a bedtime — say 23:30 — and your hardware clocks in by
itself. It pauses itself if briefs pile up unread, drops to quiet mode on
battery, and `night-shift snooze` covers vacations.
```

If yes:

```bash
night-shift schedule --nightly 23:30
```

Then close the loop either way:

```text
Sleep well. Tomorrow, just say "good morning" (or run
`night-shift report --latest`) and the brief will be waiting: what it found,
what deserves your attention first, and what stayed draft-only.
```

## Bedtime (returning user)

Config exists. Do not re-onboard, do not explain the product, do not announce
that setup was found. First check `night-shift schedule --status`: if the
standing shift is armed for tonight, say so — "Already armed for 23:30 —
nothing to do. Sleep well." — and only launch manually if they want it to
start now.

Otherwise read the config, recap in one line, offer the fast path:

```text
Same as last night? <repo> · Normal · read-only brief · stop after 8h · local: qwen2.5-coder:14b
```

- Yes → `night-shift start --yes` (add `--repo <repo>` if the conversation is
  elsewhere). Confirm launch in two lines, wish them goodnight, done.
- One thing changed ("focus on tests tonight", "go harder") → override just
  that flag (`--goal "..."`, `--mode afterburner`) and keep the rest saved.
- If they seem to be doing this manually every night, offer Autopilot once:
  "Want me to just schedule this?"
- Before launching heavy modes as the coordinator, follow the startup gate in
  `references/operations.md`; worker prompt templates live in
  `references/worker-prompts.md`. If a lane is down, degrade honestly (the CLI
  does this) — never pretend a lane ran.

## Autopilot (make it run every night)

When the user wants Night Shift automatic — "every night", "schedule it",
"I keep forgetting":

1. Confirm setup exists (`night-shift start` first if not — run First Night).
2. Ask for a bedtime; recommend a time after they usually stop working.
3. Arm it and show exactly what was armed:
   ```bash
   night-shift schedule --nightly 23:30
   night-shift schedule --status
   ```
4. Say the three safety behaviors out loud — they are why this is trustable:
   - **It pauses itself when ignored.** After 3 unread morning briefs, the
     nightly run stops and waits; reading a brief (`report --latest`) resumes
     it. No zombie automation making reports nobody reads.
   - **It respects the machine.** On battery it drops to quiet mode; every
     run still honors the stop timer and thermal limits.
   - **It is one command to stop.** `night-shift schedule --off`, or
     `night-shift snooze --days 7` for a vacation.
5. Optional, only if `gh` is signed in and the user wants results on GitHub:
   morning delivery. `night-shift deliver --latest --github-issue` keeps
   exactly ONE digest issue per repo updated with the latest brief — it never
   writes code, never opens more issues, never pushes. Offer it, never assume
   it.

## Snooze (vacations and pauses)

- "Pause for a week" → `night-shift snooze --days 7`
- "Back on the 14th" → `night-shift snooze --until 2026-07-14`
- "Resume" → `night-shift snooze --off`
- Always confirm with one line from `night-shift schedule --status`.

## Morning

When the user returns ("good morning", "Complete", "what happened"):

```bash
night-shift stop --latest    # only if a run is still active
night-shift report --latest
```

Reading the brief via `report` also marks it reviewed, which is what keeps an
armed Autopilot running instead of pausing.

Then summarize like a helpful best friend, not a log file. Lead with the one
or two things worth their attention, in plain words, with the evidence path.
Then the honest accounting: status (GREEN/YELLOW/RED), loops run, estimated
tokens by lane, KEEP/MAYBE/REJECT counts, and what stayed unknown or
draft-only. `YELLOW` is a feature, not an apology — it means the machines did
useful work and a human still verifies the best item.

End with a choice, not homework — usually:

1. Turn KEEP item 1 into a narrow draft PR after verification (Codex or this
   assistant reviews, edits in an isolated worktree, runs checks first).
2. Rerun tonight with a narrower mission.
3. Do nothing; the brief was the value.

Never present a worker draft as verified truth, and never claim manual or
hardware proof a human did not check.

## Stop Now

```bash
night-shift stop --latest
night-shift report --latest
```

Report what was stopped and what partial results exist. Full drain-and-verify
steps: `references/operations.md`.

## Tune-Up

For "I got a new GPU", "use my other computer now", "change how hard it
runs": re-run only the relevant step (the Step 3 scan for new hardware, Step
4 for a new network worker), then persist with targeted flags —
`night-shift start --yes --setup-only --windows-url ... --windows-model ...`.
Use `--reset` only when the user explicitly wants to redo setup from scratch.

## Safety Core

The boundaries that make Night Shift trustable. The deep version lives in
`SAFETY.md` next to this file; these never bend:

- `night-shift run` never pushes, merges, releases, publishes, tags,
  notarizes, deploys, or updates appcasts/casks.
- Never change repository visibility, credentials, billing, or user files.
- The only thing Night Shift may ever write to a repo is the single opt-in
  digest issue from `deliver --github-issue` — never code, never more than
  one issue, never without the user turning it on.
- Boring-safe beats ambitious: if a cheap worker proposes broad, destructive,
  private-data, release-touching, or file-reorganization work, mark it
  `REJECTED` and tighten the prompt. Cheap workers do not choose their scope.
- Workers draft; nothing a worker says is truth until Codex or a human
  verifies it against the live repo.
- Draft PRs happen only after review, in an isolated worktree, with checks
  run — and only from deduped `KEEP` items.
- No secrets, customer data, transcripts, or private user data in prompts.
  Local lanes see prompts on this machine; the Windows lane sees prompts on
  that worker; plan accordingly with the user's privacy answer.
- Do not make a repository public from any Night Shift workflow; old refs and
  cached objects outlive a clean-looking branch.

## Going Deeper

Read these only when the moment needs them (they are one level deep, next to
this file):

- `references/hardware-scan.md` — full probe reference, model picking,
  install offers, Windows/LAN worker setup, scan troubleshooting.
- `references/operations.md` — modes and their loop/token budgets, launch
  checklist, startup gate, lane routing, limits, execution pattern, the Local
  Heavy / Tokenmaxx playbook, rehearsal test, closeout formats.
- `references/worker-prompts.md` — the worker prompt contract, all lane
  templates, and KEEP/MAYBE/REJECT scoring.
- `README.md` — user-facing quickstart.
- `SAFETY.md` — the full safety and privacy boundary.
