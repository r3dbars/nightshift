# Fresh Linux install proof

Date: 2026-07-13

Command:

```bash
scripts/prove-linux-install.sh
```

Environment:

- Clean `ubuntu:24.04` container, pulled by digest
  `sha256:4fbb8e6a8395de5a7550b33509421a2bafbc0aab6c06ba2cef9ebffbc7092d90`.
- Fresh unprivileged user named `newcomer` with an empty home directory.
- Only the documented install dependencies were installed.
- No GitHub CLI, local model server, Windows worker, or Claude CLI was present.
- The Night Shift source was mounted read-only.

Observed result:

1. `install.sh` copied the command, skill, and immutable runner context under
   `/home/newcomer/.codex`.
2. The installer added one exact PATH line to `.bashrc`.
3. A brand-new interactive Bash shell resolved
   `/home/newcomer/.codex/bin/night-shift` and printed `Night Shift 0.1.0`.
4. The new user created a clean one-file Git repository.
5. `night-shift start --yes --setup-only --skip-smoke` completed with
   `NIGHTSHIFT_START: GREEN` and saved the config outside the repo.
6. With no AI available, the preview truthfully selected planning-only mode and
   retained the eight-hour stop, read-only checkout, and no-push guarantees.

The package gate separately verifies that installing twice does not duplicate
the PATH line and that `--no-path` leaves the shell profile untouched. This is
real Ubuntu integration proof, not fresh-machine macOS proof or observed human
comprehension proof.
