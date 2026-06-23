# Fake Sample Morning Brief

This is fake toy output. It is not from a real run and does not include private
user data, customer data, transcripts, credentials, private repo names, or
machine-local paths.

```text
# Morning Brief

Status: YELLOW
Mode: night-shift
Started: 2026-06-23 22:15 UTC
Stopped: 2026-06-24 06:45 UTC
Repo: public-demo-repo
Startup gate: GREEN

Loops:
- Local: 40 requested, 40 completed
- Windows: 20 requested, 18 completed, 2 timed out
- Claude: skipped

Token estimate:
- Local input/output/total: 418000 / 62000 / 480000
- Windows input/output/total: 141000 / 31000 / 172000
- Total local+Windows: 652000
- Target: 500000

Artifact scorecard:
- KEEP: 3
- MAYBE: 6
- REJECT: 49

Best KEEP items:
1. test-gap-map-local
   - Found missing deterministic tests around config fallback loading.
   - Evidence: `src/config.py`, `tests/test_config.py`
   - Safe for Codex to attempt: yes
   - Suggested check: `pytest tests/test_config.py`
   - Why first: small test-only change with a clear failure mode.

2. docs-drift-map-windows
   - Found setup docs that still mention an old command name.
   - Evidence: `README.md`, `docs/setup.md`
   - Safe for Codex to attempt: yes
   - Suggested check: `python3 -m py_compile tools/demo_cli.py`
   - Why second: low-risk docs fix, but less important than the test gap.

3. proof-audit-local
   - Found one manual QA claim that should be marked UNKNOWN.
   - Evidence: `docs/release-checklist.md`
   - Safe for Codex to attempt: no, needs human review
   - Why held: worker cannot prove real install or hardware behavior.

Rejected examples:
- Broad refactor suggestion with no exact files.
- Release checklist that tried to publish.
- Worker output that claimed hardware proof without real proof.
- Output that named a private branch from the prompt context.

Draft PRs opened: 0
Tests run by Codex: none yet
Manual proof: UNKNOWN

Next action:
- Ask Codex to verify KEEP item 1 against the repo. If it is real, make the
  smallest test-only change and open one draft PR.

Safety:
- No merges, releases, tags, notarization, deploys, appcast/cask updates,
  billing, credentials, or user-file cleanup were performed.
- Local and Windows outputs are drafts, not truth.
- Manual proof stayed UNKNOWN because no human ran the app.

lanes used: Codex=harvested and scored artifacts; Claude=skipped; Local=40 draft loops; Windows=18 draft loops plus 2 timeouts
```

Copy-paste next step:

```text
Codex, review the latest Maestro morning brief. Verify KEEP item 1 against the
repo. If it is real, make the smallest test-only change, run the mapped tests,
commit, push, and open a draft PR. Do not merge or release.
```
