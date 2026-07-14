# Explicit Goal Circuit And Source-Path Replay

Date: 2026-07-14

## Why this replay exists

The BetterFeedback checkout already had a per-revision rejection circuit open
after earlier weak candidates. A new user goal should not retry those old
fingerprints, but it should still be able to ask for one concrete, never-seen
mission.

## Replay 1: safe rejection after a fresh goal

The first fresh goal asked for a behavioral test around `formatMicros`:

```sh
night-shift run --repo /Users/redbars/.codex/night-shift/repos/r3dbars--BetterFeedback-7f3d48748b8e \
  --mode quiet --max-local 1 --max-windows 0 --permission brief \
  --guidance goal --goal 'Add one behavioral regression test for formatMicros in app/analytics/analytics-metrics.ts that covers a bigint value and preserves the displayed micro-dollar unit.' \
  --local-url http://localhost:1234/v1 --local-model qwen/qwen3-coder-next \
  --skip-smoke --timeout 900
```

Night Shift spent one local call (5,377 estimated tokens), then rejected the
worker because its citation did not match the pinned source. No patch or
GitHub write occurred. The run's `model-circuit.json` recorded the explicit
goal bypass and then the circuit returned to `OPEN` after the rejection.

## Replay 2: exact source path wins

The next fresh goal asked for `formatDuration(125)` in the same exact source
file. The run spent one local call and 3,358 estimated tokens. It produced one
`MAYBE` with:

- exact source revision `c8160e7109e496e7048498e667275d309a986678`;
- source evidence for lines 21, 22, and 24-26 of
  `app/analytics/analytics-metrics.ts`;
- the existing test file `tests/unit/lib/analytics-metrics.test.ts`;
- the verification command `npm run test:unit:vitest`.

The morning brief clearly marked the item as `MAYBE`, kept the source
checkout untouched, and recorded no GitHub write. The explicit path named by
the user was selected ahead of broader files that also mention the symbol.

These runs prove fresh explicit-goal routing, source-path grounding, and
fail-closed rejection. They do not count as an accepted patch or a draft PR.
