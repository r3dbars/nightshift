# Direct Test Evidence Hardening

Date: 2026-07-14

## Change

Test-strengthening missions now receive a longer bounded source excerpt when a
behavior body extends beyond six lines. Copy-ready citations show both the
start and end of that excerpt, and the worker is told to copy the prepared
citation literally rather than renumbering a file excerpt.

## Verification

- Queue and dispatch focused tests: 63 passed.
- Full package gate: 429 tests passed.
- `git diff --check`: passed.

## Live replay boundary

Three fresh local-only Swift replays against
`r3dbars/codex-mission-control` stayed in disposable worktrees and made no
GitHub writes. Each run used two local worker loops and four bounded calls:

- Before the hardening: 11,561 estimated tokens, YELLOW, two rejected items.
- With the longer source excerpt: 11,646 estimated tokens, YELLOW, two rejected items.
- With the literal-citation instruction: 11,788 estimated tokens, YELLOW, two rejected items.

The validator rejected off-by-one or unsupported citations each time. No
verified draft was counted, and no efficiency score increase is claimed. This
is useful fail-closed evidence about the current local model's citation
formatting, not proof of an accepted outcome.
