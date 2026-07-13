# Explicit mission grounding proof

Date: 2026-07-12

## Claim

When the user supplies goal guidance, Night Shift should select that mission
before automatic coverage leads, bind named code identities to real source and
tests, and give each distinct goal a distinct retry identity.

## Live diagnostic sequence

Seven bounded Mac-local runs used one task, one worker, no Windows lane, local
draft permission, and the same `DraftEngine.cleanup` behavioral-test mission.
The runs exposed and then exercised these failure modes:

1. Automatic `label_block` coverage outranked the explicit mission and consumed
   about 5,851 local tokens.
2. After priority correction, the mission ranked first but omitted the named
   source file.
3. Source matching found `bin/night_shift_drafts.py`, but the corrected mission
   shared the old generic mission fingerprint and entered cooldown.
4. Goal text entered the fingerprint, but textual coverage could not distinguish
   fixture strings from executable calls.
5. AST invocation evidence proved zero calls, but source selection briefly chose
   a test fixture instead of production code.
6. Non-test source preference and dotted-identity weighting selected the real
   `DraftEngine.cleanup` implementation.
7. Bounded source evidence supplied the exact method, remove, prune, and return
   lines; the remaining retry exposed evidence-line binding that was fixed by
   making invocation metrics self-identifying.

The per-revision rejection circuit eventually stopped further retries without
bypass. These were diagnostic integration runs from the in-progress branch;
they did not produce an accepted patch and are not counted as useful output.

## Final contract

- Explicit mission tasks receive the highest deterministic selection priority.
- Exact goal text is included in the task fingerprint.
- Dotted identities such as `DraftEngine.cleanup` rank co-located non-test
  source above broad keyword matches and test fixtures.
- Python invocation evidence uses AST calls, import aliases, constructor-
  assigned receivers, and owner-aware method matching.
- Unrelated same-named methods do not count.
- Python source evidence starts at the real AST declaration.
- Every invocation evidence entry must independently report a complete scan.
- Autonomous execution requires explicit `analysis=python-ast` and
  `scan_complete=true`; regex-only and non-dotted goals remain planning-only.

## Verification

- `scripts/check-package.sh`: 251 tests plus package/install checks passed.
- Claude found owner-awareness and incomplete-scan bypasses before merge, then
  found no remaining blocker in the final review.
- Initial review: `/Users/redbars/.codex/maestro/runs/20260713T045126Z-night-shift-explicit-mission-review-claude`.
- Conditional re-review: `/Users/redbars/.codex/maestro/runs/20260713T045656Z-night-shift-explicit-mission-rereview-claude`.
- Final review: `/Users/redbars/.codex/maestro/runs/20260713T050251Z-night-shift-explicit-mission-final-review-claude`.
