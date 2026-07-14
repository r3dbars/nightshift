# Handoff current-consent proof

Date: 2026-07-14

## Change

Cloud handoff now requires the one-time `--allow-cloud` flag on the current
invocation. A saved cloud preference can describe a user's general routing
choice, but it cannot silently authorize a new review send.

## Deterministic proof

- `test_handoff_cloud_run_is_explicit_and_read_only` now runs its first handoff
  attempt with a stored `allow_cloud_reasoning=true` preference and no current
  `--allow-cloud` flag.
- That attempt returns the explicit-consent result before any coding-agent
  command runs.
- The same test then adds `--allow-cloud`, uses a read-only temporary review
  root, and validates the bounded review output as before.

## Boundary

This changes only cloud-send authorization. Local pack preparation remains
available without consent, and a current `--allow-cloud` flag still cannot
bypass pack privacy validation or read-only review restrictions.
