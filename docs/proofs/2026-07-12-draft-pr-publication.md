# Draft PR Publication Rehearsal

Date: 2026-07-12

Night Shift attempted to publish one harmless documentation patch against the
exact `origin/main` commit in `r3dbars/nightshift`.

## Result

- GitHub authentication and owned, non-fork repository checks passed.
- The patch was bound to an exact 40-character source SHA.
- Patch validation and the fresh disposable worktree passed.
- The rootless Podman socket became unavailable during fresh verification.
- Publication stopped before commit, push, or PR creation.
- The disposable publication worktree was removed.
- No remote branch was created.

Artifacts:

```text
/tmp/night-shift-live-publish-proof/publish.json
/tmp/night-shift-live-publish-proof/publish-verification.txt
```

This proves the failure boundary, not successful draft-PR creation. A real
tested draft PR is still required before this dimension can approach 95.
