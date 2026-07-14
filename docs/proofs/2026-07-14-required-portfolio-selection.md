# Required portfolio selection proof

Date: 2026-07-14

## Change

Final portfolio selection now protects both the explicit primary repository
and explicit priority repositories when the configured `max_repos` capacity
can hold them. A high-scoring non-priority repository cannot displace a saved
priority row while the primary repository is being retained.

## Deterministic proof

- `test_portfolio_selection_protects_priority_rows_when_capacity_allows` uses
  one noisy high-score row, two saved priorities, and one low-score primary with
  `max_repos=3`.
- The selected set contains the primary and both saved priorities, proving that
  primary reinsertion does not silently evict a priority row when all required
  rows fit.
- The existing primary-retention test still passes when capacity is smaller
  than the number of required rows.

## Boundary

When more required rows exist than the configured capacity, the primary and
highest-ranked required rows remain bounded by `max_repos`; no portfolio size
limit is expanded.
