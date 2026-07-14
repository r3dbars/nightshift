# Bounded Python Source-Evidence Proof

Date: 2026-07-14

## Change

PR #269 changed `QueueEvidenceIndex.symbol_source_evidence` to stop Python
evidence at the target AST declaration's `end_lineno`. A fixed twelve-line
window could include the next unrelated declaration and make a model cite the
wrong physical line.

## Deterministic proof

- Focused regression: `2 tests, OK`
- Host package gate: `475 tests, OK`
- Package script: `bash scripts/check-package.sh` -> `package checks passed`
- Merged revision: `cae79759f0778c56f2b3d889bcf54296218a238e`
- Linked install: `/Users/redbars/.codex/skills/night-shift` -> repository skill

## Real isolated replay

Command: a temporary `CODEX_HOME` ran `night-shift run` against the merged
checkout with one Mac-local task, no Windows lane, brief permission, and the
repository-approved unittest command.

Ledger:
`/var/folders/89/3nbfpj616353kk0f99t9vg3c0000gn/T/night-shift-evidence-proof.XXXXXX.PRs3cWOX0j/maestro/overnight/night-shift-20260714T215137Z-night-shift`

Observed result:

- `NIGHTSHIFT_RUN: YELLOW | local=1 | windows=0 | tokens=3451`
- One local model call; no correction call
- `KEEP=0, MAYBE=1, REJECT=0`
- Morning brief cited `bin/night_shift_queue.py:50 | return any(`
- No source checkout, GitHub, cloud, or draft-PR write occurred

This proves the bounded evidence reached a real model and survived the
deterministic validator. It does not prove an accepted user outcome or move
the Efficiency score to 95 by itself.
