# Outcome-Aware Learning Replay

Date: 2026-07-14

## What Changed

Feedback ranking now uses explicit human outcomes when they are present:
accepted work keeps the full positive signal, revised work remains positive but
smaller, and rejected work is negative. Legacy useful/not-useful rows keep their
previous weights. This makes the outcome questions in the morning feedback path
affect future task selection instead of only being reported.

## Verification

- Focused feedback tests passed, including accepted/revised/rejected weighting
  and legacy clamp behavior.
- Full package gate: `482 tests, OK`.
- Clean brief replay: one local call, 31 weak signals skipped, 3,634 estimated
  tokens, no GitHub or cloud write.
- Clean draft-local autopilot replay: one local call, 3,667 estimated tokens;
  the generated patch failed isolated verification with an `UnboundLocalError`,
  so Night Shift rejected it and removed the disposable worktree.
- No draft PR, merge, deploy, or source-checkout write occurred.

## Honest Score Boundary

Learning remains **90/95**. The behavior is now wired correctly, but a real
multi-night user-rated outcome lift is still missing. The rejected draft is
recorded as a safety success, not a useful outcome.
