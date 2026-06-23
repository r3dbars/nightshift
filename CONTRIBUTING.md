# Contributing

Night Shift should stay small, local-first, and honest about proof.

Before opening a PR:

1. Keep the change focused.
2. Do not add merge, release, publish, tag, deploy, appcast, cask, credential, or billing automation.
3. Keep local and Windows lane output framed as draft work until Codex or a human verifies it.
4. Run:

```bash
bash -n install.sh bin/maestro-smoke.sh bin/maestro-delegate bin/maestro-local bin/maestro-windows bin/maestro-claude
python3 -m py_compile bin/maestro-nightshift bin/maestro-token-report
python3 bin/maestro-nightshift --version
python3 bin/maestro-nightshift --help
```
