# Verbose coverage-intent proof

Date: 2026-07-14

## Change

Explicit coverage intent now survives ordinary explanatory wording. The
matcher accepts action and test/coverage terms within a bounded 128-character
window, instead of silently rejecting a reasonable longer goal after 48
characters.

## Deterministic proof

- `test_coverage_override_requires_explicit_action_and_target` now includes a
  long payment-retry coverage request whose action and target are more than 48
  characters apart.
- The same test still rejects a negated test command and a summary request,
  because neither contains a supported positive coverage action.
- The full package and hosted CI results are recorded in the merge commit for
  this change.

## Boundary

The matcher remains bounded and still requires an allowed action plus an
explicit test, testing, coverage, or regression target. It does not turn every
mention of tests into an explicit coverage override.
