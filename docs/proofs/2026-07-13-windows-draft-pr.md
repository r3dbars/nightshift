# Windows Draft PR Publication Proof: 2026-07-13

This records a real GitHub write after a verified Windows-lane patch.

## Publication

- Repository: `r3dbars/BetterFeedback`
- Source revision: `c8160e7109e496e7048498e667275d309a986678`
- Draft branch: `night-shift/9b346155dc8e`
- Draft PR: [#491](https://github.com/r3dbars/BetterFeedback/pull/491)
- Changed file: `tests/unit/lib/analytics-metrics.test.ts`
- Verification: `npm run test:unit:vitest`
- Local verification: 406 passed, 2 skipped
- Publication status: `DRAFT_PR_OPENED`
- Temporary publication worktree removed: `true`
- Publication proof: `/Users/redbars/.codex/night-shift-bf-windows-proof-Cb5hHH/night-shift/publish-proof/publish.json`

The publisher rechecked the exact source SHA, validated the allowed file set,
ran the approved command in a fresh sandbox, committed the patch in a pinned
publication worktree, pushed a unique branch, and confirmed that GitHub kept
the PR in draft state. Nothing was merged.

## Hosted status

At capture time GitHub reported failures for the two Vercel status contexts
`Vercel - betterfeedback-327` and `Vercel - trybetterfeedback`, with the Vercel
Preview Comments check successful. No passing Ubuntu/macOS GitHub workflow was
reported for this PR, so this artifact is publication proof, not a green
release or merge recommendation.

