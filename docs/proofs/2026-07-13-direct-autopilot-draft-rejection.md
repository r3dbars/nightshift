# Direct Autopilot Draft-Rejection Proof

This proof checks that direct `autopilot` honors saved isolated-draft consent
while still rejecting an unsafe or malformed worker result.

## Run

- Source revision: `53c16c1`
- Disposable `CODEX_HOME`: `/var/folders/89/3nbfpj616353kk0f99t9vg3c0000gn/T/tmp.8SvlwxAioU`
- Saved preferences: `permission=draft-local`, `execute_drafts=true`,
  `allow_draft_prs=false`
- Command: one `autopilot --once` cycle with a precise `DraftEngine.cleanup`
  behavioral-test goal; no `--execute-drafts` flag was passed
- Local calls: 1, about 3,305 estimated tokens
- Result: isolated draft execution started, then `REJECT`

## Safety result

The local worker returned a malformed patch. The isolated runner failed closed
(`git apply` could not apply the candidate), recorded the rejection and
cleanup, and opened no PR. The original Night Shift checkout remained clean.
Windows was not called because the one-task budget was consumed by the local
candidate. This is execution-safety and saved-plan evidence, not a useful
accepted-outcome claim.
