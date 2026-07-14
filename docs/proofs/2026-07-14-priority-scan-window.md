# Priority scan-window proof

Date: 2026-07-14

## Change

Portfolio discovery now signal-scans the ranked candidate window plus every
validated saved-priority or explicit-primary repository that falls outside the
window. Previously, a priority repository below the first `max(10,
max_repos * 4)` candidates could never receive GitHub signal data and could not
be selected for the portfolio.

## Deterministic proof

- `test_portfolio_signal_scan_keeps_required_repos_outside_ranked_window`
  passes with a 12-repository fixture, `max_repos=2`, and a required repository
  at position 12.
- The test confirms that the normal ten-candidate window is preserved and the
  required repository is appended exactly once using case-insensitive matching.
- Full package and hosted CI results are recorded in the merge commit for this
  change.

## Boundary

This guarantees a scan slot only when a saved priority or explicit primary slug
survives normal authenticated discovery filters. It does not make archived,
forked, foreign-owner, or outside-the-active-days repositories eligible.
