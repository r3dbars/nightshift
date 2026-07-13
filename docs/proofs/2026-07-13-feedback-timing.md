# Feedback Timing Proof

This proof checks the local review-effort signal through the real CLI.

## Run

- Source revision: `b388986`
- Ledger: disposable temporary path containing spaces
- Setup: one `MAYBE` work-queue item and a `REVIEWED` marker three seconds in
  the past
- Command: `CODEX_HOME=<temporary-home> bin/night-shift feedback --ledger <ledger> --item 1 --useful`
- Result: `NIGHTSHIFT_FEEDBACK: GREEN`
- Recorded event: `feedback_delay_seconds: 3.0`

The feedback file stayed under the disposable `CODEX_HOME`; no real user
feedback, repo files, network data, or GitHub state changed. This measures
elapsed time from the recorded brief view to the vote. It is not a claim about
the user's actual cognitive review time, and it does not raise usefulness or
learning scores by itself.
