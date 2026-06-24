# Night Shift Troubleshooting

Start here when setup feels confusing:

```bash
night-shift doctor --repo /path/to/project
```

## What The Status Means

| Status | Meaning | What to do |
| --- | --- | --- |
| `GREEN` | Ready. | You can run `night-shift start` or `night-shift run`. |
| `YELLOW` | Usable, but something needs attention. | Read the next step printed by `doctor`. |
| `RED` | A required thing is missing. | Fix the named blocker first. |
| `INFO` | Optional detail. | You can ignore it unless you wanted that feature. |

## Common Fixes

| Message | Simple fix |
| --- | --- |
| `git not found` | Install Git, then rerun `night-shift doctor`. |
| `night-shift missing or not executable` | From the repo, run `./install.sh`. |
| `LM Studio not reachable` | Open LM Studio, start the local server, load the model, then rerun `doctor`. |
| `expected model not listed` | Load that model or pass `--local-model MODEL_NAME`. |
| `Windows worker not configured` | Ignore it for Mac-only setup, or pass `--windows-url http://HOST:11434/v1`. |
| `dirty lines=` | Night Shift will not edit this checkout directly. Commit/stash your work or let it run read-only. |
| `no origin remote configured` | Fine for local toy repos. Add a remote only if you want fetch checks. |
| `on battery` | Plug in before Normal or Afterburner mode. |
| `not on PATH` | Use `~/.codex/bin/night-shift`, or add `~/.codex/bin` to your shell `PATH`. |

## Setup Lab Files

Every setup writes a small lab folder under `~/.codex/maestro/overnight/`.

- `lab/readiness.json`: what passed, warned, or failed.
- `lab/providers.json`: which AI providers were configured and reachable.
- `lab/routing.json`: privacy, mode, stop timer, and user intent.

These files are safe to inspect. They should not contain API keys.

## Recovery

Stop the latest run:

```bash
night-shift stop --latest
```

Read the latest result:

```bash
night-shift report --latest
```

Make a no-model planning brief:

```bash
night-shift plan --repo /path/to/project --mode quiet
```
