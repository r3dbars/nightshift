# Contributing

Night Shift should stay small, local-first, and honest about proof.

Before opening a PR:

1. Keep the change focused.
2. Do not add merge, release, publish, tag, deploy, appcast, cask, credential, or billing automation.
3. Keep local and Windows lane output framed as draft work until Codex or a human verifies it.
4. Update `CHANGELOG.md` for user-facing command, install, packaging, or safety changes.
5. Keep `VERSION`, `bin/maestro-nightshift`, and release/tag notes in sync when changing versions.
6. Run:

```bash
scripts/check-package.sh
```

Release tags should use `vMAJOR.MINOR.PATCH`, for example `v0.1.0`. Do not cut
or push release tags unless the maintainer explicitly approves that release.
