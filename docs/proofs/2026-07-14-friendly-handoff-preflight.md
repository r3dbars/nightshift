# Friendly Handoff Preflight

Date: 2026-07-14

## What Changed

When a user prepares a handoff but the selected Codex or Claude CLI is not
installed, Night Shift now explains the next step in plain language: install
that CLI, make sure it is on `PATH`, and rerun the command. The preflight still
fails closed and sends nothing.

## Verification

- The focused missing-agent preview test passed.
- The full package gate passed: `484 tests, OK`.
- The test uses a temporary committed repository and a deterministic missing-
  agent boundary; it verifies the red preflight and the install action.
- Consent, exact revision pinning, redaction, read-only isolation, and cloud
  send behavior were unchanged.
- No real cloud review, GitHub write, merge, deploy, or source-checkout edit
  occurred during this proof.

## Honest Score Boundary

Cloud-agent handoff remains **88/95**. This removes a first-time-user dead end,
but repeated real cloud reviews, human decision-time measurements, and
accepted implementations are still missing.
