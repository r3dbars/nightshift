# Safety And Privacy

Night Shift may do useful repository work overnight: focused tests, one
existing E2E journey, stale docs, narrow issue fixes, reproducible failing-check
repairs, and exact one-file cleanup. With saved hands-on consent, a verified
patch may become a GitHub draft PR. Night Shift never merges, releases, deploys,
or edits the checkout you are using.

## The Controller Is In Charge

Models do not choose their own permissions. Before dispatch, the controller
assigns a trusted intent that fixes the allowed file types, file and line limit,
exact verification command, baseline requirement, and publication policy.

Repository text and model output are untrusted. Night Shift never runs a
repository or model-proposed command on the host. Approved checks run only from
an external owner approval, as exact argv without shell operators, in a
rootless Docker or Podman sandbox with no network, a read-only source mount, no
host credentials, and resource and time limits.

The same check runs twice before editing. The finished patch must pass twice,
or three times for E2E work. A repair is proven only when the same assertion
failure reproduces twice and the patch fixes it. Missing tools, timeouts,
infrastructure errors, skipped checks, and flaky outcomes are not proof.

## Draft PR Boundary

A draft PR requires every gate below:

- GitHub proves the signed-in user owns the non-fork repo.
- A separate approval outside the repo is bound to its exact remote.
- The source SHA is on the freshly fetched default branch.
- The diff stays inside the intent's files and size limit.
- The patch adds no dependency, workflow, config, generated, migration,
  secret, network, process, environment, dynamic-code, or release behavior.
- Host Git hooks, custom filters, and executable diff drivers are absent.
- The patch passes fresh repeated sandbox checks again.

Repos with `pull_request_target` or external CI configuration keep the patch
local because publication may trigger privileged automation. Published commits
include `[skip ci]`, PRs remain draft, and publication is capped at one PR per
repo and three per shift. Webhooks are outside Night Shift's control, so review
repo integrations before enabling hands-on mode.

## Hard Stops

Night Shift never:

- merges, approves, force-pushes, releases, deploys, publishes, or tags;
- edits the original checkout or reuses an existing branch;
- changes credentials, secrets, billing, settings, or repo visibility;
- changes workflows, manifests, lockfiles, generated files, migrations, or its
  own approval;
- moves, deletes, or reorganizes user files;
- sends private content to cloud lanes without explicit consent;
- claims hardware, audio, install, hosted, telemetry, or manual proof that was
  not collected.

An in-repo `.night-shift.json` is only a proposal and cannot authorize itself.
Forks, collaborator repos, and unknown ownership remain analysis-only. A human
or trusted coding agent decides what merges.

## Lane Privacy

- Local prompts go to the configured local model server.
- Windows prompts go to `WINDOWS_WORKER_BASE_URL`.
- Claude prompts leave the machine through the configured CLI.
- Codex coordinates and performs explicit user-requested work.

Keep private notes, customer data, raw transcripts, audio, credentials,
payment details, personal data, and unreleased plans on a trusted local lane.
Never paste secrets into prompts.

## Local Artifacts

Runs write ledgers under:

```text
~/.codex/maestro/overnight/night-shift-<timestamp>/
```

These contain scans, queues, worker output, verification proofs, draft records,
token estimates, stop reasons, and the morning brief. Worktrees live under
`~/.codex/night-shift/worktrees/`. Delegate proofs live under
`~/.codex/maestro/runs/` and may repeat prompt content.

ClaudeBrain `brain-intake` writes only a source-linked suggestion packet under
`raw/scraps/`. It does not move raw files or edit authoritative memory.

## Scheduled Runs

Scheduled nights use the same saved boundaries, drop to quiet mode on battery,
honor stop and failure limits, and pause after three unread briefs. Hands-on
mode may open tested draft PRs under the rules above, but never merges them.

Stop gracefully with:

```bash
night-shift stop --latest
```
