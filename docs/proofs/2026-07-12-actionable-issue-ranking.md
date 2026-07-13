# Actionable Issue Ranking Proof

Date: 2026-07-12

## Claim

Night Shift can rank a bounded, source-grounded GitHub issue ahead of broad
trackers and stale documentation prompts without asking a model to choose.

## Baseline Failures

Three fresh Draft rehearsals exposed and fixed distinct deterministic problems:

1. Generic CamelCase terms matched unrelated source files and admitted release
   issue #37.
2. Repository-order truncation displaced the strongest file match.
3. Feedback ranking alphabetized equal-priority issues, putting #28 before the
   stronger #38 signal.

The final policy uses only explicit backticked symbols and exact repo paths,
ranks files by exact matched-symbol count, and carries issue signal strength
into selection priority.

## Final Rehearsal

A direct run against the real `r3dbars/Draft` checkout used an empty Night Shift
home and a one-task limit:

```sh
night-shift run --repo /tmp/.../r3dbars--Draft-... \
  --mode night-shift --permission draft-local --guidance scan \
  --task-limit 1 --timeout 300 --skip-smoke
```

Results:

- Selected issue: Draft #38, live EOU transcription not firing.
- Selection priority: 440 from four exact issue symbols.
- First candidate file: `Sources/Speech/ParakeetEngine.swift`.
- Exact finding: line 51 sets `private let liveDisplayEnabled = false`.
- Verification command: `bash run-tests.sh`.
- Windows calls: 2, including one bounded evidence correction.
- Estimated tokens: 7,722.
- Validator result: `MAYBE` with zero quality reasons.
- Original checkout status: clean.
- Patch, PR, merge, deploy, and release: none.

The issue remains open and the cited line exists at the pinned revision. Draft
does not contain an approved `.night-shift.json` execution profile, so Night
Shift correctly stopped before isolated patch execution. This is a useful,
reviewable candidate, not a verified repair.

Two follow-up replays selected the same issue and correct first file, but the
Windows worker broadened its claim beyond the cited lines. The validator rejected
both. Across three final-form replays, selection was 3/3 correct and evidence
acceptance was 1/3. This is honest and safe, but not yet reliable enough for a
high useful-output or efficiency score.

## Deterministic Gate

The package gate passes 165 tests. Focused coverage proves bounded issue ranking,
exact symbol-file grounding, selection-priority preservation through feedback,
and one correction pass for exact files pinned to a commit.
