# Validator And Log-Noise Proof

Date: 2026-07-14

## Changes

- PR #271 routes repository Python AST inspection through a narrow
  `SyntaxWarning` suppression. Parse failures still fail closed.
- PR #272 stops the validator from treating the literal `./` as a repository
  path.
- PR #273 stops quoted example paths from becoming uncited path claims.
- PR #274 applies the same rule to quoted literals wrapped in Markdown
  backticks, while preserving citation checks for real backticked paths.

## Gates

- Host suite: `478 tests, OK`
- Package gate: `bash scripts/check-package.sh` -> `package checks passed`
- Final replay revision: `595eb75`

## Real clean-checkout replay

Ledger:
`/var/folders/89/3nbfpj616353kk0f99t9vg3c0000gn/T/night-shift-validator-replay3.XXXXXX.x60Wp9hviC/maestro/overnight/night-shift-20260714T221547Z-night-shift`

Observed result:

- `NIGHTSHIFT_RUN: YELLOW | local=1 | windows=0 | tokens=3585`
- One local model call and zero correction calls
- `KEEP=0, MAYBE=1, REJECT=0`
- Validated citation: `bin/night_shift_patch_protocol.py:35`
- Warning scan: `WARNING_SCAN=GREEN`
- No source checkout, GitHub, cloud, or draft-PR write occurred

This is real validator and runtime-noise proof. It is not an accepted user
outcome, so the Efficiency score remains below the promotion threshold.
