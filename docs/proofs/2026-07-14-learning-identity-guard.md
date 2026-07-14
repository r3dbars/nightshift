# Feedback And Handoff Identity Guard

## Scope

This pass hardens two places where the local learning loop could quietly lose
signal:

- task families with more than one trailing numeric suffix now normalize to the
  same family;
- a completed read-only handoff now records when learning could not be updated
  because the candidate fingerprint, source revision, or verdict was missing.

No cloud handoff, GitHub write, draft PR, merge, or deployment was performed.

## Evidence

- Claude read-only audit: `~/.codex/maestro/runs/20260714T192503Z-handoff-learning-audit-claude`
- Focused proof: five handoff/feedback tests passed.
- Full gate: `bash scripts/check-package.sh` passed **459 tests** and package checks.
- The scorecard remains conservative: Learning loop stays **90/95** and
  Cloud-agent handoff stays **88/95** because multi-night accepted outcomes and
  a real user-approved cloud review are still unproven.

## Files

- `bin/night_shift_feedback.py`
- `bin/night_shift_handoff.py`
- `bin/night-shift`
- `tests/test_night_shift.py`
