# Fake Sample Morning Brief

This is sample output only. It is not from a real run and does not include
private user data.

```text
# Morning Brief

Status: YELLOW
Mode: night-shift
Startup gate: GREEN
Local loops: 40
Windows loops: 20
Estimated local+Windows tokens: 612000
Token target: 500000
Artifacts: KEEP=3, MAYBE=7, REJECT=50

Best KEEP items:
1. test-gap-map-local
   - Found one missing regression test around config loading.
   - Safe for Codex to attempt: yes.
   - Suggested check: pytest tests/test_config_loader.py

2. docs-drift-map-windows
   - Found setup docs that still mention an old command name.
   - Safe for Codex to attempt: yes.
   - Suggested check: markdown link check plus install smoke.

3. proof-audit-local
   - Found one manual QA claim that should be marked UNKNOWN.
   - Safe for Codex to attempt: no, needs human review.

Rejected examples:
- Broad refactor suggestion with no exact files.
- Release checklist that tried to publish.
- Worker output that claimed hardware proof without real proof.

Draft PRs opened: 0
Tests run by Codex: none yet
Manual proof: UNKNOWN

Next action:
- Ask Codex to verify KEEP item 1 and open one draft PR if the test gap is real.

Safety:
- No merges, releases, tags, notarization, deploys, appcast/cask updates,
  billing, credentials, or user-file cleanup were performed.
- Local and Windows outputs are drafts, not truth.

lanes used: Codex=harvested and scored artifacts; Claude=skipped; Local=40 draft loops; Windows=20 draft loops
```

Copy-paste next step:

```text
Codex, review the latest Maestro morning brief. Verify KEEP item 1 against the
repo. If it is real, make the smallest test-only change, run the mapped tests,
commit, push, and open a draft PR. Do not merge or release.
```
