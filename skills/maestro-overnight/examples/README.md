# Night Shift Examples

These are copy-paste starting points. Replace `/path/to/project` with your repo.

Night Shift is artifact-first. Local, Windows, and Claude lanes can
think and draft. Codex verifies before code, PRs, merges, or releases happen.

## Quiet Shift

Use this for low heat, short runs, or a laptop on battery.

```bash
maestro-nightshift doctor --repo /path/to/project
maestro-nightshift run --repo /path/to/project --mode quiet
maestro-nightshift report --latest
```

Good Quiet Shift tasks:

- Find missing tests.
- Check docs drift.
- Draft one small issue list.

## Night Shift

Use this for a normal overnight run.

```bash
maestro-nightshift doctor --repo /path/to/project --smoke
maestro-nightshift plan --repo /path/to/project --mode night-shift
maestro-nightshift run --repo /path/to/project --mode night-shift
```

In the morning:

```bash
maestro-nightshift report --latest
```

## Afterburner

Use this when you want to spend idle local and Windows compute hard.

```bash
maestro-nightshift doctor --repo /path/to/project --smoke
maestro-nightshift run --repo /path/to/project --mode afterburner
```

Stop it cleanly:

```bash
maestro-nightshift stop --latest
maestro-nightshift report --latest
```

Afterburner should still avoid merges, releases, deploys, credentials, billing,
and manual hardware proof claims.

## Mac-Only

Use this when LM Studio is your only worker.

```bash
export MAESTRO_LOCAL_MODEL=phi-4-mini-instruct
maestro-nightshift doctor --repo /path/to/project
maestro-nightshift run --repo /path/to/project --mode quiet --max-windows 0
```

Best fit: private triage, TODO mining, docs drift, and test-gap maps.

## Windows Worker

Use this when you have a Windows GPU worker on your LAN.

```bash
maestro-nightshift doctor --repo /path/to/project \
  --windows-url http://windows-host.local:11434/v1 \
  --windows-model qwen3-coder:30b

maestro-nightshift run --repo /path/to/project \
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
maestro-nightshift report --latest
sed -n '1,220p' ~/.codex/maestro/overnight/*/harvest.md | tail -n 120
```

Then ask Codex:

```text
Review the latest Maestro harvest. Pick the best KEEP item, verify it against
the repo, make only that narrow change, run tests, commit, push, and open a
draft PR. Do not merge or release.
```

## Morning Harvest

Use this when you wake up or want to stop the run.

```bash
maestro-nightshift stop --latest
maestro-nightshift report --latest
```

Read these first:

```bash
latest="$(ls -td ~/.codex/maestro/overnight/night-shift-* | head -n 1)"
sed -n '1,220p' "$latest/morning.md"
sed -n '1,220p' "$latest/harvest.md"
sed -n '1,160p' "$latest/token-report.txt"
```

See [sample-morning-brief.md](sample-morning-brief.md) for fake sample output.
