---
name: night-shift
description: Launch and supervise Night Shift, a bounded overnight local-compute work mode. Use when the user asks for Night Shift, goodnight / going to sleep / run overnight / tokenmaxx / use local models / use a Windows GPU worker, wants an on-button for bounded repo work, or returns in the morning with "Complete", "Good morning", "stop the night", or asks what happened overnight.
---

# Night Shift

Tagline: put your idle AI hardware to work while you sleep.

The simplest user promise:

```bash
night-shift start
night-shift report --latest
```

Use this skill as the coordinator cockpit for a bounded overnight run. The goal is useful draft work, not autonomous shipping.

Core rule: local and Windows lanes may draft; Codex reviews and verifies; Claude is rare; `night-shift run` does not edit the target repo; nothing pushes branches, merges, releases, publishes, tags, notarizes, changes repository visibility, changes credentials, or edits billing without the user explicitly saying so after the morning review.

Hard default: boring-safe beats ambitious. If a cheap worker suggests broad,
destructive, private-data, hardware-proof, release, or file-reorganization work,
mark that worker result `REJECTED` and tighten the prompt. Do not let cheap
workers choose their own scope.

Tokenmaxx philosophy: spend local/Windows compute on attention-expensive,
execution-safe work. Make maps, rankings, audits, briefs, issue candidates,
test ideas, and patch plans. Let Codex turn only the best few into real draft
PRs after verification. Unlimited artifacts are good; unlimited GitHub changes
are not.

## Product Shape

User-facing name: `Night Shift`.

Short name: `Night Shift`.

Power modes:

- `Quiet Shift`: low heat, small safe work. Maps to `Conservative`.
- `Night Shift`: normal overnight compute. Maps to `Local Heavy`.
- `Afterburner`: tokenmaxx / full-send local compute. Maps to `Tokenmaxx`.
- `Morning Brief`: stop, harvest, summarize, and tell the user what to review.

Core UX:

1. User runs `night-shift start`.
2. Night Shift asks a few plain-English setup questions.
3. Night Shift detects available AI tools and saves preferences.
4. Night Shift shows a "will / will not" preview before launching.
5. User goes to sleep.
6. User wakes up to a morning brief, artifacts, and at most a few high-signal draft PRs
   that Codex or a human opened after review.

This should meet users where they are:

- Mac only: use LM Studio/local models.
- Windows only: use Windows worker if exposed on the LAN.
- Mac + Windows: use both.
- Claude Code plan: use Claude sparingly for hard reasoning.
- Codex plan: use Codex for orchestration, isolated worktree edits, draft PRs,
  and verification.
- No local models yet: run `doctor`, show exact setup blockers, and fall back to a planning brief.

Public launch blocker: do not make the repository public from a normal Night
Shift workflow. Old closed PR refs, branch refs, review comments, fork refs, and
cached GitHub objects can expose old history even after the visible branch looks
clean. The safest public path is a fresh clean repository from an audited export.
The alternate path is a GitHub-supported purge of old refs, PR refs, cached
objects, and forks before changing visibility.

See `README.md` in this skill folder for the user-facing quickstart and 20 common scenarios.

Preferred launcher:

```bash
night-shift start
night-shift report --latest
```

Use `night-shift start` whenever the user wants a simple setup, a repeatable
run, token accounting, or a portable "night shift" experience. Use direct Codex
threads only when the task requires real repo edits, PRs, manual review, merges,
release work, or this exact chat as the cockpit.

## Setup Wizard

For first-time users, launch with:

```bash
night-shift start
```

The wizard should ask, in plain language:

1. Which project should Night Shift look at?
2. What AI tools should it use?
   - Not sure, check for me.
   - AI coding subscriptions, like Codex or Claude Code.
   - Local AI on this Mac, like LM Studio or Ollama.
   - Local AI on another computer.
   - Local AI on this Mac and another computer.
3. What is Night Shift allowed to do overnight?
   - Read only and make a morning brief.
   - Draft ideas locally, but do not push.
   - Suggest draft PRs after checks pass.
4. How hard should Night Shift work?
   - Quiet.
   - Normal.
   - Afterburner.
5. When should Night Shift stop?
   - When I come back and say stop.
   - After 2 hours.
   - After 6 hours.
   - After 8 hours.

Before launching, always show a preview with:

- Project.
- AI tools detected or configured.
- Mode.
- Safety setting.
- Stop setting.
- Output.
- A clear "Will not" line: no push, merge, release, deploy, delete files,
  billing changes, or credential changes.

The wizard saves preferences at `~/.codex/night-shift/config.json`.
Advanced users can still use `doctor`, `plan`, `run`, `report`, and `stop`
directly.

## Modes

Choose one mode unless the user specifies another.

- `Conservative`: default. 1-3 tasks, max 1 draft PR per repo, local/Windows first, low heat.
- `Local Heavy`: burn local Mac + Windows compute on useful repo work for hours.
  40-80 Mac local loops plus 20-40 Windows loops by default, max 2 draft PRs
  per repo, Codex filters results.
- `Tokenmaxx`: run Mac local + Windows workers hard until the user returns in
  the morning or says `Complete`. Keep filling the queue, harvest often, and
  maximize useful local/Windows token throughput. Max draft PRs still bounded;
  no branch push/merge/release/publish actions from `run`.
- `Fun`: 3-6 tasks, more experiments, still no merge/release.
- `Research`: read-heavy, produces briefs/issues/plans, code changes only if tiny and obvious.
- `Morning Review`: stop active work, collect results, verify claims, and report the next action.

If the user wants the machines to "use tokens", "burn local compute", "work
overnight", "use Windows", "use local models", or says the prior run was too
cautious, use `Local Heavy`. If the user says "tokenmaxx", "maximize hardware",
"run until morning", or "I'll turn it off in the morning", use `Tokenmaxx`. If
the requested mode is unclear, use `Conservative`.

## Launch Checklist

Before launching overnight work:

1. State the selected mode and safety limits in one short update.
2. Run the lane smoke check if available:
   ```bash
   ~/.codex/bin/maestro-smoke.sh
   ```
3. Confirm these as facts or mark them `UNKNOWN`:
   - Mac local model server reachable, usually LM Studio at `localhost:1234`.
   - Windows worker reachable if `WINDOWS_WORKER_BASE_URL` or `--windows-url` is configured.
   - Target repo paths exist.
   - Target worktrees are clean enough or can use fresh isolated worktrees.
   - Power, sleep, and thermal posture are acceptable.
4. Pick tasks from live repo truth, open issues/PRs, recent failures, TODOs, or the user's prompt. Avoid stale memory as repo truth.
5. Create a run ledger path under `~/.codex/maestro/overnight/` when writing artifacts is useful.

If a critical readiness check fails, do not improvise a long night. Fall back to a short research or planning run and report the blocker.

For normal users, prefer the productized startup path:

```bash
night-shift start
```

The CLI writes the startup gate, board, artifacts, token report, and morning
brief under `~/.codex/maestro/overnight/`.

## Startup Gate

Before `Local Heavy` or `Tokenmaxx` starts real loops, Codex must prove the
system is good enough to run:

1. Run `~/.codex/bin/maestro-smoke.sh`.
2. Confirm LM Studio is reachable and has at least one local chat model loaded.
3. Confirm the Windows worker endpoint is reachable and lists the expected model.
4. Confirm `~/.codex/bin/maestro-delegate` and `~/.codex/bin/maestro-token-report`
   are executable.
5. Confirm the target repo can be fetched.
6. Confirm dirty worktrees are not used for edits.
7. Create a fresh isolated worktree or clone before any code changes.
8. Write all startup facts into the run ledger before dispatching workers.

If one lane is down:

- If Mac local is down, try one quick restart/remediation only if the fix is
  obvious; otherwise mark `LOCAL_DOWN` and do not call the run Tokenmaxx.
- If Windows is down, mark `WINDOWS_DOWN`; continue only with Mac local if
  the user explicitly allowed degraded mode or the run is useful as read-only
  planning.
- If both cheap lanes are down, do not run. Report `RED` and the exact next
  thing the user should start or fix.
- If the repo is dirty, use it read-only only. Never edit it.

Only after the startup gate is `GREEN` should Tokenmaxx begin high-volume loops.

`night-shift run` performs this gate before dispatching model loops. If
Mac local or Windows is down, it degrades honestly or stops instead of pretending
the lane ran.

## Lane Routing

Prefer the cheapest capable lane.

- `Local`: private triage, summarization, task selection, logs, issue clustering, small planning.
- `Windows`: cheap long-running code drafts and review drafts. Treat output as a draft, not truth.
- `Codex`: final coordination, repo edits when needed, GitHub state, verification, PR creation, morning review.
- `Claude`: hard reasoning or risky architecture only when the budget allows and the prompt justifies it.

In `Local Heavy`, the goal is to keep local compute busy on bounded work:

- Mac local models: use for repeated classification, clustering, review notes,
  TODO mining, log triage, issue drafting, analytics/Sentry summarization, test
  gap discovery, and duplicate/stale PR analysis.
- Windows worker: use for longer draft reviews, test ideas, patch plans, and
  low-risk draft implementation sketches.
- Codex: every 30-60 minutes, harvest artifacts, reject junk, select the best
  items, run real repo commands, and optionally open draft PRs.
- Claude: only for one or two high-leverage architecture/risk questions.

Mode mapping for the CLI:

- `quiet`: low heat and low parallelism.
- `night-shift`: normal overnight Mac local + Windows work.
- `afterburner`: tokenmaxx mode with larger loop targets.

For non-Codex lanes, prefer:

```bash
~/.codex/bin/maestro-delegate <local|windows|claude> --label <label> -- "<self-contained prompt>"
```

A lane counts as used only if there is a proof path, `MAESTRO_PROOF=...`, command output, or a saved transcript. Require every worker closeout to include:

```text
lanes used: Codex=...; Claude=...; Local=...; Windows=...
```

## Worker Prompt Contract

Cheap workers must get small, closed-form prompts. Prefer classification,
clustering, issue drafting, and bounded review over open-ended "go improve this"
requests.

Every non-Codex worker prompt should include:

- `ROLE`: local triage / Windows draft worker / Claude risk reviewer.
- `TASK`: one narrow task.
- `ALLOWED`: exact files, commands, or read-only scope.
- `FORBIDDEN`: push branches, merge, release, publish, tag, notarize, deploy,
  appcast/cask, repository visibility, credentials, billing, private user data,
  destructive cleanup, broad rewrites, real hardware/audio claims, and
  unapproved file reorganization.
- `OUTPUT`: an exact schema.
- `STOP`: stop after the requested output; do not continue inventing work.

Use this local classification template:

```text
ROLE: local triage classifier.
TASK: classify the overnight task.
ALLOWED_LABELS: SAFE_OVERNIGHT, HOLD_RELEASE, HOLD_PRIVATE, HOLD_BROAD, HOLD_DESTRUCTIVE
RULES:
- Return exactly one line.
- Format: LABEL | one short reason.
- No extra paragraphs.
TASK_TO_CLASSIFY: <task>
```

Use this Windows draft template:

```text
ROLE: Windows draft worker.
TASK: propose safe overnight work only.
ALLOWED: tests, docs, fixtures, read-only audits, narrow issue lists, small draft PR ideas.
FORBIDDEN: branch push/merge/release/publish/tag/notarize/deploy/appcast/cask, repository visibility, credentials, billing,
private user data, destructive cleanup, file reorganization, audio mutation, broad rewrites,
real hardware/audio proof claims.
OUTPUT:
- exactly 3 bullets
- each bullet must be safe, narrow, and reviewable in the morning
- end with: lanes used: Codex=skipped; Claude=skipped; Local=skipped; Windows=draft only
STOP: no extra text.
```

If the output violates the schema, rambles, invents categories, suggests unsafe
work, or ignores `STOP`, record it as `YELLOW` or `RED`. Do not use that result
as a task source without Codex rewriting it.

For `Local Heavy`, use loop prompts that produce artifacts instead of vague
advice. Each loop must have an artifact file under the run ledger.

Use this Mac local loop template:

```text
ROLE: Mac local repo analyst.
TASK: <one narrow scan: TODOs/tests/analytics/events/docs/errors/PR dedupe>
INPUTS: <repo paths, command outputs, or pasted snippets only>
FORBIDDEN: private user data, raw transcripts, secrets, destructive edits, release actions.
OUTPUT:
1. FINDINGS: exactly 5 bullets max
2. BEST_NEXT_ACTION: one concrete task
3. SAFE_FOR_DRAFT_PR: yes/no
4. CONFIDENCE: low/medium/high
STOP: no extra text.
```

Use this Windows long-worker template:

```text
ROLE: Windows long-running draft worker.
TASK: <one narrow implementation/review/test-planning task>
ALLOWED: draft patches, pseudodiffs, test plans, file/path suggestions, review notes.
FORBIDDEN: branch push/merge/release/publish/tag/notarize/deploy/appcast/cask, repository visibility, credentials, billing,
private user data, destructive cleanup, file reorganization, audio mutation, broad rewrites,
real hardware/audio proof claims.
OUTPUT:
1. SUMMARY: 2 sentences max
2. FILES_TO_TOUCH: up to 6 paths
3. PROPOSED_CHANGE: concise patch plan or review findings
4. TESTS_TO_RUN: exact commands
5. RISK: low/medium/high
6. SAFE_FOR_CODEX_TO_ATTEMPT: yes/no
7. lanes used: Codex=skipped; Claude=skipped; Local=skipped; Windows=draft only
STOP: no extra text.
```

Codex must score every artifact:

- `KEEP`: useful and safe enough to become a task, issue, or draft PR.
- `MAYBE`: useful idea but needs human/Codex rewrite.
- `REJECT`: unsafe, broad, duplicate, stale, private, release-touching, or low signal.

Only `KEEP` items may become draft PRs.

## Safe Work Menu

Good overnight tasks:

- Add or repair focused tests.
- Fix small obvious bugs with clear repro or failing checks.
- Improve docs, comments, scripts, fixtures, or telemetry guardrails.
- Run narrow security/privacy sweeps with deterministic checks.
- Triage issues and open polished GitHub issues.
- Produce draft PRs for low-risk cleanup.
- Create morning briefs from verified evidence.
- Build or update tiny deterministic fixtures.
- Draft small issues from existing failures or TODOs.
- Create no-code, read-only product/analytics/Sentry/PostHog briefs.
- Mine TODOs/FIXMEs and classify them by risk and payoff.
- Compare open PRs against current main and identify duplicates/superseded work.
- Search for missing tests around recently changed files and draft focused test plans.
- Audit analytics taxonomy and dashboards for product-decision blind spots.
- Audit Sentry issue families and produce fix candidates without touching release.
- Run static searches for dead code, oversized files, and risky seams, then rank them.
- Generate morning-ready issue drafts with exact files, repro hints, and checks.

Avoid or hold:

- Merge, release, publish, tag, notarize, deploy, or update appcast/cask.
- Push commits or branches from `night-shift run`.
- Make repositories public or change repository visibility.
- Broad "improve the app" prompts.
- Secrets, credentials, billing, private user data, or destructive migrations.
- Hardware/audio/manual-proof claims without real proof.
- Duplicate PRs when an open nightly PR already owns the gap.
- File reorganization, renaming user artifacts, deleting data, moving captures,
  or mutating audio unless the user explicitly asked for that exact action.
- Any task where success requires this Mac's microphone, Bluetooth, AirPods,
  camera, screen permissions, or a real meeting app while the user is away.

## Limits

Set explicit caps before launching workers. Defaults:

- `max_runtime`: 8 hours.
- `max_tasks`: 3 in Conservative, 6 in Fun.
- `max_draft_prs`: 1 per repo unless the user asks for more.
- `max_cloud_calls`: 0-1 Claude calls, Codex only for coordination and final verification.
- `max_failures`: stop a lane after 2 repeated failures on the same task.
- `thermal`: stop or pause if fans/temperature become concerning.
- `sleep`: do not prevent sleep unless the user explicitly wants the machines held awake.

`Local Heavy` defaults:

- `max_runtime`: 8 hours.
- `target_local_loops`: 40-80.
- `target_windows_loops`: 20-40.
- `min_total_estimated_tokens`: 500,000.
- `stretch_total_estimated_tokens`: 2,000,000.
- `max_parallel_local`: 3.
- `max_parallel_windows`: 2.
- `max_draft_prs`: 2 per repo.
- `max_cloud_calls`: 0-1 Claude calls.
- `harvest_interval`: 30-60 minutes.
- `stop_if`: two repeated failures on the same lane, laptop heat/fans are
  concerning, repo truth says release work should pause, or outputs are mostly
  `REJECT`.
- `morning_review_required`: always.
- `token_accounting`: record per-call estimated input/output/total tokens from
  `~/.codex/maestro-sidecar/events.jsonl` and summarize local, Windows, Claude,
  and Codex totals in the morning brief.

`Tokenmaxx` defaults:

- `max_runtime`: until the user says `Complete`, `Good morning`, or `stop the night`;
  otherwise cap at 12 hours.
- `target_local_loops`: keep queue full; start with 120.
- `target_windows_loops`: keep queue full; start with 80.
- `min_total_estimated_tokens`: 2,000,000.
- `stretch_total_estimated_tokens`: 10,000,000+.
- `max_parallel_local`: 4.
- `max_parallel_windows`: 2.
- `max_draft_prs`: 3 per repo.
- `max_cloud_calls`: 0-1 Claude calls.
- `harvest_interval`: 20-30 minutes.
- `stop_if`: thermal/fan concern, repeated lane failure, network/model down,
  repo safety risk, release blocker, outputs become mostly junk, or the user
  says stop.
- `must_report_underuse`: if total estimated local/Windows tokens are below
  2M by morning without a blocker, mark the run `YELLOW`.

Use shell `timeout`, worker-level caps, or process supervision when available. If a tool like `gnhf` is used, add its own `--max-iterations`, `--max-tokens`, and `--stop-when` limits.

## Execution Pattern

1. Build a tiny task board:
   - `task`
   - `repo`
   - `lane`
   - `allowed files`
   - `stop condition`
   - `verification`
   - `artifact path`
2. Dispatch independent tasks in parallel when safe.
3. Use fresh worktrees or dedicated branches for repo changes.
4. Keep each task narrow enough to review in the morning.
5. Commit and push only the files changed for that task when the repo's global instructions require it.
6. Open draft PRs only for clean, useful, low-risk work after Codex or a human
   reviews the artifact, edits in an isolated worktree, and runs checks.
7. Save proof: command outputs, test names, PR links, branch names, and blockers.
8. Stop lanes that drift, touch unrelated files, repeat failed fixes, or claim success without evidence.

## Local Heavy / Tokenmaxx Pattern

When running `Local Heavy` or `Tokenmaxx`, do this instead of a single small worker:

1. Build a compute board with enough narrow loops to keep hardware busy. Start
   with at least 12 tasks, then rotate/retry until the token or time budget is
   reached. Good first board:
   - release blockers and open PR state
   - TODO/FIXME/code smell mining
   - missing tests around recent files
   - analytics/PostHog blind spots
   - Sentry issue family triage
   - docs/release wording drift
   - oversized files/refactor candidates
   - stale branch/PR dedupe
   - deterministic replay/fixture ideas for meeting, dictation, import, and agent flows
   - PR description/test proof audits
   - code-map summarization by subsystem
   - failing/slow/flaky test risk mining
   - user-story to test/analytics coverage gaps
2. Create a ledger:
   - `board.md`
   - `artifacts/<task>-local.md`
   - `artifacts/<task>-windows.md`
   - `harvest.md`
   - `morning.md`
3. Dispatch Mac local loops and Windows loops with strict templates. Use bigger
   pasted context packs when safe so the local hardware is actually doing work:
   2k-8k tokens per Mac local prompt and 4k-16k tokens per Windows prompt.
4. Do not trust workers. Codex harvests and scores each artifact as `KEEP`,
   `MAYBE`, or `REJECT`.
5. Codex may turn only the best `KEEP` item into a draft PR, using a fresh
   worktree and real tests.
6. If a worker finds something release-impacting, hold it for morning review.
   Do not patch release flow overnight without the user's explicit approval.
7. The final morning brief must include:
   - local loops run
   - Windows loops run
   - estimated local input/output/total tokens
   - estimated Windows input/output/total tokens
   - whether the minimum token budget was reached
   - artifacts kept/rejected
   - compact `KEEP`, `MAYBE`, and `REJECT` summaries
   - top 5 ranked actionable items
   - draft PRs opened
   - tests run
   - what the user should do first
   - what the user should review first
   - what stayed unknown/manual

If no draft PR is safe, still consider the night successful if it produced a
useful ranked morning brief from real artifacts and hit the local/Windows work
budget. If it stops below the minimum estimated token budget without a hard
blocker, mark the run `YELLOW` for underuse.

For `Tokenmaxx`, after each harvest:

1. Run `~/.codex/bin/maestro-token-report` over the current run directories.
2. If useful artifacts are scarce, tighten prompts and continue rather than
   stopping early.
3. If a board item is exhausted, generate the next board item from live repo
   truth, not imagination.
4. Prefer many read-only/code-grounded scans over risky draft edits.
5. Keep Codex awake as the queue manager; local/Windows do the bulk thinking.

Best Tokenmaxx workloads:

- Codebase map: summarize every subsystem, what it does, main risks, missing
  tests, and weird files.
- Test gap mining: compare changed/risky files to test coverage and propose
  exact test files or fixtures.
- PostHog/Sentry thinking: mine events/issues into product and reliability
  hypotheses without changing code unless Codex verifies.
- PR cleanup intelligence: compare open/stale PRs to main and classify merge,
  superseded, cherry-pick, close, or hold.
- User story coverage: list app behaviors, expected behavior, tests covering
  them, analytics covering them, and unknowns.
- Refactor candidates: find oversized files, duplicated patterns, unclear
  boundaries, and rank by payoff/risk.
- Release readiness briefs: summarize what changed, what blocks release, what
  manual QA remains, and what proof is deterministic vs manual.
- Tiny PR idea generation: propose many small fixes; Codex opens only the best
  few after live repo verification.

Do not use Tokenmaxx for:

- branch pushes from `run`, release cuts, merges, tags, notarization,
  appcast/cask updates, repository visibility changes, or deploys
- real hardware/audio/manual-proof claims
- broad refactors without human approval
- destructive file cleanup or moving user artifacts
- private user data, raw transcripts, audio refs, titles, names, emails,
  tokens, raw URLs, raw paths, raw devices, or source-app identifiers

## Rehearsal Test

When the user asks to test Night Shift, run a tiny no-edit rehearsal:

1. Create a ledger under `~/.codex/maestro/overnight/test-<timestamp>/`.
2. Run `~/.codex/bin/maestro-smoke.sh`.
3. Run one local classification using the local classification template.
4. Run one Windows draft using the Windows draft template.
5. Validate both outputs against their schemas.
6. Kill or confirm there are no leftover rehearsal processes.
7. Report:

```text
MAESTRO_OVERNIGHT_TEST: GREEN/YELLOW/RED | smoke | local output verdict | Windows output verdict | no repo edits | no PRs | ledger | next adjustment
```

Only call the rehearsal `GREEN` if lane smoke passes and both cheap-worker
outputs obey the schema and stay inside the safe work menu.

## Morning Stop

When the user says `Complete`, `Good morning`, `stop the night`, or similar:

1. Stop or gracefully drain active `maestro`, `gnhf`, `codex`, `claude`, `opencode`, and worker processes that belong to the overnight run.
2. Do not start new work.
3. Reconstruct state from live proof, not memory:
   ```bash
   pgrep -fl 'maestro|gnhf|codex|claude|opencode|rovodev' || true
   git status --short
   git log --oneline --decorate --max-count=20
   ```
4. Inspect branches, PRs, notes, logs, and changed files.
5. Run independent verification for any branch that looks promising.
6. Report a short morning brief.

## Closeout Format

For launch:

```text
MAESTRO_OVERNIGHT_STARTED: GREEN/YELLOW/RED | mode | runtime cap | tasks launched | lanes | cloud budget | stop command | ledger
```

For morning:

```text
MAESTRO_OVERNIGHT_COMPLETE: GREEN/YELLOW/RED | what got done | PRs/branches | proof | blocked | needs user review | next action | lanes used: Codex=...; Claude=...; Local=...; Windows=...
```

Keep the coordinator answer short. The first screen should tell the user what happened, what is blocked, and what they should do first.

For `Local Heavy` launch, include local/Windows loop counts:

```text
MAESTRO_OVERNIGHT_STARTED: GREEN/YELLOW/RED | Local Heavy | runtime cap | local loop target | Windows loop target | token target | draft PR cap | cloud budget | ledger
```

For `Tokenmaxx` launch:

```text
MAESTRO_OVERNIGHT_STARTED: GREEN/YELLOW/RED | Tokenmaxx | run until morning/stop phrase | local queue target | Windows queue target | min/stretch token target | draft PR cap | ledger
```

For `Local Heavy` morning:

```text
MAESTRO_OVERNIGHT_COMPLETE: GREEN/YELLOW/RED | local loops run | Windows loops run | estimated local tokens | estimated Windows tokens | kept/rejected artifacts | PRs/branches | tests/proof | needs user review | next action | lanes used: Codex=...; Claude=...; Local=...; Windows=...
```
