# Launchd portfolio proof

Date: 2026-07-14

## What changed

PR #231 merged as `49a2588`. Generated macOS launchd jobs now preserve
`CODEX_HOME` and include the Codex bin plus common Homebrew and user tool
locations in `PATH`.

The earlier temporary launchd run started with launchd's default
`/usr/bin:/bin:/usr/sbin:/sbin` path. Its parent ledger
`/Users/redbars/.codex/maestro/overnight/night-shift-20260714T170810Z-autopilot`
visited only `r3dbars/nightshift`, even though the command requested
`--scope github-recent --max-repos 3`.

## Corrected run

The next real launchd submission supplied the same environment that the new
plist generates. Parent ledger:

`/Users/redbars/.codex/maestro/overnight/night-shift-20260714T171835Z-autopilot`

It visited three owner-validated repositories in ranked order:

- `r3dbars/BetterFeedback`: 3 failed checks, 3 PRs, and 1 issue; no safe task
  was grounded, so no model call was spent.
- `r3dbars/suckscancer.com`: 1 failed check; no safe task was grounded, so no
  model call was spent.
- `r3dbars/nightshift`: one verified local draft, 3,472 estimated tokens,
  sandbox verification `rc=0`, and the disposable worktree removed.

The draft cited `bin/night_shift_drafts.py:389`, passed the repository-approved
package verification, and left `/Users/redbars/code/night-shift` clean. No
GitHub write, cloud transfer, merge, release, or deployment occurred.

## What this proves

- A launchd-style environment can discover GitHub-owned portfolio repos when
  the generated tool path is present.
- Weak repos are skipped before model calls when their evidence is not specific
  enough.
- A multi-repo run can still produce an isolated, verified local draft while
  preserving the source checkout boundary.

## What remains unproven

This is one corrected portfolio run. It does not prove independently accepted
user value, repeated multi-night outcome lift, a hosted green draft PR, or a
cloud-agent review. Those scores remain below 95 until the required real
consent and outcome evidence exists.
