# Safety And Privacy

Night Shift is a bounded overnight work launcher. It is designed to
produce drafts, audits, maps, and morning briefs. It is not an autonomous
release, deploy, cleanup, or credential-management system.

## What It Never Does By Itself

- Merges pull requests.
- Cuts releases, publishes, tags, notarizes, deploys, updates appcasts, or
  updates casks.
- Changes credentials, secrets, billing, or account settings.
- Moves, deletes, or reorganizes user files.
- Claims real hardware, audio, Bluetooth, camera, screen-share, install, or
  manual QA proof.

Codex or a human must review worker output before it becomes a real code
change, PR, merge, release, or public claim.

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

## What Gets Written To Disk

Night Shift writes run ledgers under:

```text
~/.codex/maestro/overnight/night-shift-<timestamp>/
```

Typical files include:

- `startup-gate.md`
- `board.md`
- `context-pack.txt`
- `artifacts/`
- `harvest.md`
- `morning.md`
- `token-report.txt`

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
maestro-nightshift stop --latest
```

The command writes a `STOP` file into the latest ledger, signals recorded
delegate process groups, and prevents new workers from starting for that run.

If you need an immediate stop, terminate the relevant `maestro-nightshift`,
`maestro-delegate`, `maestro-local`, `maestro-windows`, `maestro-claude`,
`curl`, or model-server processes from your shell or process manager.
