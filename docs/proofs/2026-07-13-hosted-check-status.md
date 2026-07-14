# Hosted Draft Check Status

This proof covers the GitHub status boundary added after the July 13 quality
review. A draft PR is not called healthy just because it was opened. Night
Shift now reads the GitHub check rollup briefly, records `passed`, `failed`,
`pending`, or `unknown`, and shows that state in the portfolio morning brief.

## Deterministic proof

- PR #180 added the parser, bounded polling, publish artifact field, and
  morning-brief line.
- The package gate passed on the working tree with 408 tests.
- The parser tests cover Check Run `conclusion`, Status Context `state`, an
  in-progress check, a failed check, and an empty rollup.
- Unknown or missing data cannot become `passed`. Only explicit `SUCCESS`
  results pass.

## Live GitHub proof

Command:

```text
gh pr view 491 --repo r3dbars/BetterFeedback --json number,isDraft,statusCheckRollup
```

Night Shift's parser reported:

```json
{"hosted_checks":{"check_count":3,"failed":["Vercel - betterfeedback-327","Vercel - trybetterfeedback"],"pending":[],"state":"failed","unknown":[]},"isDraft":true,"number":491}
```

The source rollup contained the two failing Vercel checks and one Vercel
Preview Comments check. The draft remains a human-review item; this proof does
not claim that the hosted PR is useful or ready to merge.

## Remaining gap

We still need a fresh, independently useful Night Shift draft PR whose hosted
checks pass across a varied repository. This change improves truthfulness and
the morning decision surface, but it does not manufacture a successful PR.
