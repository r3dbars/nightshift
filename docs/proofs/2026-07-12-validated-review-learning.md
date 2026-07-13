# Validated review learning proof

Date: 2026-07-12

## Claim

Night Shift can retain a valid independent handoff verdict and use it on a later
selection pass without suppressing a task family or carrying the verdict to a
new revision.

## Real evidence

Two real pinned, read-only Codex handoffs ran with explicit `--allow-cloud`
consent and wrote local-only rows to
`~/.codex/night-shift/review-outcomes.jsonl`:

| Repository | Fingerprint | Revision | Verdict |
| --- | --- | --- | --- |
| Night Shift | `572faef9...` | `29e4ae657efe...` | CONFIRMED |
| BetterFeedback | `bb384347...` | `69a08846e76b...` | NEEDS_INFO |

Both reviews passed the citation and schema validator. A direct replay through
`apply_review_outcomes` found each exact fingerprint/revision and retained its
latest verdict. Changing only the revision to a new 40-character SHA left both
tasks eligible with no skip.

The BetterFeedback verdict differed from an earlier independent review. The
history therefore preserves verdict transitions and uses the newest valid
decision instead of freezing the first judgment. Identical reruns are deduped.

## Safety and boundaries

- Only valid reviews with an exact fingerprint and source revision are learned.
- `REJECTED` suppresses only that exact fingerprint at that exact repo revision.
- `CONFIRMED` adds a bounded 30-point priority boost.
- `NEEDS_INFO` is recorded but neither boosted nor suppressed.
- Manual user feedback remains in the ranking and is not overwritten.
- A new revision creates a new fingerprint and remains eligible.

This is real persistence and replay evidence, but it is not yet proof that user-
rated acceptance improves over multiple nights. The score remains conservative.

## Verification

- `scripts/check-package.sh`: 241 tests plus package/install checks passed.
- Claude found and helped prevent a ranking regression where automatic outcomes
  could have erased manual-feedback ordering.
- Claude proof: `/Users/redbars/.codex/maestro/runs/20260713T041059Z-night-shift-review-learning-review-claude`.
- Fix re-review: `/Users/redbars/.codex/maestro/runs/20260713T041619Z-night-shift-review-learning-rereview-claude`.
