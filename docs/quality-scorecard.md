# Night Shift Quality Scorecard

This scorecard keeps the rebuild honest. A number only moves when there is
repeatable code, test evidence, or an end-to-end run artifact behind it.

## Current Regrade: 2026-07-10

| Dimension | Score | Evidence | What reaches 90 |
| --- | ---: | --- | --- |
| Product idea | 92 | Idle local compute becomes a morning decision surface. | Keep real outcomes ahead of activity. |
| Useful output | 60 | Grounded briefs and queues exist; accepted outcomes are still sparse. | Track reviewed/accepted work across real repos. |
| Portfolio discovery | 74 | GitHub recent-repo ranking and cached checkouts work. | Owner allowlist and per-repo priority/quiet hours. |
| Task specificity | 65 | Source evidence and exact paths are required. | Reproduce failures before escalating to a patch task. |
| Multi-repo operation | 72 | Portfolio cycles, stop limits, and a controller lock exist. | Test real mixed-language portfolio runs. |
| Mac compute | 72 | LM Studio detection and local lane work. | Dynamic queueing and thermal/resource feedback. |
| Windows compute | 72 | LAN worker detection and lane routing. | Authenticated endpoint validation and reconnect tests. |
| Efficiency | 68 | Durable reject cooldowns and dedupe prevent known loops. | Token budgets per outcome and context caching by revision. |
| Evidence quality | 84 | Numbered source/CI evidence and proof artifacts exist. | Independent reproduction evidence for every patch candidate. |
| Deterministic proof | 78 | Explicit argv profiles and a rootless-container gate are implemented. | Install and prove the sandbox on a real supported host. |
| Patch autonomy | 45 | Writable patch workers are deliberately disabled. | Isolated writable container protocol plus independent verifier. |
| Brief safety | 92 | No host repo execution; restricted actions and redaction. | Continue adversarial prompt-injection testing. |
| Execute-draft safety | 90 | Fail-closed profile, owned trust, rootless Docker, read-only/no-network baseline. | Keep the writable protocol at this bar before enabling it. |
| Prompt and secret security | 85 | Redaction before ledgers/model evidence and protected paths. | Structured secret scanning and a prompt-injection corpus. |
| GitHub usefulness | 72 | PR, issue, failed-workflow signals feed queues. | PR/issue outcome correlation and explicit repo ownership profiles. |
| Setup UX | 84 | Friendly wizard and legacy re-consent migration. | Explain profile setup from a single command. |
| Morning UX | 72 | Brief, queue, harvest, token report, and metrics files. | One concise outcome dashboard with feedback prompts. |
| Reliability | 78 | Stop deadlines, process cancellation, single-controller lock, and migration tests. | Crash-recovery and concurrent-scheduler integration tests. |
| Observability | 86 | Ledgers, task attempts, cooldown skips, and outcome metrics. | Disk quota/retention and a compact health command. |
| Learning loop | 68 | Local usefulness feedback changes rankings. | Tie feedback to task families and actual accepted patches. |
| Test coverage | 78 | 40 focused tests, including hostile command/profile cases. | Integration tests for Docker and interrupted autopilot runs. |
| Maintainability | 58 | Policy, sandbox, state, and redaction modules now isolate critical rules. | Split the remaining controller/work-queue monolith. |
| Portability | 70 | Local-first defaults with Linux/macOS scheduling paths. | Document/test rootless Docker on macOS, Linux, and Windows worker hosts. |
| Ten-hour readiness | 78 | Fixed stop limits, lock, cooldown, and unattended pause. | A clean 10-hour soak with resource and disk evidence. |

## Non-Negotiable Promotion Rules

1. A score never increases from a model claim alone.
2. A repo is analysis-only until its owner supplies a reviewed profile.
3. A task becomes patchable only after a sandboxed reproduction and immutable verification plan.
4. An overnight run never pushes, opens code PRs, merges, deploys, or releases.
5. The 90 target means demonstrated behavior, not merely code paths that look plausible.
