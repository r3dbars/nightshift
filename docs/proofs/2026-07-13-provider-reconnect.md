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

## Disposable process restart

`python3 scripts/prove-provider-process-restart.py` also passed:

```text
PROVIDER_RESTART_PROOF: GREEN | startup=GREEN offline=YELLOW restart=GREEN same-port=1
```

That proof starts and terminates a child HTTP provider, checks the offline
message, and restarts it on the same port. It verifies the restart state
machine without touching LM Studio or Ollama. The hardware score therefore
stays below 95 until a real provider process restart is observed.
