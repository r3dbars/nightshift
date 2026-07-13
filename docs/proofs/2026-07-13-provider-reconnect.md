# Provider Reconnect Proof

Date: 2026-07-13

## Live provider baseline

`night-shift doctor` completed GREEN on the user's Mac. It listed and
chat-probed LM Studio with `qwen/qwen3-coder-next`, then listed and chat-probed
the private-LAN Windows worker with `qwen3-coder:30b`.

## Reconnect exercise

A loopback HTTP fixture accepted a model-list request, dropped that first TCP
connection without a response, then returned an OpenAI-compatible model list
on the second request. `check_endpoint` returned:

```text
RECONNECT_PROOF state=GREEN calls=2 message=Reconnect fixture reachable; models=['coder']
```

The retry is limited to one attempt and only covers transient network errors.
Invalid JSON and other response errors are not retried. Focused tests cover
both paths, and `scripts/check-package.sh` remains the full promotion gate.

## Proof boundary

This proves live Mac and Windows provider health plus bounded reconnect logic.
It does not prove automatic LAN discovery, a provider process restart, or a
Swift-capable isolated runner.
