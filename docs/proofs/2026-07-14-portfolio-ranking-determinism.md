# Portfolio Ranking Determinism

Date: 2026-07-14

## Change

Added dedicated portfolio-ranking tests covering repeated discovery, shuffled
input rows, score ties, and the explicit primary-repository guarantee.

## Deterministic proof

- A fixed five-repository GitHub fixture was discovered three times.
- Each run produced the same four selected rows and scores:
  `owner/broken=340`, `owner/active=130`, `owner/issue=90`, and
  `owner/extra=80`.
- Reversing the input order still produced score-descending, slug-ascending
  output.
- A low-scoring primary repository stayed selected when the portfolio limit
  would otherwise exclude it.

## Verification

- `python3 -m unittest tests/test_night_shift_portfolio_ranking.py -v`
- `./scripts/check-package.sh`
- 427 tests passed.

## Proof boundary

This proves mechanical repeatability of portfolio selection on fixed fixture
data. It does not prove that live rankings consistently match accepted user
value, varied-account discovery, or useful hosted outcomes. Those scorecard
dimensions remain below 95 until their live evidence exists.
