# Portfolio Morning Handoff Proof

Date: 2026-07-14

## Change

PR #188 (`c622d25bc6a27ecbdc017058ad66d0fed6f89c79`) fixes the portfolio
morning handoff path. A portfolio ledger's numbered choices now resolve from
`morning-items.json`, while the selected child ledger supplies the real repo
and pinned source revision. The local handoff pack remains in the parent
portfolio ledger, where the morning brief tells the user to find it.

Portfolio verification fields are normalized at the handoff boundary, so the
portfolio's `verification` field is checked by the same validator used for a
single-repo queue.

## Reproduction

The real portfolio ledger was:

`/Users/redbars/.codex/night-shift/portfolio-retry.20260713/maestro/overnight/night-shift-20260714T012137Z-autopilot`

Before PR #188, this exact command failed because the controller fell through
to the latest child queue and reported that item 2 did not exist:

```text
NIGHTSHIFT_HANDOFF: RED | item 2 does not exist
```

After the merge, the same local-only command succeeded:

```text
NIGHTSHIFT_HANDOFF: GREEN | prepared item=2 | agent=codex | prompt=/Users/redbars/.codex/night-shift/portfolio-retry.20260713/maestro/overnight/night-shift-20260714T012137Z-autopilot/handoff/item-2-codex-prompt.md
Nothing was sent. Add --run after reviewing the local handoff pack.
```

The pack was created in the parent portfolio ledger, selected the requested
second item, preserved its exact source revision, and did not invoke a cloud
agent. The package gate passed 409 tests locally; GitHub Actions passed on both
Ubuntu and macOS for the pull request.

## Result

- Portfolio item numbers now mean the same thing in the morning brief and the handoff command.
- The parent ledger has one obvious place for the user's review pack.
- Cloud use remains opt-in and explicit with `--run --allow-cloud`.
- No merge, deploy, release, credential, or original-checkout write was performed by the handoff command.

