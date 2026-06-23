# Contributing

Night Shift should stay small, local-first, and honest about proof.

Before opening a PR:

1. Keep the change focused.
2. Do not add merge, release, publish, tag, deploy, appcast, cask, credential, billing, or repository-visibility automation.
3. Keep `maestro-nightshift run` artifact-only. Code changes should happen only in a reviewed branch or worktree and land through a draft PR.
4. Keep local and Windows lane output framed as draft work until Codex or a human verifies it.
5. Do not make this repository public from a normal contribution. Old closed PR refs can expose old history; use a fresh clean repo or a GitHub-supported purge before any public launch.
6. Run:

```bash
bash -n install.sh bin/maestro-smoke.sh bin/maestro-delegate bin/maestro-local bin/maestro-windows bin/maestro-claude
python3 -m py_compile bin/maestro-nightshift bin/maestro-token-report
python3 bin/maestro-nightshift --version
python3 bin/maestro-nightshift --help
```
