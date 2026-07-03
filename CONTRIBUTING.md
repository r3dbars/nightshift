# Contributing

Night Shift should stay small, local-first, and honest about proof.

Before opening a PR:

1. Keep the change focused.
2. Do not add merge, release, publish, tag, deploy, appcast, cask, credential, billing, or repository-visibility automation.
3. Keep `night-shift run` artifact-only. Code changes should happen only in a reviewed branch or worktree and land through a draft PR.
4. Keep local and Windows lane output framed as draft work until Codex or a human verifies it.
5. Never change any repository's visibility from a Night Shift workflow or a normal contribution. Taking a repo public is a manual, deliberate act: old closed PR refs can expose old history, so use a fresh clean repo or a GitHub-supported purge first.
6. Update `CHANGELOG.md` for user-facing command, install, packaging, or safety changes.
7. Keep `VERSION`, `bin/night-shift`, and release/tag notes in sync when changing versions.
8. Run:

```bash
scripts/check-package.sh
```

Release tags should use `vMAJOR.MINOR.PATCH`, for example `v0.1.0`. Do not cut
or push release tags unless the maintainer explicitly approves that release.
