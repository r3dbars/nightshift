# Latest-Feedback Learning Proof

Date: 2026-07-13

## Bug fixed

Queue selection already treated a changed user verdict as latest-wins. Morning
ranking separately summed every historical verdict, so changing one exact
candidate from useful to not useful could retain stale positive weight.

Both paths now use the same exact-candidate latest-verdict reducer. Run metrics
also snapshot raw history events, current preferences, current useful choices,
and current not-useful choices so later runs can be compared without rewriting
history.

## Verification

- Changed-verdict tests prove one candidate has one current preference.
- Morning ranking applies only the final not-useful verdict.
- Outcome metrics preserve two history events while reporting one current
  not-useful preference.
- `scripts/check-package.sh` passed 308 tests and package checks.

## Live boundary

`night-shift health` reported zero current preferences and zero history events
in the user's real profile. This change therefore fixes and instruments the
learning loop, but does not prove multi-night user-rated outcome lift. The
Learning loop score remains 70 until later real rated runs demonstrate that
accepted outcomes improve or wasted tokens fall.
