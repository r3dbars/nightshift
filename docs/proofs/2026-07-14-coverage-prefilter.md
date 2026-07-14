# Coverage Prefilter Proof

Date: 2026-07-14

## Change

Draft-local runs now skip an automatic coverage-gap candidate when its queue
item has no safe patch path. Brief and afterburner analysis still retain the
candidate. Coverage prompts also require a concrete observable behavior and
reject symbol-presence, import, signature, or textual-match-only proposals.

## Real workflow evidence

The fresh post-merge portfolio pass inspected `r3dbars/transcripted` at
`792a8b52ed5d2759560648d8149e31553b2de39e`. Before this change, its bounded
local attempt spent 5,180 tokens on `recent-change-test-gap`, then rejected the
worker's symbol-presence proposal. The post-merge child ledger
`/Users/redbars/.codex/maestro/overnight/night-shift-20260714T213701Z-night-shift`
recorded the same candidate in `task-skips.json` with the reason `test candidate
has no safe automatic patch path`; it made no model call for that candidate.
The run's only model attempt was a separate Windows PR review at 4,478 tokens,
which also failed closed on unsupported negative evidence.

The pass also visited `r3dbars/BetterFeedback` and `r3dbars/nightshift`, and
recorded honest no-work rows without GitHub writes or source-checkout edits.

## Deterministic proof

```text
python3 -m unittest \
  tests.test_night_shift.NightShiftQualityTests.test_draft_local_skips_non_executable_coverage_gap_before_model \
  tests.test_night_shift.NightShiftQualityTests.test_coverage_gap_has_complete_zero_match_evidence \
  tests.test_night_shift.NightShiftQualityTests.test_explicit_coverage_goal_routes_away_from_ungrounded_mission_brief \
  tests.test_night_shift.NightShiftQualityTests.test_top_level_python_coverage_gap_is_executable_with_complete_ast_evidence
...
Ran 4 tests ... OK

bash scripts/check-package.sh
Ran 474 tests ... OK
package checks passed
```

## Boundary

This reduces wasted local calls; it does not turn a candidate into a verified
draft, open a PR, or claim user acceptance.
