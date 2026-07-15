# Safety And Privacy

Night Shift is a bounded overnight work launcher. It is designed to
produce drafts, audits, maps, and morning briefs. It is not an autonomous
release, deploy, cleanup, or credential-management system.

The safety promise is simple: overnight lanes may produce artifacts, but they
do not get to ship. Repository files are untrusted input, so Night Shift does
not run discovered package scripts, Makefiles, or shell commands on the host.
Sandboxed execution is disabled unless the repo owner supplies a reviewed
`.night-shift.json` profile, marks the repo `owned`, names a pinned pre-installed runner image, lists exact argv commands,
and Docker rootless mode or Podman's rootless local engine is available. The sandbox has no network, a read-only
repo mount, no host credentials, and CPU/memory/PID/time limits.
Only failing-before and passing-after is called a proven repair. A human or
Codex still reviews, commits, pushes, and opens any PR.

## What It Never Does By Itself

- Merges pull requests.
- Pushes commits or branches from `night-shift run`.
- Edits the user's original checkout; optional patches live under
  `~/.codex/night-shift/worktrees/`.
- Cuts releases, publishes, tags, notarizes, deploys, updates appcasts, or
  updates casks.
- Changes credentials, secrets, billing, or account settings.
- Makes repositories public or changes repository visibility.
- Moves, deletes, or reorganizes user files.
- Claims real hardware, audio, Bluetooth, camera, screen-share, install, or
  manual QA proof.
- Executes arbitrary commands found in a repository on the host machine.

Codex or a human must review worker output before it becomes a real code
change, PR, merge, release, or public claim.

`night-shift handoff` prepares one redacted KEEP/MAYBE item locally. It sends
nothing unless the user previously approved cloud reasoning or supplies a
one-time `--allow-cloud` consent with `--run`. The Codex handoff is ephemeral,
read-only, cannot edit or push, treats candidate text as untrusted data, and is
accepted only with one structured verdict, a current source citation, and an
explicit implementation-readiness decision.

## Manual Approval Boundaries

Require explicit approval after the morning review before any of these actions:

- Merge a PR or close a release blocker as done.
- Publish a release, deploy, tag, notarize, update an appcast, or update a cask.
- Change secrets, credentials, billing, account settings, or repository
  visibility.
- Send prompts or artifacts containing private data to non-local lanes.
- Claim manual proof, hardware proof, install proof, audio proof, or real-user
  validation.

Green checks mean the automation ran. They do not prove manual, hardware, or
public-surface behavior.

## Repository Profiles And Trust

Copy `.night-shift.json.example` into a repository only after reviewing it.
The profile is an allowlist, not a request from the repository to trust itself:

- `owned` is the only class eligible for sandboxed verification.
- `owned-pr`, `collaborator-pr`, `fork`, and `unknown` remain analysis-only.
- Commands are JSON argv arrays; strings, shell operators, pipes, redirects,
  and substitutions are rejected.
- Runner images must be pinned by OCI SHA-256 digest and are never pulled by an
  unattended shift.
- Dependency manifests, lockfiles, CI/workflow files, policy files, and the
  profile itself are immutable to overnight patch attempts.
- Every rejected task is written to durable history with an exponential
  cooldown. A task only retries after that cooldown or a new repository head.

## What Lanes Can See

- Codex lane: can read and edit the repo when you ask it to do execution work.
- Local lane: sends prompts to the local OpenAI-compatible server at
  `http://localhost:1234` by default. The local model sees the prompt text.
- Windows lane: sends prompts to `WINDOWS_WORKER_BASE_URL` when configured.
  That machine sees the prompt text.
- Claude lane: sends prompts to the configured Claude CLI. Use it only for work
  that is safe to send outside your local machines.

Do not use non-local lanes for private notes, customer data, raw transcripts,
audio, secrets, credentials, payment details, personal contact details, raw
URLs, raw file paths, or unreleased sensitive plans.

Public information can go to any configured lane. Private information should
stay local. Sensitive information should not be pasted at all unless the task
explicitly requires it and the lane is trusted for that data.

## What Gets Written To Disk

Night Shift writes run ledgers under:

```text
~/.codex/maestro/overnight/night-shift-<timestamp>/
```

Typical files include:

- `startup-gate.md`
- `repo-scan.md` / `repo-scan.json`
- `board.md`
- `planned-work-queue.json`
- `context-pack.txt`
- `artifacts/`
- `harvest.md`
- `work-queue.md` / `work-queue.json`
- `morning.md`
- `token-report.txt`
- `verification-proof.json` when one owner-approved deterministic check was requested.
- `run-summary.json` for the controller's factual elapsed time and stop reason.

The delegate wrapper also writes proof artifacts under:

```text
~/.codex/maestro/runs/<timestamp>-<label>-<lane>/
```

Those proof directories store prompt hashes, lane output, stderr, and metadata.
They do not store the raw prompt in `prompt.sha256`, but worker outputs can still
repeat prompt content. Treat the run directories as sensitive if your prompts
contained sensitive material.

Token accounting events are appended to:

```text
~/.codex/maestro-sidecar/events.jsonl
```

Those events contain lane names, model names, output paths, return codes,
durations, and estimated token counts.

## What Not To Paste

Do not paste:

- API keys, tokens, passwords, or private keys.
- Customer data or private repo content that should not leave the selected lane.
- Raw transcripts, audio snippets, meeting titles, speaker names, emails, phone
  numbers, personal addresses, billing details, or payment identifiers.
- Sensitive URLs, private file paths, device identifiers, app titles, or window
  titles.

For sensitive work, use only local lanes and keep prompts coarse.

## Automated Nights And Delivery

The standing schedule (`night-shift schedule --nightly`) runs the same
`run` command with the same boundaries — an unattended night has less
authority than an attended one, never more:

- On battery the run drops to quiet mode; stop timers and failure limits
  still apply.
- After 3 unread morning briefs the nightly run pauses itself until a brief
  is read. Snoozed nights are logged as skipped, never hidden.
- The only remote repository write Night Shift may perform is the single
  opt-in digest issue maintained by `deliver --github-issue`. Isolated draft
  patches stay local and uncommitted; no branch or PR is pushed overnight.

## Taking Repositories Public

Night Shift never changes repository visibility, and no overnight workflow
should. Taking any repo from private to public is a manual, deliberate act by
its owner: even when the current branch is clean, old closed PR refs, branch
refs, review comments, fork refs, and cached GitHub objects can expose old
history.

The safest public-launch path is a fresh clean repository created from an
audited export. The alternate path is a GitHub-supported purge of old refs, PR
refs, cached objects, and forks before changing visibility.

## Network And Auth Defaults

After you configure `WINDOWS_WORKER_BASE_URL`, the Windows worker API key
defaults to `Authorization: Bearer ollama`. That is a convenience default for a
trusted local network, not a production security boundary. Override
`WINDOWS_WORKER_API_KEY`, `WINDOWS_WORKER_BASE_URL`, and
`WINDOWS_WORKER_MODEL` for your own environment.

Example:

```bash
export WINDOWS_WORKER_BASE_URL=http://windows-host.local:11434/v1
export WINDOWS_WORKER_MODEL=qwen3-coder:30b
```

## How To Stop It

Request a graceful stop for the latest run:

```bash
night-shift stop --latest
```

The command writes a `STOP` file into the latest ledger, signals recorded
delegate process groups, and prevents new workers from starting for that run.

If you need an immediate stop, terminate the relevant `night-shift`,
`maestro-delegate`, `maestro-local`, `maestro-windows`, `maestro-claude`,
`curl`, or model-server processes from your shell or process manager.
