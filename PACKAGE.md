# Package Notes

Night Shift is a small open-source package under the MIT license. Keep the
install and release surface boring and explicit.

## Installed Layout

`./install.sh` installs into `${CODEX_HOME:-$HOME/.codex}` by default:

```text
bin/night-shift
bin/maestro-delegate
bin/maestro-local
bin/maestro-windows
bin/maestro-claude
bin/maestro-smoke.sh
bin/maestro-token-report
skills/night-shift/
```

Use `./install.sh --codex-home PATH` to install into another Codex home.

## Command Names

The user-facing command is `night-shift`.

Helper commands keep the `maestro-` prefix because they are lane wrappers used
by the CLI and by Codex coordinator prompts:

- `maestro-delegate`
- `maestro-local`
- `maestro-windows`
- `maestro-claude`
- `maestro-smoke.sh`
- `maestro-token-report`

Do not introduce a second public command name. Keep the beginner path to one
command: `night-shift`.

## Versioning

- Current version lives in `VERSION` and `bin/night-shift`.
- Tags should be `vMAJOR.MINOR.PATCH`.
- Pre-1.0 changes may break command flags or ledger formats, but the changelog
  should say so plainly.
- Do not cut or push tags without explicit maintainer approval.

## Release Checklist

Before a release tag:

1. Update `VERSION`.
2. Update `VERSION` inside `bin/night-shift`.
3. Update `CHANGELOG.md`.
4. Run `scripts/check-package.sh`.
5. Run `./install.sh --codex-home "$(mktemp -d)"`.
6. From that temporary install, run `night-shift --version` and
   `night-shift --help`.
7. Confirm `LICENSE` is still the MIT license and the copyright year is right.

## Skill Bundle

The bundled skill is installed at:

```text
${CODEX_HOME:-$HOME/.codex}/skills/night-shift/
```

Keep the root README, skill README, and `skills/night-shift/SKILL.md`
aligned on the core command promise:

```bash
night-shift start
night-shift report --latest
```
