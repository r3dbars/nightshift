# Fake Sample Ledger Output

This is fake toy output. It is here to show what Night Shift leaves behind in
the morning. Do not treat any path, repo, metric, or finding below as real.

Night Shift writes a ledger like this:

```text
~/.codex/maestro/overnight/night-shift-20260624T064500Z-night-shift/
|-- startup-gate.md
|-- board.md
|-- context-pack.txt
|-- artifacts/
|   |-- test-gap-map-local.md
|   |-- docs-drift-map-windows.md
|   `-- proof-audit-local.md
|-- harvest.md
|-- token-report.txt
`-- morning.md
```

## startup-gate.md

```text
# Startup Gate

Status: GREEN

- GREEN maestro-delegate: /Users/example/.codex/bin/maestro-delegate
- GREEN maestro-token-report: /Users/example/.codex/bin/maestro-token-report
- GREEN maestro-smoke: /Users/example/.codex/bin/maestro-smoke.sh
- GREEN git: /usr/bin/git
- GREEN gh-auth: logged in
- GREEN local-models: LM Studio reachable; models=['phi-4-mini-instruct']
- GREEN windows-worker: Windows worker reachable; models=['qwen3-coder:30b']
- GREEN repo: /Users/example/code/public-demo-repo head=abc1234 clean
- GREEN repo-fetch: ok
```

## board.md

```text
# Night Shift Board

Mode: night-shift

| item | safe lane | artifact |
| --- | --- | --- |
| release-readiness | local/windows | Find release blockers, proof gaps, and manual QA unknowns. |
| test-gap-map | local/windows | Find missing deterministic tests around current risky files. |
| docs-drift-map | local/windows | Find setup, release, or agent docs that may be stale or confusing. |
| proof-audit | local/windows | Check whether current proof separates deterministic, telemetry, and manual evidence. |

All work is artifact-first. No merge, release, publish, tag, notarize, deploy,
appcast, cask, credentials, billing, or user-file cleanup.
```

## artifacts/test-gap-map-local.md

```text
1. TASK_ID: test-gap-map
2. FINDINGS:
- `src/config.py` has fallback behavior for a missing config file.
- `tests/test_config.py` covers valid config but not the fallback.
- The risk is small and deterministic.
3. BEST_NEXT_ACTION: Add one test for missing config file fallback behavior.
4. SAFE_FOR_DRAFT_PR: yes
5. CONFIDENCE: high
```

## artifacts/docs-drift-map-windows.md

```text
1. TASK_ID: docs-drift-map
2. SUMMARY: Setup docs still mention `old-demo-run`, but the CLI now uses
`demo run`. This is a docs-only fix.
3. FILES_TO_TOUCH: README.md, docs/setup.md
4. PROPOSED_CHANGE: Replace stale command examples and keep wording scoped to setup.
5. TESTS_TO_RUN: python3 -m py_compile tools/demo_cli.py
6. RISK: low
7. SAFE_FOR_CODEX_TO_ATTEMPT: yes
8. lanes used: Codex=skipped; Claude=skipped; Local=skipped; Windows=draft only
```

## harvest.md

```text
# Harvest

## KEEP

1. test-gap-map-local
   - score: 94
   - reason: high-confidence, deterministic test gap with exact files.
   - next: Codex should verify and add the smallest test-only change.

2. docs-drift-map-windows
   - score: 81
   - reason: exact stale command references and low-risk docs fix.
   - next: Do after the test gap if time remains.

## MAYBE

1. proof-audit-local
   - reason: useful manual-proof concern, but needs human review.

## REJECT

1. broad-refactor-windows
   - reason: suggested a file reorganization with no exact bug.

2. release-publish-local
   - reason: tried to publish release notes. Night Shift does not release.
```

## token-report.txt

```text
# Night Shift Token Report

Local:
- calls: 40
- estimated input tokens: 418000
- estimated output tokens: 62000
- estimated total tokens: 480000

Windows:
- calls: 18
- timed out: 2
- estimated input tokens: 141000
- estimated output tokens: 31000
- estimated total tokens: 172000

Claude:
- calls: 0
- estimated total tokens: 0

Total local+Windows: 652000
Target: 500000
Status: GREEN
```

## morning.md

```text
# Morning Brief

Status: YELLOW
Mode: night-shift
Startup gate: GREEN
Artifacts: KEEP=3, MAYBE=6, REJECT=49
Draft PRs opened: 0
Manual proof: UNKNOWN

What happened:
- Local and Windows lanes produced draft artifacts.
- Codex scored the artifacts and kept only narrow, reviewable items.
- No release, deploy, merge, credential, billing, or file cleanup action ran.

Review first:
1. test-gap-map-local: verify the missing config fallback test.
2. docs-drift-map-windows: fix stale setup commands if still true.
3. proof-audit-local: have a human decide whether the manual QA claim should stay UNKNOWN.

Next action:
- Ask Codex to verify KEEP item 1 and open one draft PR if the gap is real.

lanes used: Codex=harvested and scored artifacts; Claude=skipped; Local=40 draft loops; Windows=18 draft loops plus 2 timeouts
```
