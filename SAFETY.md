# Safety And Privacy

Night Shift is allowed to do useful repository work overnight. On a new
install, the normal hands-on setting can create small patches, run approved
checks, and open bounded GitHub draft PRs for review. It still cannot merge,
release, deploy, or edit the checkout you are using.

The safety model is simple: the model proposes code, but the controller decides
what the model is allowed to touch and what counts as proof.

## How A Patch Earns Trust

Before a model runs, Night Shift assigns a trusted intent such as test
strengthening, E2E strengthening, docs repair, narrow issue fix, safe refactor,
or failing-check repair. Each intent fixes:

- the exact file types it may change;
- the maximum file and line count;
- the exact approved verification command;
- whether the baseline must be clean or reproducibly failing;
- whether the result may become a draft PR.

Repository files and model output are untrusted input. Night Shift never runs a
discovered package script, Makefile target, shell snippet, or model command on
the host. Verification runs only from an external owner approval, as an argv
array without shell operators, in a rootless Docker or Podman sandbox with no
network, a read-only source mount, no host credentials, and CPU, memory, PID,
and time limits.

The approved check must produce the same result twice before editing. The
finished patch must pass twice, or three times for E2E work. Only the same real
assertion failure reproduced twice and then fixed is called a `PROVEN_REPAIR`.
Missing tools, infrastructure errors, skipped checks, timeouts, and flaky
results are never counted as proof.

## What Night Shift May Do

With saved hands-on consent and a trusted owned repository, Night Shift may:

- add or strengthen one focused unit or E2E test;
- fix one narrow source-grounded issue;
- repair stale setup, test, quickstart, or command documentation;
- remove one exact piece of redundant code in a recently changed source file;
- repair a reproducible failing check;
- preserve a verified patch in an isolated worktree;
- push one unique branch and open a draft PR after fresh repeated verification.

Publication is capped at one draft PR per repo and three per shift. More
verified patches stay local for the morning brief.

## What It Never Does By Itself

- Merge, approve, or auto-merge a pull request.
- Release, deploy, publish, tag, notarize, update an appcast, or update a cask.
- Edit the user's original checkout.
- Force-push or reuse an existing branch.
- Change credentials, secrets, billing, account settings, or repo visibility.
- Change workflows, dependency manifests, lockfiles, generated files,
  migrations, policy files, or the Night Shift approval itself.
- Add source-code network, process, environment, secret, or dynamic-code access.
- Move, delete, or reorganize user files.
- Claim hardware, audio, Bluetooth, camera, screen-share, install, hosted, or
  manual QA proof that was not actually collected.
- Run arbitrary repository or model-proposed commands on the host.

A human or trusted coding agent still decides whether any draft PR should
merge.

## Repository Trust

An in-repo `.night-shift.json` file is only a proposal. It cannot authorize its
own repository. Execution requires a separate approval stored outside the repo
and bound to the exact Git remote.

- Only GitHub repos proven to be owned by the signed-in user are eligible.
- Forks, collaborator repos, and unknown ownership stay analysis-only.
- Runner images must already exist locally and be pinned by OCI SHA-256 digest.
- Commands must be JSON argv arrays. Shell strings, pipes, redirects,
  substitutions, and control operators are rejected.
- Custom Git hooks, executable filters, and diff drivers block host checkout.
- Rejected tasks enter a cooldown and retry only after the repo or live signal
  changes.

Before publication, Night Shift fetches the remote again and proves the source
SHA is on the default branch. Repos using `pull_request_target` or external CI
configuration keep the patch local because a same-repo branch could trigger
privileged automation. Published commits include `[skip ci]`, but webhooks are
outside Night Shift's control; review repository integrations before enabling
hands-on mode.

## Manual Approval Boundaries

Require a human decision after the morning review before any of these actions:

- merge a PR or mark a release blocker done;
- publish, release, deploy, tag, notarize, or update distribution metadata;
- change secrets, credentials, billing, settings, or repo visibility;
- send private data to a non-local model;
- claim manual, hardware, install, audio, or real-user validation.

Green checks prove only the exact automated command that ran.

## What Lanes Can See

- Local lane: prompts go to the local OpenAI-compatible server, normally
  `http://localhost:1234`.
- Windows lane: prompts go to `WINDOWS_WORKER_BASE_URL` when configured.
- Claude lane: prompts go to the configured Claude CLI and leave the local
  machine.
- Codex lane: coordinates, reviews, and performs explicit user-requested work.

Private notes, customer data, raw transcripts, audio, secrets, credentials,
payment details, personal contact details, and unreleased sensitive plans must
stay on a trusted local lane. Do not paste secrets into any prompt.

## What Gets Written

Run ledgers live under:

```text
~/.codex/maestro/overnight/night-shift-<timestamp>/
```

They include scans, queues, worker artifacts, verification proofs, draft
records, token estimates, stop reasons, and the morning brief. Isolated
worktrees live under `~/.codex/night-shift/worktrees/`; owned portfolio clones
live under `~/.codex/night-shift/repos/`.

The optional `brain-intake` command may write one local source-linked triage
packet to a ClaudeBrain vault's `raw/scraps/` directory. It does not move source
files or edit authoritative memory, people, projects, notes, or archive pages.

Delegate proof artifacts live under `~/.codex/maestro/runs/`. Worker output may
repeat prompt content, so treat these directories as sensitive.

## Scheduled Nights And Delivery

`night-shift schedule --nightly` uses the same saved boundaries as a manual
start. On battery it drops to quiet mode. Stop timers and failure limits still
apply. After three unread briefs, scheduled runs pause until one is reviewed.

The optional digest issue is updated in place. In hands-on mode, Night Shift may
also open bounded, tested draft PRs under the publication rules above. It never
merges them.

## Windows Network Default

The Windows worker key defaults to `Authorization: Bearer ollama`. This is only
a convenience for a trusted private network, not a production security
boundary. Override the URL, key, and model for your environment:

```bash
export WINDOWS_WORKER_BASE_URL=http://windows-host.local:11434/v1
export WINDOWS_WORKER_MODEL=qwen3-coder:30b
```

## Stop A Shift

```bash
night-shift stop --latest
```

This requests a graceful stop, signals recorded worker process groups, and
prevents new work from starting. For an immediate stop, terminate the related
`night-shift` or `maestro-*` processes with your normal process manager.
