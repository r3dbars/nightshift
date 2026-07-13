# Real Provider And Swift Runner Proof: 2026-07-13

This closes two previously explicit proof gaps without weakening the sandbox.

## Real LM Studio restart

The user's actual LM Studio server was stopped with `lms server stop`. While it
was stopped, the real command:

```text
night-shift doctor --repo /Users/redbars/code/night-shift \
  --local-url http://127.0.0.1:1234/v1 \
  --local-model qwen/qwen3-coder-next
```

reported `NIGHTSHIFT_DOCTOR: YELLOW` and:

```text
YELLOW local-models LM Studio not reachable: connection refused
GREEN windows-worker Windows worker reachable
```

LM Studio was then restarted with `lms server start --port 1234`. The same
doctor command returned `NIGHTSHIFT_DOCTOR: GREEN`, with both `local-models`
and `local-chat` green. The Windows worker stayed reachable throughout the
recovery proof.

## Swift-capable isolated runner

The runner now uses the pinned multi-architecture Swift image
`sha256:dd349c6dfc3cd3040910a84ab3e5bd5d08efdd547e5fb9f77b765abed16fe5ff`
and carries the existing Node 22 toolchain plus Python, `gh`, and `rsync`.
The resulting local runner image is
`sha256:c5735f545d157bb17c3fa82c1fb7a21e5c0fe997644f84f3b44046de3c2298c9`.

An isolated, no-network container run against a fresh shallow clone of the
real `r3dbars/Draft` repository:

- passed `Tests/check-teardown-safety.sh`;
- compiled the repository's Linux-compatible Swift test subset with `swiftc`;
- ran 128 real tests with 128 passing and 0 failing;
- kept the source checkout read-only and wrote only to disposable tmpfs.

The repository's full `run-tests.sh` intentionally includes AppKit and
`DateComponentsFormatter`, which are macOS-only APIs and cannot be claimed as
Linux proof. Night Shift therefore keeps that command analysis-only unless the
repo supplies a compatible runner profile.

