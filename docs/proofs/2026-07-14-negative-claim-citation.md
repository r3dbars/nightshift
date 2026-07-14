# Negative-claim citation proof

Date: 2026-07-14

## Change

Worker prompts now state the evidence rule that the validator already enforces:
when a claim says a repository source path is missing or lacks behavior, the
evidence must cite that same source path and line. A synthetic coverage or
invocation index alone cannot support a negative source claim.

## Real trigger

The live revision `fa64028` used one local model attempt on
`changed-file-proof-02-bin-night-shift-portfolio-py`. The candidate identified
a plausible missing behavioral test for `PortfolioEngine.repo_slug`, but was
rejected because its evidence cited only
`coverage-index/bin-night_shift_portfolio.py-repo_slug.txt:5` while the claim
named `bin/night_shift_portfolio.py`.

## Deterministic proof

- Prompt tests assert the negative-claim rule appears in both correction and
  normal worker context.
- The validator remains fail-closed; this change does not accept the old
  malformed candidate.
- A post-merge live run must produce a separately verified candidate before
  this improves usefulness or efficiency scores.
