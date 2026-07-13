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

## Successful Docker Rehearsal

Later the same day, a fresh Colima VM provided a real Docker runtime. Night
Shift rebuilt the reviewed runner as immutable image
`sha256:6ca48b362769883b2b56564a9f339ec17ce25ce4b364b2000610269a0f44cccc`
and repeated the exact-main rehearsal from a production-path disposable
worktree.

- Source SHA: `b37c4b870f7e567ffb43aee23a784581c6c07dbb`.
- Focused no-network verification: 9 publisher safety tests passed.
- Draft PR: <https://github.com/r3dbars/nightshift/pull/24>.
- GitHub independently reported `isDraft: true`, one commit, and one approved
  changed file.
- The rehearsal PR was then closed without merge and its remote branch was
  deleted.
- Original checkout remained unchanged apart from the active implementation
  branch.
- Publication worktree was removed.
- A replay of the same patch was rejected before a second PR or branch.
- No merge, deploy, release, credential, visibility, or billing action ran.

Proof artifacts:

```text
~/.codex/night-shift/live-publish-proof/proof-5/publish.json
~/.codex/night-shift/live-publish-proof/proof-5/publish-verification.txt
~/.codex/night-shift/live-publish-proof/replay-proof/publish.json
```

This proves real Docker-backed draft publication and replay suppression for one
harmless repository change. It does not yet prove varied useful PRs or an
unattended overnight publication.
