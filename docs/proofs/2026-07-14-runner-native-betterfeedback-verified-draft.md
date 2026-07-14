# Runner-Native BetterFeedback Verified Draft

Date: 2026-07-14

This is a local-only proof of the external repository approval and isolated
draft path. It does not authorize a GitHub write, cloud review, or merge.

## Run

- Repository: `r3dbars/BetterFeedback`
- Candidate source revision: `c8160e7109e496e7048498e667275d309a986678`
- Disposable clone: `/Users/redbars/.codex/night-shift/probe.XVNhEI/BetterFeedback`
- Explicit goal: add a focused behavioral test for `formatPercent` in
  `tests/unit/lib/analytics-metrics.test.ts`.
- Trust: the owned GitHub remote, repository identity, approved argv, and
  pinned runner image were reviewed by `trust-repo`.
- Dependencies: a runner-native Linux `node_modules` cache was prepared in a
  disposable networked setup container and then reused read-only.
- Execution: `draft-local`, `--execute-drafts`, Mac-only routing, no GitHub
  writes.

## Result

Night Shift produced one `VERIFIED_DRAFT` after isolated execution. The patch
changed exactly one allowed test file, the approved
`npm run test:unit:vitest` command exited `0`, and the disposable worktree was
removed after verification. The canonical `/Users/redbars/code/BetterFeedback`
checkout was not touched.

The run used 19,558 estimated local tokens across seven calls. It also
rejected two weaker candidates. Those candidates are not counted as useful
outcomes.

## Artifacts

- Parent ledger: `/var/folders/89/3nbfpj616353kk0f99t9vg3c0000gn/T/tmp.uDB2x7lLwm/maestro/overnight/night-shift-20260714T150645Z-autopilot`
- Child ledger: `/var/folders/89/3nbfpj616353kk0f99t9vg3c0000gn/T/tmp.uDB2x7lLwm/maestro/overnight/night-shift-20260714T150648Z-night-shift`
- Verified patch: `drafts/r3dbars--BetterFeedback/changed-file-proof-02-app-analytics-analytics-metrics-ts-tests-draft-pr-candidat-sandbox/applied.patch`
- Verification result: `.../draft-pr-candidat-sandbox/verification.rc` contains `0`
- Changed paths: `.../draft-pr-candidat-sandbox/changed-paths.txt`

This raises confidence in runner portability and isolated local usefulness. It
does not raise hosted draft-PR, cloud-handoff, or human-acceptance scores.
