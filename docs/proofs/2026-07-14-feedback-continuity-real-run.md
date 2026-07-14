# Feedback Continuity Real Run

Date: 2026-07-14

## Run

Night Shift ran one fresh current-main cycle using the real saved local
feedback file at `/Users/redbars/.codex/night-shift/feedback.jsonl`. The
feedback contained one prior useful vote for `r3dbars/nightshift` in the
`changed-file-proof` family.

Command:

```sh
CODEX_HOME=/Users/redbars/.codex \
  /Users/redbars/code/night-shift/bin/night-shift start --yes --once --skip-smoke
```

Artifacts:

- Parent ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260714T023610Z-autopilot`
- Child ledger: `/Users/redbars/.codex/maestro/overnight/night-shift-20260714T023632Z-night-shift`
- Source revision in the child scan: `9559a31015ff1b2bb6eddb8d70ff30d260cd81c`

## What Was Observed

The child morning brief reported:

```text
Learning signals for this repo: useful=1 not useful=0 history events=1

What I learned from your last votes:
- You marked changed-file-proof useful. Note: The isolated test draft was verified and became merged PR 111. I will look for more work like this.
```

The portfolio brief also explained the ranking as:

```text
your current project; you marked recent work here useful
```

The run spent 20,932 local tokens across seven calls, found three evidence-
backed MAYBE choices, and made no GitHub or source-checkout writes. The
feedback note was redacted before it was written to the morning artifact.

This proves that a real vote changes the next brief in plain language and
survives into portfolio ranking. It does not prove multi-night outcome lift,
repeated user-rated accepted patches, or a useful overnight result by itself.

