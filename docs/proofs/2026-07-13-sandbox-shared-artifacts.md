# Isolated Draft Evidence Bridge: 2026-07-13

## Change

PR #161 (`45a3e1b`) made isolated draft verification portable on macOS. Docker
cannot reliably read or write the temporary `/var/folders` paths used by a
temporary `CODEX_HOME`, even when the host process can. Night Shift now stages
the candidate patch and isolated runner output in a per-run directory under
the already shared `~/.codex/night-shift/worktrees` tree, copies the four
evidence files back into the normal ledger, and removes the shared staging
directories after each run.

The same change also validates saved `active_days` and `max_repos` after
argument defaults are resolved, so a saved-plan autopilot replay cannot compare
`None` with an integer.

## Deterministic Real Sandbox Proof

Source checkout: `/Users/redbars/code/night-shift`

The proof used the real pinned runner and a known patch with the harmless
`true` verification command. It reported:

```text
SANDBOX_RC=0
PATCH_INPUT_VISIBLE=True
changed-paths.txt=True
tests/test_night_shift.py
applied.patch=True
verification.rc=True
0
HOST_SOURCE_STATUS=M bin/night-shift
 M bin/night_shift_drafts.py
 M bin/night_shift_sandbox.py
 M tests/test_night_shift.py
```

The source checkout retained only the intended local worktree changes; the
container did not write to it. The package gate then passed **399 tests**.
Hosted Ubuntu and macOS package checks passed before PR #161 merged.

## Model-Driven Replay

A saved-settings `autopilot` launch omitted `--execute-drafts` and inherited
the saved draft consent as intended. The local model produced a grounded
candidate, but the run rejected it because its corrected evidence citation and
patch output did not satisfy the proof contract. No PR was created and the
temporary worktree was removed. This is a successful safety outcome, not a
useful patch outcome.

## Score Effect

This proof strengthens isolated evidence portability and saved-plan replay
reliability. It does not raise useful-output, draft-PR, or human morning-UX
scores: those still require independently accepted results and user review.
