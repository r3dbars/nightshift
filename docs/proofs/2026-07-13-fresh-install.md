# Fresh Install Proof: 2026-07-13

This proof starts with an empty temporary home and uses the normal copied
installation path.

## Install

- Home: `/tmp/night-shift-fresh-install-Tx5Bg5`
- Codex home: `/tmp/night-shift-fresh-install-Tx5Bg5/.codex`
- GitHub: not signed in
- Claude CLI: not installed
- Install mode: copied files, `--no-path`

The first install completed with `Night Shift 0.1.0` and printed the one
explicit PATH command plus the simple next command, `night-shift start`.

A clean shell with only the installed bin directory added to `PATH` resolved
the command and printed the version. Running the install command a second time
completed successfully without duplicate or conflicting files.

## First launch from the install

The installed command ran:

```text
night-shift start --repo /Users/redbars/code/night-shift --setup-only --reset
```

It detected local Mac AI, treated GitHub and Claude as optional, showed the
safe plan, saved setup, and returned `NIGHTSHIFT_START: GREEN | setup saved | no
run started`.

No source checkout files were changed by the install or setup run.

