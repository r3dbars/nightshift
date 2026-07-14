# Feedback Metrics And Rejected-Only Morning Replay

Date: 2026-07-14

## Real replay

I ran a fresh local-only Night Shift batch against the current Night Shift repo
with the saved useful vote copied into an isolated `CODEX_HOME`. The run used
one local model lane, no Windows lane, and a bounded behavioral-test goal.

The run completed with:

- status: `YELLOW`
- local calls: 2, including one bounded retry
- estimated tokens: 5,336
- pre-model weak-signal skips: 6
- accepted candidates: 0
- rejected candidates: 1
- source checkout changes: 0

The candidate was rejected because its evidence did not pass the deterministic
source check. No draft or GitHub write was created.

## Feedback effect

The durable `outcome-metrics.json` recorded the saved vote without mixing it
with unrelated global history:

```json
{
  "feedback_signal_active": true,
  "repo_feedback_events": 1,
  "repo_current_useful_preferences": 1,
  "feedback_adjusted_candidates": 3,
  "feedback_adjustment_total": 75,
  "feedback_positive_adjustments": 3,
  "feedback_skips_before_model": 0,
  "review_outcome_skips_before_model": 0
}
```

The brief carried the vote forward in plain language:

```text
You marked changed-file-proof useful. Note: The isolated test draft was verified and became merged PR 111. I will look for more work like this.
```

## Morning wording fix

Before the fix, a rejected-only run headed its section `Three useful choices`,
which implied that a rejected item was useful. The reporter now says `What I
checked` when no KEEP or MAYBE item survives. The latest replay after the fix
shows the corrected heading and keeps the detailed rejection summary below it.

The worker also proposed a focused behavioral test for the untested
`PortfolioReportEngine.morning_items` ordering contract. That test was added
and verifies rank ordering, portfolio-score tie-breaking, and returned metadata.

The latest raw run ledger is:

```text
/Users/redbars/.codex/night-shift/feedback-effect-replay.dUjzXO/maestro/overnight/night-shift-20260714T131418Z-quiet
```

## Verification

The focused reporting tests and the complete package gate pass 419 tests on the
Mac. No score was raised for the replay itself: it proves feedback continuity,
honest rejection, and clearer UX, but not multi-night accepted-outcome lift.
