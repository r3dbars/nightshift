# Primary repository slug case proof

Date: 2026-07-14

## Change

Portfolio discovery now matches the current repository's GitHub slug
case-insensitively. GitHub repository slugs are case-insensitive, so a remote
reported as `Owner/Repo` and an authenticated listing reported as `owner/repo`
must describe the same primary project.

## Deterministic proof

- `test_portfolio_matches_primary_repo_slug_without_case_sensitivity` passes
  with a remote URL using `Owner/Repo` and a GitHub listing using `owner/repo`.
- The test confirms the discovered row is the single explicit primary row,
  rather than a non-primary row plus a duplicate fallback.
- The full package and hosted CI results are recorded in the merge commit for
  this change.

## Boundary

The comparison is only case-insensitive. Ownership validation, archive/fork
filtering, active-days filtering, and checkout safety remain unchanged.
