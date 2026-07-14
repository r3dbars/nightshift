# Atomic outcome-ledger proof

Date: 2026-07-14

## Change

`repo-outcomes.jsonl` now writes through a temporary file, flushes and syncs
that file, then replaces the destination atomically. A failed replacement no
longer leaves the learning ledger truncated or empty.

## Deterministic proof

- `test_outcome_ledger_preserves_existing_rows_when_atomic_replace_fails`
  injects a replacement failure after the new content has been written.
- The original row remains readable, the new row is not partially visible, and
  the temporary file is cleaned up.
- The existing bounded-retention test still proves the ledger keeps only the
  newest configured rows.

## Boundary

This protects local outcome-ledger integrity during interruption or filesystem
failure. It does not claim a useful user outcome or raise the learning score
without real accepted/revised/rejected feedback across later runs.
