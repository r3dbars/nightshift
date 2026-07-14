# Claude Handoff CLI Compatibility Proof

Date: 2026-07-14

## Finding

The installed Claude Code CLI reports version `2.1.201`. Its help output accepts
`--allowed-tools <tools...>` and does not list the older `--tools` option.

Night Shift's bounded handoff command builder had been emitting `--tools Read`.
The existing test only inspected that constructed list, so it could pass while
the real installed CLI rejected the command before a review started.

## Fix

Claude handoffs now emit:

```text
claude -p --permission-mode plan --allowed-tools Read \
  --no-session-persistence --safe-mode --add-dir <temporary-review-dir> <prompt>
```

The handoff remains opt-in, read-only, sessionless, safe-mode, and scoped to the
temporary materialized review directory. No cloud review was sent during this
compatibility check.

## Verification

The regression test now requires `--allowed-tools Read` and rejects `--tools`.
The full host and isolated package gate passes 416 tests.
