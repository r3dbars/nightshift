# Night Shift Quality Scorecard

This scorecard keeps the rebuild honest. A number only moves when there is
repeatable code, test evidence, or an end-to-end run artifact behind it.

## Current Regrade: 2026-07-12

The target is **95/100 in every dimension at the same time**. Scores describe
proven user outcomes, not the amount of code present. The July 11 overnight
run remains the broad baseline: 4 repos, 69 batches, 40 attempted findings,
0 accepted findings, and about 181,159 estimated tokens. A July 12 bounded
rehearsal produced 1 evidence-backed candidate in 1 local call and 2,887
estimated tokens; independent review confirmed the missing direct contract
test and added it to the suite.

| Dimension | Score | Evidence | What reaches 95 |
| --- | ---: | --- | --- |
| Product idea | 95 | Idle local compute becomes a morning decision surface. | Preserve the promise while proving repeated value. |
| One-command repeat use | 72 | Saved setup can launch without questions. | Prove the native skill invocation starts a healthy shift with zero repeat questions. |
| Installation | 72 | Linked and copied installs work on this Mac. | Fresh-machine macOS and Linux install proof with automatic PATH handling. |
| First-run UX | 55 | Normal setup now auto-selects safe defaults and asks one start confirmation; advanced choices are optional. | Observe new users completing setup with at most one consent and no endpoint knowledge. |
| Hardware detection | 70 | Ollama and configured Windows endpoints are detected and chat-probed. | Prove LM Studio, Ollama, offline fallback, LAN discovery, and reconnect behavior. |
| Minimal setup | 50 | Normal setup hides modes, endpoints, privacy routing, and duration behind detected defaults. | Fresh-user proof with no manual URLs, model names, or GitHub repo selection. |
| Useful output | 42 | Two bounded July 12 runs surfaced real missing tests that were independently verified and added; the latest produced 1 MAYBE and 0 rejects. The broad July 11 overnight baseline remains 0 of 40. | Varied healthy overnight runs produce independently verified useful outcomes without duplicate churn. |
| Task selection | 55 | Deterministic readiness skipped six weak signals before the latest one-task run, which returned one grounded candidate and no rejects. | Demonstrate high accepted-outcome rates across varied live GitHub signals and repos. |
| Repository prioritization | 62 | Activity, PR, issue, and failed-run scores exist. | Measure that selected repos match user value and active work, not recency alone. |
| GitHub usefulness | 72 | PR, issue, failed-workflow, and recent-repo signals feed queues. | Correlate selected work to accepted PR/issue outcomes across owned repos. |
| Portfolio discovery | 74 | GitHub recent-repo ranking and cached checkouts work. | Owner allowlist and per-repo priority/quiet hours. |
| Task specificity | 78 | Source evidence and exact paths are required; patching requires a reproduced failure. | Exercise it on varied real repositories. |
| Multi-repo operation | 72 | Portfolio cycles, stop limits, and a controller lock exist. | Test real mixed-language portfolio runs. |
| Mac compute | 82 | LM Studio detection, local lane work, and default routing for generic exploration. | Dynamic queueing and thermal/resource feedback. |
| Windows compute | 80 | LAN worker detection and routing reserved for pinned CI/PR signals. | Authenticated endpoint validation and reconnect tests. |
| Efficiency | 55 | The latest bounded rehearsal skipped six weak signals and produced one grounded candidate in one local call and about 2,887 estimated tokens, down from 6,115 after removing an unnecessary retry. The broad overnight baseline remains poor. | Prove strong tokens-per-accepted-outcome across full overnight runs with revision caching. |
| Evidence quality | 90 | Copy-ready deterministic coverage citations produced one validator-accepted candidate with exact source and zero-match evidence; proof artifacts and lifecycle transitions remain separate from verified truth. | Exercise reproduction evidence across varied real repositories. |
| Deterministic proof | 84 | Explicit argv profiles and a rootless-container baseline/after verifier are implemented. | Install and prove the sandbox on a real supported host. |
| Patch autonomy | 58 | A bounded patch protocol exists, but the real host sandbox is not ready. | Prove isolated patches and checks across diverse repositories. |
| Draft PR creation | 10 | Overnight runs do not currently push branches or open code PRs. | One-time consent, isolated tested branches, real draft PR proof, never merge or deploy. |
| Brief safety | 92 | No host repo execution; restricted actions and redaction. | Continue adversarial prompt-injection testing. |
| Execute-draft safety | 92 | Fail-closed profile, pinned runner, owned trust, no-network temporary workspace, and independent verifier. | Prove the protocol on a real runner image before widening access. |
| Prompt and secret security | 88 | Redaction, protected paths, code-first context selection, and explicit untrusted-data boundaries. | Add a prompt-injection corpus and real-run measurements. |
| Morning UX | 65 | The brief leads with ranked items and now offers one bounded handoff command for the best survivor. | Validate morning comprehension and review effort across varied real overnight outcomes. |
| Cloud-agent handoff | 35 | A real morning item produced a redacted local pack; the real no-consent run was denied, while 70-test coverage proves read-only invocation and response validation. | Obtain explicit consent and prove a live Codex review, then repeat across varied items without privacy leaks. |
| Reliability | 82 | Stop deadlines, process cancellation, single-controller lock, migration tests, and validated task-state transitions. | Crash-recovery and concurrent-scheduler integration tests. |
| Observability | 91 | Ledgers, task attempts, cooldown skips, outcome metrics, health, review-preserving retention, and explicit sandbox-capability health. | Confirm retention behavior in a real 10-hour soak. |
| Learning loop | 55 | Feedback now changes pre-model selection by repo and task family: positive votes prioritize, one negative downranks, and two negatives suppress Normal-mode work without bypassing grounding. No real user-feedback outcome lift is proven yet. | Demonstrate better accepted outcomes and lower wasted tokens across later real user-rated runs. |
| Test coverage | 89 | 112 focused tests now include direct reporting-module coverage for status, metrics, lifecycle, dedupe, queues, and morning KEEP/MAYBE/fallback output; the package gate compiles every installed Python module. | Real provider, interrupted-controller, scheduler, and GitHub-write integration tests. |
| Maintainability | 58 | Evidence/scoring and reporting/ranking now live in directly tested dependency-injected modules; the main controller is still about 4,350 lines. | Continue splitting setup, scanning, queueing, dispatch, and lifecycle into tested modules. |
| Portability | 78 | Local-first defaults with Linux/macOS scheduling and Docker-rootless/Podman-rootless sandbox providers. | Prove both providers on real supported hosts. |
| Ten-hour readiness | 86 | Fixed stop limits, lock, cooldown, unattended pause, retention controls, and a per-revision rejection circuit breaker. | A clean 10-hour soak with resource and disk evidence. |
| Honesty about proof | 91 | Worker claims stay separate from deterministic and manual proof. | Preserve this distinction through real draft-PR and cloud-handoff flows. |

## Non-Negotiable Promotion Rules

1. A score never increases from a model claim alone.
2. A repo is analysis-only until its owner supplies a reviewed profile.
3. A task becomes patchable only after a sandboxed reproduction and immutable verification plan.
4. An overnight run never pushes, opens code PRs, merges, deploys, or releases.
5. Every score must reach 95 simultaneously; code paths, mocks, and model claims alone do not qualify.
6. Safety and privacy may not be weakened to improve usefulness or autonomy.
7. Hardware, LAN, GitHub writes, scheduling, recovery, and overnight usefulness require real integration proof.
