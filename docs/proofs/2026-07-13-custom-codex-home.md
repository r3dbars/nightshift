# Custom CODEX_HOME Portability Proof

This proof covers a common fresh-install shape where `HOME` and Night Shift's
installed `CODEX_HOME` are different directories.

## Wrapper Path

The package-gated worker wrapper proof now installs Night Shift into a custom
Codex home while keeping `HOME` elsewhere. It runs `maestro-delegate local`
through the installed wrapper, confirms the malformed response is rejected,
and confirms the `MAESTRO_PROOF` directory is written under `CODEX_HOME`.

```text
WORKER_WRAPPER_ERROR_PROOF: GREEN | offline, malformed, and custom CODEX_HOME paths fail closed
```

## Fresh Mixed-Repo Rehearsal

A fresh temporary install ran against a clean clone of the private
`r3dbars/BetterFeedback` repository with `HOME=/tmp/...` and
`CODEX_HOME=/tmp/night-shift-betterfeedback-fixed`. The local Mac model made
three calls using about 9,951 estimated tokens and returned grounded TypeScript
test candidates for `formatPercent` and `getAnalyticsSourceData`, each with
exact source evidence, files, and a test command.

The run did not claim a patch: the clone had no installed Node dependencies,
so deterministic verification was unavailable and all three candidates stayed
REJECT. That is intentional fail-closed behavior, not a usefulness success.

Artifacts:

```text
/tmp/night-shift-betterfeedback-fixed/maestro/overnight/night-shift-20260713T173515Z-night-shift/morning.md
/tmp/night-shift-betterfeedback-fixed/maestro/overnight/night-shift-20260713T173515Z-night-shift/artifacts/
```
