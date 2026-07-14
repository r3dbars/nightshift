# Claude Handoff CLI Compatibility Proof

Date: 2026-07-14

## Finding

The installed Claude Code CLI reports version `2.1.201`. Its help output
supports `--tools <tools...>`, which is the option that restricts the available
tool set for a session.

The compatibility test now checks the installed help output rather than only
checking our own constructed command list.

## Fix

Claude handoffs now emit:

```text
claude -p --permission-mode plan --tools Read \
  --no-session-persistence --safe-mode --add-dir <temporary-review-dir> <prompt>
```

The handoff remains opt-in, read-only, sessionless, safe-mode, and scoped to the
temporary materialized review directory. No cloud review was sent during this
compatibility check.

## Verification

The regression test now requires `--tools Read` and verifies that the installed
CLI advertises the same restriction flag.
The host gate passes 417 tests, including the live help check. The isolated
package gate passes 416 runnable tests and skips the compatibility check when
Claude is not installed in the runner.
