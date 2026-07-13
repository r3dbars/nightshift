# Night Shift Progress Loop: 2026-07-13

This is a source-backed progress record for the 95/100 rebuild. It keeps live
run evidence separate from model claims and from human/manual proof.

## Merged Changes

- PR #108 merged portfolio priorities and quiet hours.
- PR #109 merged the clean temporary-home macOS install proof and Ubuntu/macOS
  package CI matrix.
- PR #110 merged the disposable 10-hour controller soak harness.
- PR #111 was generated from a verified Night Shift draft, reviewed by Codex,
  passed Ubuntu and macOS CI, and merged as `65513f6`. It added one focused
  behavioral test in `tests/test_night_shift_queue.py`.
- PR #112 merged disk-headroom and ledger-growth metrics for the soak.
- PR #113 merged clearer first-run permission copy and the updated wizard guide.
- PR #115 merged friendlier no-work morning language.
- PR #116 merged fail-closed first-run prompts, clear blank-project recovery,
  completed-brief selection, and evidence-rich portfolio choices.
- PR #117 merged fail-closed Mac/Windows worker transport handling and a
  loopback wrapper proof.
- PR #118 merged complete empty-run artifacts so no-compute and no-task runs
  retain harvest, queue, metrics, lifecycle, token, and morning files.

## Live Evidence

- The authenticated portfolio run visited three owned repos: BetterFeedback,
  Night Shift, and Transcripted. It completed three child batches with no
  duplicate ledger and honestly found no model-ready task in Normal mode.
  Parent ledger: `~/.codex/maestro/overnight/night-shift-20260713T161145Z-autopilot`.
- An explicit goal run produced one exact MAYBE with source/test evidence in
  3,204 estimated local tokens. Parent ledger:
  `~/.codex/maestro/overnight/night-shift-20260713T161529Z-autopilot`.
- The same candidate became `VERIFIED_DRAFT` after the full package gate in an
  isolated worktree, then passed fresh publication verification and opened
  draft PR #111 before merge. Publication proof:
  `~/.codex/maestro/overnight/night-shift-20260713T161529Z-autopilot/drafts/r3dbars--nightshift/manual-publish/publish.json`.
- A useful vote was recorded against the exact candidate. The feedback event
  includes its ledger, fingerprint, repo, source revision, family, and note.
- The short soak rehearsal completed with 18/18 killed controllers recovered,
  no active state remaining, and disk-headroom metrics. The full 10-hour soak
  is running separately; its final result is intentionally not claimed here.
- A disposable native `night-shift start --yes` run was started from a clean
  temporary home with an eight-hour stop. Its setup was saved, its controller
  is live, and its first completed portfolio brief is YELLOW with no unsafe
  task claimed. The run is still in progress and is not counted as complete
  repeat-use proof yet.
- The current package gate passes 370 tests, including the wrapper error proof
  and the complete empty-run artifact regression.

## Remaining Proof Gaps

- A real 10-hour soak must finish successfully before runtime scores move to
  95.
- Useful output, multi-repo operation, and draft-PR scores still need repeated
  accepted outcomes across varied healthy repositories.
- First-run and morning UX still need observation by a new user, not another
  automated script.
