# Live Codex Morning Handoff Proof

Date: 2026-07-12

## Claim

A real Night Shift morning candidate can now be sent with one-time consent to
an independent Codex review in an ephemeral read-only workspace containing only
allowlisted committed files. Night Shift validates the returned verdict and
citations before accepting it.

## Authentic Candidate

The completed ledger
`night-shift-20260712T191935Z-quiet` contained one grounded MAYBE item claiming
that `validate_patch` lacked regression coverage for binary, added, and deleted
patches. It allowed only:

- `tests/test_night_shift.py`
- `bin/night_shift_patch_protocol.py`

The real command used one-time cloud consent:

```sh
night-shift handoff \
  --ledger ~/.codex/maestro/overnight/night-shift-20260712T191935Z-quiet \
  --item 1 --agent codex --run --allow-cloud --timeout 300
```

## Live Failures Found And Fixed

1. Current `codex exec` rejected the removed `--ask-for-approval` flag.
2. The isolated copied-file workspace required `--skip-git-repo-check`.
3. Codex returned valid citations in several standard Markdown/backtick styles
   that the handoff validator did not recognize.

The final invocation used `--ephemeral`, `--sandbox read-only`, an isolated
temporary directory, and `--skip-git-repo-check`. It did not use the source
checkout as the Codex working directory.

The citation parser now accepts:

- plain `path:line`;
- `[path:line](path:line)`;
- `[path](path:line)`;
- a relative visible label whose absolute temporary target ends in the exact
  same `path:line`;
- backticked `path:start-end` using the first line for existence validation.

Every extracted path must still be in the materialized allowlist and exist at
the reviewed revision. Arbitrary absolute citations are not accepted.

## Accepted Independent Result

Final terminal status:

```text
NIGHTSHIFT_HANDOFF: GREEN | independent read-only review complete
```

Codex returned `REJECTED` and `READY_FOR_IMPLEMENTATION: no`. It independently
found that the requested regression test already exists in
`tests/test_night_shift.py` and that the implementation rejects those patch
markers in `bin/night_shift_patch_protocol.py`. This prevented stale duplicate
work rather than manufacturing a coding task.

Night Shift recorded:

- cloud authorized: true;
- read only: true;
- return code: 0;
- valid review: true;
- validation reasons: none.

The review and metadata remain under the source ledger's `handoff/` directory.

## Morning Ergonomics

When a morning brief has a reviewable KEEP/MAYBE item, it now prints the exact
one-action read-only Codex command. The `--run --allow-cloud` text makes consent
visible in the command itself; no cloud review happens from merely reading the
brief or preparing a local handoff pack.

## Deterministic Gate

`scripts/check-package.sh` passed all 234 tests and package/install checks.
Coverage includes no-consent denial, allowlisted materialization, redaction,
read-only invocation, revision mismatch rejection, multiple citation styles,
line existence, and output-schema validation.

## Regrade

- Cloud-agent handoff: 35 to 55. One real bounded Codex review is now proven and
  useful, but varied-item repetition and privacy measurement are still needed.
- Morning UX: 72 to 76. A reviewable brief now provides the exact one-action
  command, but real user comprehension and review-effort studies are missing.
