# Worker Prompt Contract and Templates

How to prompt cheap workers so their output is usable in the morning. Read
this alongside `operations.md` when dispatching local or Windows loops.

## The Contract

Cheap workers must get small, closed-form prompts. Prefer classification,
clustering, issue drafting, and bounded review over open-ended "go improve
this" requests.

Every non-Codex worker prompt should include:

- `ROLE`: local triage / Windows draft worker / Claude risk reviewer.
- `TASK`: one narrow task.
- `ALLOWED`: exact files, commands, or read-only scope.
- `FORBIDDEN`: push branches, merge, release, publish, tag, notarize, deploy,
  appcast/cask, repository visibility, credentials, billing, private user data,
  destructive cleanup, broad rewrites, real hardware/audio claims, and
  unapproved file reorganization.
- `OUTPUT`: an exact schema.
- `STOP`: stop after the requested output; do not continue inventing work.

If the output violates the schema, rambles, invents categories, suggests
unsafe work, or ignores `STOP`, record it as `YELLOW` or `RED`. Do not use
that result as a task source without Codex rewriting it.

For `Local Heavy`, use loop prompts that produce artifacts instead of vague
advice. Each loop must have an artifact file under the run ledger. The queue
should be repo-specific: prefer recent files, detected test commands, open
issues/PRs, TODOs, docs drift, and the user's stated mission over generic
categories. Repeated worker findings should strengthen one deduped work item,
not flood the morning brief.

## Local Classification Template

```text
ROLE: local triage classifier.
TASK: classify the overnight task.
ALLOWED_LABELS: SAFE_OVERNIGHT, HOLD_RELEASE, HOLD_PRIVATE, HOLD_BROAD, HOLD_DESTRUCTIVE
RULES:
- Return exactly one line.
- Format: LABEL | one short reason.
- No extra paragraphs.
TASK_TO_CLASSIFY: <task>
```

## Windows Draft Template

```text
ROLE: Windows draft worker.
TASK: propose safe overnight work only.
ALLOWED: tests, docs, fixtures, read-only audits, narrow issue lists, small draft PR ideas.
FORBIDDEN: branch push/merge/release/publish/tag/notarize/deploy/appcast/cask, repository visibility, credentials, billing,
private user data, destructive cleanup, file reorganization, audio mutation, broad rewrites,
real hardware/audio proof claims.
OUTPUT:
- exactly 3 bullets
- each bullet must be safe, narrow, and reviewable in the morning
- end with: lanes used: Codex=skipped; Claude=skipped; Local=skipped; Windows=draft only
STOP: no extra text.
```

## Mac Local Loop Template

```text
ROLE: Mac local repo analyst.
TASK: <one narrow scan: TODOs/tests/analytics/events/docs/errors/PR dedupe>
INPUTS: <repo paths, command outputs, or pasted snippets only>
FORBIDDEN: private user data, raw transcripts, secrets, destructive edits, release actions.
OUTPUT:
1. FINDINGS: exactly 5 bullets max
2. BEST_NEXT_ACTION: one concrete task
3. FILES_TO_TOUCH: up to 5 exact paths, or none
4. TESTS_TO_RUN: exact commands, or none
5. ACTION_TYPE: brief | issue | patch-plan | draft-pr-candidate | reject
6. SAFE_FOR_DRAFT_PR: yes/no
7. CONFIDENCE: low/medium/high
STOP: no extra text.
```

## Windows Long-Worker Template

```text
ROLE: Windows long-running draft worker.
TASK: <one narrow implementation/review/test-planning task>
ALLOWED: draft patches, pseudodiffs, test plans, file/path suggestions, review notes.
FORBIDDEN: branch push/merge/release/publish/tag/notarize/deploy/appcast/cask, repository visibility, credentials, billing,
private user data, destructive cleanup, file reorganization, audio mutation, broad rewrites,
real hardware/audio proof claims.
OUTPUT:
1. SUMMARY: 2 sentences max
2. FILES_TO_TOUCH: up to 6 paths
3. PROPOSED_CHANGE: concise patch plan or review findings
4. TESTS_TO_RUN: exact commands
5. RISK: low/medium/high
6. ACTION_TYPE: brief | issue | patch-plan | draft-pr-candidate | reject
7. SAFE_FOR_CODEX_TO_ATTEMPT: yes/no
8. lanes used: Codex=skipped; Claude=skipped; Local=skipped; Windows=draft only
STOP: no extra text.
```

## Scoring

Codex must score every artifact:

- `KEEP`: useful and safe enough to become a task, issue, or draft PR.
- `MAYBE`: useful idea but needs human/Codex rewrite.
- `REJECT`: unsafe, broad, duplicate, stale, private, release-touching, or low signal.

Only deduped `KEEP` items may become draft PR candidates.
