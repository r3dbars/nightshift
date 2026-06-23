# Package Notes

Night Shift is currently a small private package, not a public open-source
project. Keep the install and release surface boring and explicit.

## Installed Layout

`./install.sh` installs into `${CODEX_HOME:-$HOME/.codex}` by default:

```text
bin/maestro-nightshift
bin/maestro-delegate
bin/maestro-local
bin/maestro-windows
bin/maestro-claude
bin/maestro-smoke.sh
bin/maestro-token-report
skills/maestro-overnight/
```

Use `./install.sh --codex-home PATH` to install into another Codex home.

## Command Names

The user-facing command is `maestro-nightshift`.

Helper commands keep the `maestro-` prefix because they are lane wrappers used
by the CLI and by Codex coordinator prompts:

- `maestro-delegate`
- `maestro-local`
- `maestro-windows`
- `maestro-claude`
- `maestro-smoke.sh`
- `maestro-token-report`

Do not introduce a second public command name unless the old one remains as a
documented compatibility alias.

## Versioning

- Current version lives in `VERSION` and `bin/maestro-nightshift`.
- Tags should be `vMAJOR.MINOR.PATCH`.
- Pre-1.0 changes may break command flags or ledger formats, but the changelog
  should say so plainly.
- Do not cut or push tags without explicit maintainer approval.

## Release Checklist

Before a private release tag:

1. Update `VERSION`.
2. Update `VERSION` inside `bin/maestro-nightshift`.
3. Update `CHANGELOG.md`.
4. Run `scripts/check-package.sh`.
5. Run `./install.sh --codex-home "$(mktemp -d)"`.
6. From that temporary install, run `maestro-nightshift --version` and
   `maestro-nightshift --help`.
7. Confirm `LICENSE` still matches the intended distribution status.

## Skill Bundle

The bundled skill is installed at:

```text
${CODEX_HOME:-$HOME/.codex}/skills/maestro-overnight/
```

Keep the root README, skill README, and `skills/maestro-overnight/SKILL.md`
aligned on the core command promise:

```bash
maestro-nightshift doctor --repo /path/to/project
maestro-nightshift run --repo /path/to/project --mode night-shift
maestro-nightshift report --latest
```
