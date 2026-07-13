# Tracker Issue Gate Proof

Date: 2026-07-12

## Claim

Normal mode does not spend model tokens on multi-item GitHub tracking issues.
Afterburner can still explore them. A no-work run reports `YELLOW` consistently
and does not tell the user that healthy compute setup is broken.

## Baseline

The prior fresh three-repo rehearsal spent about 6,031 Windows-model tokens on
two multi-item tracking issues. Both reviews were rejected:

- BetterFeedback issue #161 contained five unchecked production-hardening tasks.
- Draft issue #41 contained seven unchecked public-release tasks.

One review proposed a broad production storage and rate-limit project. The
other wandered from a release checklist into unrelated architecture docs.
Neither produced a patch or deterministic outcome.

## Rehearsal

The same GitHub scope was run from another empty Night Shift home:

```sh
night-shift autopilot --repo /Users/redbars/code/night-shift \
  --scope github-recent --active-days 14 --max-repos 3 --task-limit 6 \
  --mode night-shift --permission draft-local --guidance scan \
  --stop-after 2h --timeout 300 --once --skip-smoke
```

Results:

- BetterFeedback: 40 weak signals skipped, including the five-item tracker.
- Draft: 40 weak signals skipped, including the seven-item tracker.
- Night Shift: 28 weak signals skipped.
- Model calls: 0.
- Estimated model tokens: 0.
- Patches and PRs: 0.
- Portfolio terminal and morning status: `YELLOW`.

A direct repeat on Night Shift also used zero calls and zero tokens. Its terminal
and morning report both said `YELLOW`; the morning report said that nothing had
enough evidence to work on safely while showing startup gate `GREEN`.

## Deterministic Gate

The package gate passes 163 tests. Focused coverage proves that Normal mode
rejects multi-item trackers, Afterburner accepts them, single-action issues stay
eligible, and empty grounded runs do not blame compute setup.

This proves lower waste and clearer reporting. It does not prove useful output,
so the useful-output score does not move.
