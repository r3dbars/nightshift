# Night Shift Examples

These are copy-paste starting points. Replace `/path/to/project` with your repo.

Night Shift is artifact-first. Local, Windows, and Claude lanes can
think and draft. Codex verifies before code, PRs, merges, or releases happen.

## Quiet Shift

Use this for low heat, short runs, or a laptop on battery.

```bash
night-shift doctor --repo /path/to/project
night-shift run --repo /path/to/project --mode quiet
night-shift report --latest
```

Good Quiet Shift tasks:

- Find missing tests.
- Check docs drift.
- Draft one small issue list.

## Night Shift

Use this for a normal overnight run.

```bash
night-shift doctor --repo /path/to/project --smoke
night-shift plan --repo /path/to/project --mode night-shift
night-shift run --repo /path/to/project --mode night-shift
```

In the morning:

```bash
night-shift report --latest
```

## Afterburner

Use this when you want to spend idle local and Windows compute hard.

```bash
night-shift doctor --repo /path/to/project --smoke
night-shift run --repo /path/to/project --mode afterburner
```

Stop it cleanly:

```bash
night-shift stop --latest
night-shift report --latest
```

Afterburner should still avoid merges, releases, deploys, credentials, billing,
and manual hardware proof claims.

## Mac-Only

Use this when LM Studio is your only worker.

```bash
export MAESTRO_LOCAL_MODEL=phi-4-mini-instruct
night-shift doctor --repo /path/to/project
night-shift run --repo /path/to/project --mode quiet --max-windows 0
```

Best fit: private triage, TODO mining, docs drift, and test-gap maps.

## Windows Worker

Use this when you have a Windows GPU worker on your LAN.

```bash
night-shift doctor --repo /path/to/project \
  --windows-url http://windows-host.local:11434/v1 \
  --windows-model qwen3-coder:30b

night-shift run --repo /path/to/project \
  --mode night-shift \
  --windows-url http://windows-host.local:11434/v1 \
  --windows-model qwen3-coder:30b
```

Best fit: draft patch plans, longer review notes, and exact test ideas. Treat
Windows output as a draft, not truth.

## Claude Lane

Use Claude sparingly for hard reasoning, architecture, or risk review.

```bash
~/.codex/bin/maestro-delegate claude --label risk-review -- \
  "ROLE: Claude risk reviewer. TASK: Review this repo plan for correctness risks. ALLOWED: read-only reasoning. FORBIDDEN: code edits, merge, release, deploy, credentials. OUTPUT: 5 bullets max plus tests to run. STOP."
```

The proof path prints as `MAESTRO_PROOF=...`. Keep that path in the run notes.

## Codex Verification

Use Codex after the run to turn only the best artifact into real work.

```bash
night-shift report --latest
sed -n '1,220p' ~/.codex/maestro/overnight/*/harvest.md | tail -n 120
```

Then ask Codex:

```text
Review the latest Night Shift harvest. Pick the best KEEP item, verify it against
the repo, make only that narrow change, run tests, commit, push, and open a
draft PR. Do not merge or release.
```

## Morning Harvest

Use this when you wake up or want to stop the run.

```bash
night-shift stop --latest
night-shift report --latest
```

Read these first:

```bash
latest="$(ls -td ~/.codex/maestro/overnight/night-shift-* | head -n 1)"
sed -n '1,220p' "$latest/morning.md"
sed -n '1,220p' "$latest/harvest.md"
sed -n '1,160p' "$latest/token-report.txt"
```

See these fake sample outputs:

- [sample-morning-brief.md](sample-morning-brief.md): what the morning summary looks like.
- [sample-ledger-output.md](sample-ledger-output.md): what the ledger files look like.
