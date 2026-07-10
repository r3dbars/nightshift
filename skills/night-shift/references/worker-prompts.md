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

Every finding must also include:

- `CLAIM`: one narrow conclusion.
- `EVIDENCE`: exactly one `path:line - observed fact` entry from supplied context.
- `WHY_NOW`: the recent change, issue, failure, TODO, or mission that makes it timely.
- `TESTS_TO_RUN`: an exact detected verification command.
- `EXPECTED_RESULT`: what passing proof looks like.

Never accept invented paths, line numbers, issue state, failures, or command
results. A self-reported `SAFE_FOR_DRAFT_PR: yes` is not enough for KEEP.
When a negative claim names a file, its evidence must cite that same file.

If the output violates the schema, rambles, invents categories, suggests
unsafe work, or ignores `STOP`, record it as `YELLOW` or `RED`. Do not use
that result as a task source. Retry once with the exact missing fields, then
reject it if it is still ungrounded.

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
1. CLAIM: one specific repo-grounded finding
2. EVIDENCE: exactly one path:line and observed fact, or none
3. WHY_NOW: connect it to a supplied live signal
4. BEST_NEXT_ACTION: one concrete task
5. FILES_TO_TOUCH: up to 5 exact paths, or none
6. TESTS_TO_RUN: exact detected command, or none
7. EXPECTED_RESULT: what would prove the task worked
8. ACTION_TYPE: brief | issue | patch-plan | draft-pr-candidate | reject
9. SAFE_FOR_DRAFT_PR: yes/no
10. CONFIDENCE: low/medium/high
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
1. CLAIM: one specific repo-grounded finding
2. EVIDENCE: exactly one path:line and observed fact, or none
3. WHY_NOW: connect it to a supplied live signal
4. PROPOSED_CHANGE: concise patch plan or review finding
5. FILES_TO_TOUCH: up to 6 exact paths
6. TESTS_TO_RUN: exact detected commands, or none
7. EXPECTED_RESULT: what would prove the task worked
8. RISK: low/medium/high
9. ACTION_TYPE: brief | issue | patch-plan | draft-pr-candidate | reject
10. SAFE_FOR_CODEX_TO_ATTEMPT: yes/no
11. lanes used: Codex=skipped; Claude=skipped; Local=skipped; Windows=draft only
STOP: no extra text.
```

## Scoring

Codex must score every artifact:

- `KEEP`: grounded in supplied evidence, names real files and verification,
  and is safe enough to become a task, issue, or draft PR.
- `MAYBE`: useful idea but needs human/Codex rewrite.
- `REJECT`: unsafe, broad, duplicate, stale, private, release-touching, or low signal.

Only deduped `KEEP` items may become draft PR candidates.
