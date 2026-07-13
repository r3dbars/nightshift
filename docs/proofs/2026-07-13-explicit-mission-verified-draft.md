# Explicit Mission Verified Draft

This is the real current-main replay after PR #168. It proves the explicit
mission path can select a declared repository symbol, ask for a focused
behavioral test, recover from a malformed worker patch, and leave a verified
local draft without touching the source checkout.

## Run

- Source revision: `0b6ac39e3a04ffa685c197949d342240e6c60fbf`
- Mission: `Add one focused behavioral regression test proving patch_input_directory handles two artifact paths`
- Command shape: local-only `autopilot --scope current --mode afterburner --permission draft-local --execute-drafts --guidance goal --once`
- Parent ledger: `/var/folders/89/3nbfpj616353kk0f99t9vg3c0000gn/T/tmp.G2N5Ctvm5H/maestro/overnight/night-shift-20260713T235107Z-autopilot`
- Child afterburner ledger: `/var/folders/89/3nbfpj616353kk0f99t9vg3c0000gn/T/tmp.G2N5Ctvm5H/maestro/overnight/night-shift-20260713T235109Z-afterburner`
- Result: `NIGHTSHIFT_AUTOPILOT: YELLOW | cycles=1 | local=1 | tokens=3238`

## Verified result

- Draft status: `VERIFIED_DRAFT`
- Baseline check: exit `0`
- Post-patch check: exit `0`
- Isolated sandbox check: exit `0`
- Changed files: `tests/test_night_shift_queue.py` only
- Guard reasons: none
- Temporary worktree removed: yes
- Verification command: `python3 -m unittest discover -s tests -p 'test_*.py'`
- Patch artifact: `.../drafts/r3dbars--nightshift/mission-brief-install-draft-pr-candidate-verification-sandbox-1/applied.patch`

The first worker response was malformed. The bounded recovery path produced the
verified patch above, which demonstrates recovery behavior rather than silently
accepting a worker claim. No GitHub PR was opened because the run used
`draft-local`; human usefulness review is still pending.

## Package gate

After the replay, the current checkout passed:

```text
python3 -m unittest discover -s tests -p 'test_*.py'  -> 402 tests, OK
bash scripts/check-package.sh                         -> package checks passed
```

This proof supports explicit-goal routing, deterministic evidence, bounded
patch preparation, recovery, and cleanup. It does not yet support 95/100 for
repeated useful output, multi-repo usefulness, draft-PR creation, morning
comprehension, or multi-night learning.
