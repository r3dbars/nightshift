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
| One-command repeat use | 80 | A live blank-home setup was followed by a zero-question `--yes` repeat that reused the saved repo and defaults without changing config or creating a ledger. | Prove the native skill invocation starts a full healthy shift with zero repeat questions. |
| Installation | 76 | Linked and copied installs work on this Mac; copied installs now include the pinned runner context and package checks verify it. | Fresh-machine macOS and Linux install proof with automatic PATH handling. |
| First-run UX | 78 | A live blank-home interactive run from `/tmp` automatically selected an owned GitHub repo, showed the complete safe plan, and asked exactly one question: `Start Night Shift now?`; a real new-user comprehension study is still missing. | Observe brand-new users understanding and completing the one-consent flow without help. |
| Hardware detection | 70 | Ollama and configured Windows endpoints are detected and chat-probed. | Prove LM Studio, Ollama, offline fallback, LAN discovery, and reconnect behavior. |
| Minimal setup | 72 | Live interactive and `--yes` setup from an ordinary folder required no repo path, URL, model name, or GitHub selection; both chose mac-only, github-recent, Normal, and eight hours. | Repeat on fresh macOS/Linux users and prove clear recovery when no eligible repo or AI is available. |
| Useful output | 42 | Two bounded July 12 runs surfaced real missing tests that were independently verified and added; the latest produced 1 MAYBE and 0 rejects. The broad July 11 overnight baseline remains 0 of 40. | Varied healthy overnight runs produce independently verified useful outcomes without duplicate churn. |
| Task selection | 68 | A live July 12 rehearsal exposed feedback reordering evidence-backed work behind a broad mission; the repaired rerun dispatched the 800-point deterministic task first, skipped four weak signals, and avoided Python nested-helper false positives. | Demonstrate high accepted-outcome rates across varied live GitHub signals and repos. |
| Repository prioritization | 62 | Activity, PR, issue, and failed-run scores exist. | Measure that selected repos match user value and active work, not recency alone. |
| GitHub usefulness | 72 | PR, issue, failed-workflow, and recent-repo signals feed queues. | Correlate selected work to accepted PR/issue outcomes across owned repos. |
| Portfolio discovery | 82 | Live authenticated discovery selected `r3dbars/BetterFeedback`, cloned an owner-validated private cache, and rejected symlink, path-escape, foreign-owner, and mismatched-origin cases in tests. | Add user-controlled owner/repo priorities and quiet hours, then prove varied-account behavior. |
| Task specificity | 78 | Source evidence and exact paths are required; patching requires a reproduced failure. | Exercise it on varied real repositories. |
| Multi-repo operation | 72 | Portfolio cycles, stop limits, and a controller lock exist. | Test real mixed-language portfolio runs. |
| Mac compute | 82 | LM Studio detection, local lane work, and default routing for generic exploration. | Dynamic queueing and thermal/resource feedback. |
| Windows compute | 80 | LAN worker detection and routing reserved for pinned CI/PR signals. | Authenticated endpoint validation and reconnect tests. |
| Efficiency | 58 | The repaired bounded rehearsal skipped four weak signals and produced one schema-valid candidate in one local call and about 2,695 estimated tokens; independent review still rejected its usefulness, and the broad overnight baseline remains poor. | Prove strong tokens-per-accepted-outcome across full overnight runs with revision caching. |
| Evidence quality | 90 | Copy-ready deterministic coverage citations produced one validator-accepted candidate with exact source and zero-match evidence; proof artifacts and lifecycle transitions remain separate from verified truth. | Exercise reproduction evidence across varied real repositories. |
| Deterministic proof | 92 | A real rootless Podman rehearsal reproduced a failing Python test, applied one approved patch in an isolated tmpfs, passed the same check afterward, removed the worktree, and left the source repo clean. | Repeat across diverse repositories and prove provider restart recovery. |
| Patch autonomy | 72 | The real Podman rehearsal reached `PROVEN_REPAIR` with baseline 1, after 0, no guard reasons, and an immutable local runner; the patch-worker response was controlled test input. | Prove model-generated isolated patches across diverse repositories. |
| Draft PR creation | 10 | Overnight runs do not currently push branches or open code PRs. | One-time consent, isolated tested branches, real draft PR proof, never merge or deploy. |
| Brief safety | 92 | No host repo execution; restricted actions and redaction. | Continue adversarial prompt-injection testing. |
| Execute-draft safety | 94 | A real pinned runner proved read-only source mounts, no-network tmpfs patching, exact changed-path validation, clean source status, and disposable-worktree removal. | Repeat adversarial real-run proof across Docker and Podman before widening access. |
| Prompt and secret security | 88 | Redaction, protected paths, code-first context selection, and explicit untrusted-data boundaries. | Add a prompt-injection corpus and real-run measurements. |
| Morning UX | 65 | The brief leads with ranked items and now offers one bounded handoff command for the best survivor. | Validate morning comprehension and review effort across varied real overnight outcomes. |
| Cloud-agent handoff | 35 | A real morning item produced a redacted local pack; the real no-consent run was denied, while 70-test coverage proves read-only invocation and response validation. | Obtain explicit consent and prove a live Codex review, then repeat across varied items without privacy leaks. |
| Reliability | 82 | Stop deadlines, process cancellation, single-controller lock, migration tests, and validated task-state transitions. | Crash-recovery and concurrent-scheduler integration tests. |
| Observability | 92 | Ledgers, task attempts, cooldown skips, outcome metrics, health, and sandbox capability remain explicit; real runner stdout/stderr is now retained beside patch artifacts. | Confirm retention behavior in a real 10-hour soak. |
| Learning loop | 55 | Feedback now changes pre-model selection by repo and task family: positive votes prioritize, one negative downranks, and two negatives suppress Normal-mode work without bypassing grounding. No real user-feedback outcome lift is proven yet. | Demonstrate better accepted outcomes and lower wasted tokens across later real user-rated runs. |
| Test coverage | 93 | The full discovered suite has 136 tests plus a real Podman integration rehearsal covering provider build syntax, copied runner context, image-ID normalization, tmpfs compatibility, and sandbox diagnostics. | Interrupted-controller, scheduler, Docker-provider, and GitHub-write integration tests. |
| Maintainability | 60 | Evidence scoring, reporting, and selection policy now live in directly tested modules; the main controller fell from 4,465 to 4,413 lines but still owns queue construction and dispatch. | Continue splitting setup, scanning, queueing, dispatch, and lifecycle into tested modules. |
| Portability | 82 | The runner now builds on real ARM64 macOS Podman with provider-specific pull and tmpfs syntax; Docker behavior remains unit-tested only and Podman VM restart stability is unresolved. | Prove Docker and Linux hosts plus reliable provider restart behavior. |
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
