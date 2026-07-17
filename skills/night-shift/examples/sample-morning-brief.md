# Fake Sample Morning Brief

This is fake toy output. It is not from a real run and contains no private user
data, customer data, transcripts, credentials, private repo names, or local
machine paths.

```text
# Morning Brief

Status: GREEN
Mode: Normal, hands-on
Elapsed: 8h 00m
Repositories visited: 3

## Review First

1. Draft PR opened: add checkout failure coverage
   - Repo: example/storefront
   - Intent: E2E strengthening
   - Changed: tests/e2e/checkout.spec.ts
   - Baseline: 2 matching passes
   - Finished patch: 3 matching passes
   - Draft PR: https://github.com/example/storefront/pull/42
   - Why first: it protects a real payment failure path with a small test-only diff.

2. Verified local patch: repair stale setup docs
   - Repo: example/cli-tool
   - Intent: docs repair
   - Changed: README.md
   - Verification: python3 -m unittest, 2 matching passes before and after
   - Patch: drafts/example-cli-tool/docs-repair/applied.patch
   - Why local: the shift-wide draft PR cap was already reached.

3. Candidate: config fallback may need a focused unit test
   - Repo: example/api
   - Evidence: src/config.py:84 and tests/test_config.py:31
   - Status: candidate only; no patch was attempted because the approved runner was unavailable.

## Totals

- Draft PRs opened: 1
- Verified local patches: 1
- Source-grounded candidates: 1
- Rejected or blocked tasks: 7
- Nothing merged, released, or deployed

## What Stayed Honest

- One infrastructure failure stayed BLOCKED instead of being called a test failure.
- One broad refactor was rejected because it exceeded the one-file cleanup policy.
- Manual install and hardware behavior remain UNKNOWN because nobody tested them.

## Best Next Move

Review draft PR #42 first. Then ask your coding agent to inspect the verified
docs patch and the config-test candidate together.

lanes used: Codex=controller and verification; Claude=skipped; Local=18 tasks; Windows=7 tasks
```

Teach the next run after review:

```bash
night-shift feedback --latest --item 1 --useful --outcome accepted
night-shift feedback --latest --item 2 --not-useful --note "not worth a separate PR"
```
