# Rejected Draft Reason Proof

Date: 2026-07-14

## Real replay

I ran a fresh current-main Night Shift mission against the Night Shift repo with
a bounded behavioral-test goal, local Mac AI, `--privacy mac-only`, draft
execution enabled, and a two-hour limit. The mission used two local model calls,
zero Windows calls, and exited successfully.

The worker produced a candidate, but the isolated verification sandbox failed.
Night Shift correctly rejected the draft and removed its temporary worktree:

- draft status: `REJECT`
- worker result: `rc=0`
- sandbox result: `rc=1`
- guard reason: `isolated verification did not pass`
- source checkout: unchanged

## Reporting defect and fix

The first morning brief rendered the internal applied-patch path after
`Draft: REJECT`, which was confusing and exposed an implementation detail. The
portfolio reporter now shows the human-readable rejection reason for rejected
or otherwise unproven drafts. Patch paths remain available for proven or
verified drafts, where they are useful to a reviewer.

## Verification

The focused regression and the full package gate pass:

```text
Ran 2 tests ... OK
Ran 416 tests ... OK
package checks passed
```
