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
| Task specificity | 84 | A live Windows repair was constrained to one exact source file, one reproduced assertion, one approved argv command, and one expected result. | Exercise it on varied real repositories. |
| Multi-repo operation | 72 | Portfolio cycles, stop limits, and a controller lock exist. | Test real mixed-language portfolio runs. |
| Mac compute | 92 | Mac-local `qwen/qwen3-coder-next` generated a real one-file repair through the local lane; rootless Podman promoted it to `PROVEN_REPAIR` with the source untouched. | Dynamic queueing, thermal/resource feedback, and varied real-repo repairs. |
| Windows compute | 90 | The live LAN `qwen3-coder:30b` worker produced a one-file repair through two bounded calls; real Podman verification promoted it to `PROVEN_REPAIR`. | Authenticated endpoint validation, reconnect tests, and varied real-repo repairs. |
| Efficiency | 65 | Both live Mac and Windows repairs used about 440 worker tokens each across one draft and one format correction to reach deterministic acceptance; broad overnight efficiency remains poor. | Prove strong tokens-per-accepted-outcome across full overnight runs with revision caching. |
| Evidence quality | 90 | Copy-ready deterministic coverage citations produced one validator-accepted candidate with exact source and zero-match evidence; proof artifacts and lifecycle transitions remain separate from verified truth. | Exercise reproduction evidence across varied real repositories. |
| Deterministic proof | 94 | A real Windows-model plus rootless-Podman rehearsal reproduced a failure, applied one approved patch in tmpfs, passed afterward, removed the worktree, and left the source repo clean. | Repeat across diverse repositories and prove provider restart recovery. |
| Patch autonomy | 92 | Live Mac and Windows models each generated a one-file repair; strict bounded correction plus Podman promoted both only after failing-before/passing-after proof. | Prove model-generated isolated patches across diverse real repositories. |
| Draft PR creation | 78 | Real Docker-backed publication opened draft PR #24 from an exact-main SHA after 9 focused safety tests; GitHub confirmed draft status and one approved file, the worktree was removed, replay was rejected, and nothing merged or deployed. This was a harmless rehearsal, not useful project work. | Produce independently useful tested draft PRs across varied repos during unattended runs without duplicate churn. |
| Brief safety | 92 | No host repo execution; restricted actions and redaction. | Continue adversarial prompt-injection testing. |
| Execute-draft safety | 94 | A real pinned runner proved read-only source mounts, no-network tmpfs patching, exact changed-path validation, clean source status, and disposable-worktree removal. | Repeat adversarial real-run proof across Docker and Podman before widening access. |
| Prompt and secret security | 88 | Redaction, protected paths, code-first context selection, and explicit untrusted-data boundaries. | Add a prompt-injection corpus and real-run measurements. |
| Morning UX | 65 | The brief leads with ranked items and now offers one bounded handoff command for the best survivor. | Validate morning comprehension and review effort across varied real overnight outcomes. |
| Cloud-agent handoff | 35 | A real morning item produced a redacted local pack; the real no-consent run was denied, while 70-test coverage proves read-only invocation and response validation. | Obtain explicit consent and prove a live Codex review, then repeat across varied items without privacy leaks. |
| Reliability | 82 | Stop deadlines, process cancellation, single-controller lock, migration tests, and validated task-state transitions. | Crash-recovery and concurrent-scheduler integration tests. |
| Observability | 92 | Ledgers, task attempts, cooldown skips, outcome metrics, health, and sandbox capability remain explicit; real runner stdout/stderr is now retained beside patch artifacts. | Confirm retention behavior in a real 10-hour soak. |
| Learning loop | 55 | Feedback now changes pre-model selection by repo and task family: positive votes prioritize, one negative downranks, and two negatives suppress Normal-mode work without bypassing grounding. No real user-feedback outcome lift is proven yet. | Demonstrate better accepted outcomes and lower wasted tokens across later real user-rated runs. |
| Test coverage | 95 | All 157 tests and package/install checks pass on the host and in the real no-network Docker VM; the focused publisher suite also passed before draft PR #24. Coverage includes named/default Colima binding, patch lanes, GitHub publication ambiguity, cleanup, and morning escalation. | Preserve this gate while adding interrupted-controller and scheduler integration cases. |
| Maintainability | 62 | Patch publication is isolated in a directly tested module; evidence scoring, reporting, and selection policy are also separated. The main controller still owns setup, queue construction, and dispatch. | Continue splitting setup, scanning, queueing, dispatch, and lifecycle into tested modules. |
| Portability | 92 | The immutable runner now passes the complete package/install gate and verifies a real draft through Docker in a Colima macOS VM; prior ARM64 Podman proof remains valid, while current Podman restart behavior is unstable. | Prove Linux installation and provider restart/recovery across fresh machines. |
| Ten-hour readiness | 86 | Fixed stop limits, lock, cooldown, unattended pause, retention controls, and a per-revision rejection circuit breaker. | A clean 10-hour soak with resource and disk evidence. |
| Honesty about proof | 91 | Worker claims stay separate from deterministic and manual proof. | Preserve this distinction through real draft-PR and cloud-handoff flows. |

## Non-Negotiable Promotion Rules

1. A score never increases from a model claim alone.
2. A repo is analysis-only until its owner supplies a reviewed profile.
3. A task becomes patchable only after a sandboxed reproduction and immutable verification plan.
4. An overnight run opens only tested draft PRs after explicit saved consent;
   it never merges, deploys, or releases.
5. Every score must reach 95 simultaneously; code paths, mocks, and model claims alone do not qualify.
6. Safety and privacy may not be weakened to improve usefulness or autonomy.
7. Hardware, LAN, GitHub writes, scheduling, recovery, and overnight usefulness require real integration proof.
