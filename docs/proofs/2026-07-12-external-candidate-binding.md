# External Candidate Revision Binding Proof

Date: 2026-07-12

## Claim

External repo approval revalidates the exact candidate commit immediately before
execution. Approval of a clean checkout cannot be reused for an unadvertised
local candidate.

## Negative Proof

A fresh `r3dbars/Draft` clone at advertised HEAD received an external approval
in a disposable Night Shift home. A second commit object was created locally
without changing the checkout or pushing it.

`run_isolated_draft` received that unadvertised 40-character commit and returned:

```text
REJECT | external approval requires the exact candidate commit to be advertised by the approved remote | not executed
```

No sandbox, model, patch, or proof artifact was started. HEAD and the checkout
remained unchanged and clean.

## Positive Proof

A clean sparse clone of `r3dbars/nightshift` under the real macOS home used an
external approval rather than its checked-in local profile. The loader reported:

```text
external repo approval loaded
python3 -m unittest discover -s tests -p test_*.py
```

The candidate used the exact advertised HEAD. Night Shift:

- revalidated the candidate against remote heads/tags;
- created a detached disposable worktree;
- ran the approved command in the real no-network, read-only Docker/Colima
  sandbox;
- passed the complete 174-test baseline with return code 0;
- correctly stopped before any model or patch because no failure reproduced;
- removed the worktree;
- left the source checkout clean.

This proves external approval reaches real isolated verification safely. It does
not prove a useful repair, because the clean baseline intentionally prevented
patch generation.

## Deterministic Gate

The package gate passes 176 tests. Focused coverage requires an externally
approved candidate to use an exact SHA-1 or SHA-256 commit advertised by the
bound remote, proves rejection occurs before sandbox startup, and proves an
advertised candidate proceeds to sandbox dispatch. Typed profile metadata binds
the approved remote without relying on a display string.
