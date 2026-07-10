# Night Shift Quality Scorecard

This scorecard keeps the rebuild honest. A number only moves when there is
repeatable code, test evidence, or an end-to-end run artifact behind it.

## Current Regrade: 2026-07-10

| Dimension | Score | Evidence | What reaches 90 |
| --- | ---: | --- | --- |
| Product idea | 92 | Idle local compute becomes a morning decision surface. | Keep real outcomes ahead of activity. |
| Useful output | 60 | Grounded briefs and queues exist; accepted outcomes are still sparse. | Track reviewed/accepted work across real repos. |
| Portfolio discovery | 74 | GitHub recent-repo ranking and cached checkouts work. | Owner allowlist and per-repo priority/quiet hours. |
| Task specificity | 78 | Source evidence and exact paths are required; patching requires a reproduced failure. | Exercise it on varied real repositories. |
| Multi-repo operation | 72 | Portfolio cycles, stop limits, and a controller lock exist. | Test real mixed-language portfolio runs. |
| Mac compute | 82 | LM Studio detection, local lane work, and default routing for generic exploration. | Dynamic queueing and thermal/resource feedback. |
| Windows compute | 80 | LAN worker detection and routing reserved for pinned CI/PR signals. | Authenticated endpoint validation and reconnect tests. |
| Efficiency | 76 | Durable cooldowns, code-first context selection, smaller Windows packs, and no expensive Windows retry loops. | Per-outcome budgets and context caching by revision. |
| Evidence quality | 88 | Numbered source/CI evidence, proof artifacts, and persistent lifecycle transitions exist. | Exercise reproduction evidence across varied real repositories. |
| Deterministic proof | 84 | Explicit argv profiles and a rootless-container baseline/after verifier are implemented. | Install and prove the sandbox on a real supported host. |
| Patch autonomy | 76 | A model may return only a validated diff; it is applied and verified in a no-network temporary container workspace. | Prove the protocol with a real runner image and diverse repositories. |
| Brief safety | 92 | No host repo execution; restricted actions and redaction. | Continue adversarial prompt-injection testing. |
| Execute-draft safety | 92 | Fail-closed profile, pinned runner, owned trust, no-network temporary workspace, and independent verifier. | Prove the protocol on a real runner image before widening access. |
| Prompt and secret security | 88 | Redaction, protected paths, code-first context selection, and explicit untrusted-data boundaries. | Add a prompt-injection corpus and real-run measurements. |
| GitHub usefulness | 72 | PR, issue, failed-workflow signals feed queues. | PR/issue outcome correlation and explicit repo ownership profiles. |
| Setup UX | 88 | Friendly wizard, legacy re-consent migration, sandbox status, and local-runner builder. | Complete a real first-run profile on this Mac. |
| Morning UX | 82 | Brief, queue, harvest, token report, metrics, and a factual fallback when model drafts fail. | Validate usefulness with real morning reviews. |
| Reliability | 82 | Stop deadlines, process cancellation, single-controller lock, migration tests, and validated task-state transitions. | Crash-recovery and concurrent-scheduler integration tests. |
| Observability | 90 | Ledgers, task attempts, cooldown skips, outcome metrics, health, and review-preserving retention controls. | Confirm retention behavior in a real 10-hour soak. |
| Learning loop | 72 | Local usefulness feedback and task lifecycle evidence are retained. | Tie feedback to task families and actual accepted patches. |
| Test coverage | 82 | 44 focused tests, including hostile command/profile cases and a full simulated patch chain. | Integration tests for Docker and interrupted autopilot runs. |
| Maintainability | 58 | Policy, sandbox, state, and redaction modules now isolate critical rules. | Split the remaining controller/work-queue monolith. |
| Portability | 78 | Local-first defaults with Linux/macOS scheduling and Docker-rootless/Podman-rootless sandbox providers. | Prove both providers on real supported hosts. |
| Ten-hour readiness | 78 | Fixed stop limits, lock, cooldown, and unattended pause. | A clean 10-hour soak with resource and disk evidence. |

## Non-Negotiable Promotion Rules

1. A score never increases from a model claim alone.
2. A repo is analysis-only until its owner supplies a reviewed profile.
3. A task becomes patchable only after a sandboxed reproduction and immutable verification plan.
4. An overnight run never pushes, opens code PRs, merges, deploys, or releases.
5. The 90 target means demonstrated behavior, not merely code paths that look plausible.
