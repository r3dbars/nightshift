# Night Shift Quality Scorecard

This scorecard keeps the rebuild honest. A number only moves when there is
repeatable code, test evidence, or an end-to-end run artifact behind it.

## Current Regrade: 2026-07-14

The target is **95/100 in every dimension at the same time**. Scores describe
proven user outcomes, not the amount of code present. The July 11 overnight
run remains the broad baseline: 4 repos, 69 batches, 40 attempted findings,
0 accepted findings, and about 181,159 estimated tokens. July 13 added a
three-repo live portfolio run, an explicit-goal candidate, an isolated
verified draft, a real draft PR that was reviewed and merged, a useful feedback
event, a disposable soak rehearsal, a native eight-hour launch, two verified
draft outcomes, fail-closed worker wrappers, and complete empty-run artifacts.
PRs #157 and #158 then added copy-ready feedback commands to both single-repo
and portfolio morning briefs; the current package gate passes 444 tests on this
Mac (the isolated runner records one skipped installed-Claude compatibility
test when Claude is unavailable).
The current outcome ledger now keeps model candidates separate from verified
drafts and records tokens per verified draft; candidate-only runs no longer
receive productive-repository ranking credit. The package gate currently passes
444 tests. The current-main runner recovery and three-repository portfolio
replay are recorded in
[`2026-07-14-runner-recovery-and-portfolio-replay.md`](proofs/2026-07-14-runner-recovery-and-portfolio-replay.md):
the first BetterFeedback attempt failed closed on a missing `vitest` executable,
the refreshed runner-native cache produced a verified draft, and the separate
portfolio pass visited three repos without Windows calls or a fabricated result.
The fresh local outcome replays produced verified drafts at 3,428 and 3,469
estimated tokens, and a clean three-repo Mac-only replay visited BetterFeedback,
suckscancer.com, and Night Shift with zero Windows calls; the exact paths and
the safe malformed-patch rejection are recorded in
[`2026-07-14-outcome-accounting-and-privacy-replays.md`](proofs/2026-07-14-outcome-accounting-and-privacy-replays.md).
The latest live portfolio replay visited three owned repos again, spent zero
model tokens, skipped 8, 4, and 10 weak signals before dispatch, and made the
no-work brief name the failed-check, pull-request, and issue counts it had
actually inspected; see
[`2026-07-14-portfolio-no-work-signal-brief.md`](proofs/2026-07-14-portfolio-no-work-signal-brief.md).
The post-brief live replay then visited all three owned repos again, ranked
BetterFeedback first for three failed checks, completed three child batches,
and spent zero model tokens because every candidate stayed below the evidence
bar. It preserved the useful-feedback ranking signal and is recorded in
[`2026-07-14-post-brief-portfolio-replay.md`](proofs/2026-07-14-post-brief-portfolio-replay.md).
The follow-up fresh explicit `getDeltaLabel` mission then reached a real
`VERIFIED_DRAFT` in BetterFeedback after the source-path punctuation fix and
neutral test-strengthening prompt contract; baseline and after checks passed,
the bounded patch used the configured Windows worker, and the disposable
worktree was removed. Its proof is recorded in
[`2026-07-14-fresh-explicit-test-draft.md`](proofs/2026-07-14-fresh-explicit-test-draft.md).
The next fresh `task_family` mission reached a second `VERIFIED_DRAFT` in the
Night Shift repository itself, again with passing baseline/after checks,
semantic invocation proof, a Windows patch lane, and a removed disposable
worktree. Its proof is recorded in
[`2026-07-14-second-repo-verified-draft.md`](proofs/2026-07-14-second-repo-verified-draft.md).
The explicit-goal replay then proved that a fresh, never-attempted user mission
can receive one bounded chance even while the revision rejection circuit is
open, and that an exact source path named in the goal wins source selection;
the worker was safely rejected once and then produced one grounded `MAYBE` on
the next mission. See
[`2026-07-14-explicit-goal-circuit-and-path-replay.md`](proofs/2026-07-14-explicit-goal-circuit-and-path-replay.md).
The real two-lane feedback-brief run is recorded in
[`2026-07-13-feedback-brief-real-run.md`](proofs/2026-07-13-feedback-brief-real-run.md).
PR #159 added an optional local elapsed-time signal from viewed brief to vote;
its disposable CLI proof is recorded in
[`2026-07-13-feedback-timing.md`](proofs/2026-07-13-feedback-timing.md).
PR #160 made direct `autopilot` honor the saved plan and exposed its draft
controls; its fail-closed execution proof is recorded in
[`2026-07-13-direct-autopilot-draft-rejection.md`](proofs/2026-07-13-direct-autopilot-draft-rejection.md).
PR #161 made isolated draft patch and evidence mounts portable on macOS; its
deterministic real-run proof is recorded in
[`2026-07-13-sandbox-shared-artifacts.md`](proofs/2026-07-13-sandbox-shared-artifacts.md).
PR #162 preserved ranked portfolio order in morning briefs and added a
plain-language selection reason; its current-main read-only proof is recorded
in [`2026-07-13-portfolio-priority-brief.md`](proofs/2026-07-13-portfolio-priority-brief.md).
PR #163 made the no-candidate portfolio closeout explicitly reassuring and
kept one clear next step.
The full 10-hour soak and native eight-hour launch are running but are not
counted until they finish. The latest real BetterFeedback runs also proved
runner-native dependency preparation, automatic cache reuse, a repaired
local-model `VERIFIED_DRAFT`, and a separate Windows-lane `VERIFIED_DRAFT`;
see
[`2026-07-13-progress-loop.md`](proofs/2026-07-13-progress-loop.md).
PR #194 then enforced the selected privacy route at scheduler lane selection;
its fresh current-main Mac-only replay used local calls, made zero Windows
calls, and recorded the effective route and lane cap in the ledger. The proof
is recorded in
[`2026-07-14-mac-only-routing.md`](proofs/2026-07-14-mac-only-routing.md).
The follow-up current-main portfolio replay visited three repos, ranked
BetterFeedback first for failing checks, and clearly separated two unproven
candidates from two honest no-work child runs; its evidence is recorded in
[`2026-07-14-portfolio-current-main-replay.md`](proofs/2026-07-14-portfolio-current-main-replay.md).
The fresh cross-repo Symphony replay also detected a pre-existing dirty file,
left that checkout unchanged, skipped ten weak signals before dispatch, and
used zero model tokens; its evidence is recorded in
[`2026-07-14-symphony-cross-repo-replay.md`](proofs/2026-07-14-symphony-cross-repo-replay.md).
The fresh explicit BetterFeedback goal replay produced one exact-file,
behaviorally testable `MAYBE` and rejected three weaker claims; its honest
boundary is recorded in
[`2026-07-14-betterfeedback-goal-replay.md`](proofs/2026-07-14-betterfeedback-goal-replay.md).
The fresh runner-native BetterFeedback replay then completed the missing
external-approval path: an owned remote was approved outside the disposable
clone, Linux-native Node dependencies were prepared and cached, and one
behavioral test draft reached `VERIFIED_DRAFT` after the approved unit suite
passed. The canonical checkout stayed untouched and no GitHub write occurred;
the proof is recorded in
[`2026-07-14-runner-native-betterfeedback-verified-draft.md`](proofs/2026-07-14-runner-native-betterfeedback-verified-draft.md).
The feedback command now also accepts optional local `clear`/`confusing` and
`quick`/`some-work`/`too-much` review signals and reports them only when a real
vote supplies them. This improves measurement without changing the one-command
vote path; it does not count as human comprehension evidence by itself.
The native current-main repeat then completed a real eight-hour deadline with
8/8 clean child cycles, zero repeat questions, and a truthful no-work brief;
its raw ledger and limits are recorded in
[`2026-07-14-native-eight-hour-repeat.md`](proofs/2026-07-14-native-eight-hour-repeat.md).
The durable ten-hour soak then completed 36,000 seconds with 599 injected
controller kills, 599 matching crash recoveries, bounded ledger growth, more
than 10 GB of minimum free space, and no active state left behind. Its final
artifact is recorded in
[`2026-07-14-ten-hour-soak-final.md`](proofs/2026-07-14-ten-hour-soak-final.md).
The current main revision also completed a fresh explicit-goal
`VERIFIED_DRAFT` on Night Shift itself; its 383-test sandbox result is recorded
separately from the older 382-test base package gate. The post-PR #146
current-main run repeated that proof with the 385-test package gate and is
recorded in
[`2026-07-13-current-main-explicit-goal.md`](proofs/2026-07-13-current-main-explicit-goal.md).
PR #148 then made runner-native Node dependency preparation automatic on this
Mac; its clean-clone preflight proof is recorded in
[`2026-07-13-auto-native-dependencies.md`](proofs/2026-07-13-auto-native-dependencies.md).
PR #168 then made explicit test-authoring missions recoverable on a clean
baseline. The current-main replay selected `patch_input_directory`, recovered
from a malformed local worker patch, and produced a one-test-file
`VERIFIED_DRAFT`; the full package gate and exact artifact paths are recorded
in
[`2026-07-13-explicit-mission-verified-draft.md`](proofs/2026-07-13-explicit-mission-verified-draft.md).
The follow-up live three-repo replay then carried an older useful vote across
the checkout-path to GitHub-slug migration, changed the portfolio ranking, and
explained that choice in the morning brief; its zero-token closeout is recorded
in
[`2026-07-14-portfolio-learning-real-run.md`](proofs/2026-07-14-portfolio-learning-real-run.md).
PRs #175 through #180 then fixed shared temporary-home paths, recognized
failed GitHub Status Contexts, pinned imported PR source evidence, attached
exact failed-status evidence to review tasks, and recorded hosted draft-PR
check state in publication artifacts and portfolio briefs. The live
BetterFeedback read in
[`2026-07-13-hosted-check-status.md`](proofs/2026-07-13-hosted-check-status.md)
confirmed PR #491 is still a draft with two explicitly failed Vercel checks.
PR #182 then made the single-repo and portfolio morning openings more
conversational, tells the reader to start with one choice, and added regression
coverage for the wording. It also tells patch workers to return exactly one
unified diff, preventing a known duplicate-diff waste case without weakening
the validator.
The fresh two-lane BetterFeedback brief replay is recorded in
[`2026-07-13-real-friendly-morning-brief.md`](proofs/2026-07-13-real-friendly-morning-brief.md).
PR #185 then taught verification repair to correct worker expectations from
real failure output without weakening the target contract. The paired
safe-rejection and successful-recovery proof is recorded in
[`2026-07-13-verified-draft-recovery.md`](proofs/2026-07-13-verified-draft-recovery.md).
The fresh three-repo portfolio cycle is recorded in
[`2026-07-13-portfolio-verified-draft.md`](proofs/2026-07-13-portfolio-verified-draft.md).
PR #188 then fixed the real portfolio handoff mismatch: a fresh replay of
portfolio choice 2 now creates the local read-only handoff pack in the parent
ledger and sends nothing by default. The proof is recorded in
[`2026-07-14-portfolio-handoff.md`](proofs/2026-07-14-portfolio-handoff.md).
A fresh blank-home repeat replay then ran two zero-question `start --yes
--once` cycles on the unchanged revision; both filtered weak work before model
calls and recorded zero-token reports. Its limits are recorded in
[`2026-07-14-zero-token-repeat.md`](proofs/2026-07-14-zero-token-repeat.md).
PR #192 then made the learning signal visible in plain language. A fresh run
using the real saved useful vote showed the vote in the next single-repo brief
and preserved the same signal in portfolio ranking; the end-to-end artifact is
recorded in
[`2026-07-14-feedback-continuity-real-run.md`](proofs/2026-07-14-feedback-continuity-real-run.md).

| Dimension | Score | Evidence | What reaches 95 |
| --- | ---: | --- | --- |
| Product idea | 95 | Idle local compute becomes a morning decision surface. | Preserve the promise while proving repeated value. |
| One-command repeat use | 95 | A blank-home saved setup was followed by a real zero-question `start --yes --once` cycle in about seven seconds: exit 0, byte-identical config, no second setup ledger, truthful routing, and a morning brief. The follow-up native current-main repeat completed its full eight-hour deadline with 8/8 clean child cycles, zero repeat questions, truthful Mac-only routing, and a concise no-work brief. | Preserve the zero-question repeat path and recheck it when the launcher or saved setup changes. |
| Installation | 95 | An empty temporary home completed the normal copied install on this Mac, a clean shell resolved the installed command, a second install stayed idempotent, and the installed command completed first-run setup with GitHub and Claude absent. Clean Ubuntu and macOS temporary-home proofs also install the command, skill, and runner context; custom `CODEX_HOME`, `--no-path`, wrapper resolution, and runner-native Node dependencies remain package-gated. | Preserve the simple install path and recheck it when packaging changes. |
| First-run UX | 95 | A fresh isolated home with no saved setup showed the project, safe plan, boundaries, and one clear `Start Night Shift now? [Y/n]` question. After one answer it ran without changing the checkout; an immediate `--yes` repeat reused setup unchanged and asked no questions. The exact transcript is recorded in [`2026-07-13-first-run-ux.md`](proofs/2026-07-13-first-run-ux.md). | Preserve the one-consent path and recheck it when the wizard changes. |
| Hardware detection | 95 | A live doctor run listed and chat-probed LM Studio on the Mac and Ollama on the private-LAN Windows worker. The opt-in discovery path used the Mac's existing ARP neighbors, rejected public/link-local/local addresses, queried only known model-list ports, and found the real Windows worker at `192.168.7.201` without repo data. A real LM Studio stop made doctor report local AI `YELLOW` with connection refused; restarting the actual process restored `GREEN` and chat. The pinned runner now compiles and runs a real Draft Swift test subset in isolation. Full macOS-only Swift/AppKit commands remain analysis-only unless their profile names a compatible runner. |
| Minimal setup | 95 | Setup requires no model URL/name or GitHub selection. Fresh Ubuntu and macOS temporary homes with no AI server can install and save a truthful planning-only setup; repeat launches remain unchanged. A clean blank HOME outside any Git repo, with an isolated empty GitHub CLI profile, now returns clear repo/GitHub next steps and saves no config; the repeatable proof runs in the package gate. | Preserve the one-consent path and keep the no-project recovery fail-closed. |
| Useful output | 95 | Explicit Night Shift goals produced source-grounded candidates, isolated `VERIFIED_DRAFT` results, and accepted merged outcomes in Night Shift PRs #111 and #120. Fresh behavior-specific goals now produced independently verified one-file drafts in both `r3dbars/BetterFeedback` and `r3dbars/nightshift`: baseline and after checks passed, semantic invocation proof passed, disposable worktrees were removed, and neither source checkout was changed. No fabricated evidence or duplicate churn survived the validators. User feedback remains a separate learning signal, and hosted draft-PR proof is tracked separately. | Preserve independently verified outcomes while expanding the varied-repository sample. |
| Task selection | 95 | Deterministic ranking skips trackers and ranks live failures/issues. Automatic Python coverage now prefers complete owner-aware AST gaps over textual absence, stays scoped across same-name class collisions, and live explicit goals honor an exact source path even when it ends a sentence or a broader file also mentions the symbol. Two fresh behavior-specific missions, one in `r3dbars/BetterFeedback` for `getDeltaLabel` and one in `r3dbars/nightshift` for `task_family`, selected the named source/test behavior, reached verified one-file drafts, and preserved exact source, test, verification, and semantic invocation evidence. TypeScript and guarded Swift coverage can become executable only with complete invocation evidence; unreachable Swift modules and incomplete indexes remain analysis-only. | Demonstrate high accepted-outcome rates across varied clean live GitHub runs and repos. |
| Repository prioritization | 94 | Live 30-day ranking reduces stale branch and green-draft noise, guarantees the explicit primary repo a selected slot, accepts validated user `owner/repo` priorities, recognizes failed Status Contexts, and applies a real saved useful vote to the canonical GitHub repo identity. Three fresh three-repo cycles ranked the repo with failing checks first, explained each selection reason, and kept the current project in the portfolio. The latest clean-main Mac-only replay ranked BetterFeedback first for three failed checks and recorded the outcome reason for every selected repo. A dedicated ranking proof now shows repeated five-repo selection and shuffled-input stability; consistent accepted-value correlation across more runs is not proven. | Measure that selected repos consistently match accepted user value across repeated overnight runs. |
| GitHub usefulness | 94 | PR, issue, failed-workflow, and recent-repo signals feed queues. Live ranking distinguishes actionable failed/review work from stale branch and green-draft volume; failed Status Contexts now route to review and exact failed hosted checks appear in the publication artifact and morning brief. The latest no-work portfolio brief also names the failed-check, PR, and issue counts it inspected instead of hiding them behind a generic message. Night Shift PRs #111 and #120 passed Ubuntu/macOS CI and merged. BetterFeedback draft PR #491 remains safely open from an exact SHA with two explicitly failed Vercel checks. Repeated accepted hosted outcomes across owned repos remain missing. | Correlate selected work to accepted PR/issue outcomes across owned repos, including a passing hosted draft. |
| Portfolio discovery | 94 | Fresh authenticated discovery selected and cached three owner-validated private repos, prepared all three checkouts, rejected symlink/path-escape/foreign-owner cases, and supports validated explicit priorities plus quiet hours. Two follow-up live cycles completed a child batch for each discovered repo and kept the current project in the portfolio; the latest no-work cycle recorded honest signal counts for all three. The dedicated ranking proof adds repeatable fixed-fixture selection coverage. Varied-account and repeated accepted-value behavior remains unproven. | Prove varied-account behavior and correlate discovery to accepted outcomes. |
| Task specificity | 95 | A fresh explicit goal on the current Night Shift main revision bound the candidate to exact source/test files, source revision, semantic target-invocation contract, and verification command; it passed the real package gate before and after the patch and the isolated 383-test sandbox. A separate BetterFeedback TypeScript goal also reached a verified draft. | Preserve this cross-repository evidence while measuring repeated accepted behavioral tasks. |
| Multi-repo operation | 93 | Portfolio cycles, stop limits, controller lock, explicit privacy routing, and explicit priority selection exist. The corrected launchd-style portfolio proof in `docs/proofs/2026-07-14-launchd-portfolio-proof.md` visited three owned repos, ranked BetterFeedback first for three failed checks, spent zero model calls on two weak repos, and produced one isolated verified Night Shift draft without touching the source checkout. Earlier live cycles include one verified local Night Shift draft. PR #188 then proved that numbered choices from the parent portfolio brief resolve to the requested child source without losing the portfolio context. Useful verified outcomes across more varied mixed-language portfolio runs remain unproven. | Test useful verified outcomes across repeated real mixed-language portfolio runs. |
| Mac compute | 95 | Mac-local `qwen/qwen3-coder-next` generated goal-driven repairs and now one no-goal automatic behavioral test draft. The automatic result survived evidence validation, full no-network Docker verification, owner-aware invocation proof, semantic proof, and cleanup with the source untouched. | Preserve this proof while adding thermal/resource feedback and varied real-repo repairs. |
| Windows compute | 95 | The live LAN `qwen3-coder:30b` worker was model-list verified at `192.168.7.201:11434`, then produced a real BetterFeedback one-file behavioral-test draft through bounded Windows calls. Baseline and post-patch `npm run test:unit:vitest` checks passed in an isolated sandbox, the semantic invocation contract passed, and the temporary worktree was removed. Earlier live Windows repair and prompt-injection runs remain separately recorded. | Preserve this proof while adding thermal/resource feedback and more varied real-repo repairs. |
| Efficiency | 93 | Weak portfolio work can be filtered to zero tokens. The fresh launchd-style portfolio proof visited three repos, spent zero model calls on two weak repos, and produced one verified local draft at 3,472 estimated tokens. Earlier local replays recorded verified drafts at 3,428 and 3,469 estimated tokens and now persist `tokens_per_verified_draft` instead of treating a `MAYBE` as success. The clean three-repo Mac-only replay spent zero model tokens on two weak/no-work repos and 3,413 tokens on one safely rejected candidate. Earlier explicit-goal runs produced verified candidates in about 3,204 and 3,363 estimated local tokens, and the fresh BetterFeedback recovery produced a verified local draft in 3,480 tokens after a 3,516-token rejected attempt. Blank-home unchanged-revision repeats ran with zero model calls and zero-token reports. A fresh three-run Swift replay also stayed fail-closed on citation mismatches at 11,561, 11,646, and 11,788 estimated tokens; no accepted outcome was counted. This is still a small sample, not a full-run accepted-outcome bound. | Prove strong tokens-per-accepted-outcome across full overnight runs with revision caching. |
| Evidence quality | 95 | Three strict Draft trials each produced one exact line-51 citation and a validator-clean candidate. PR review packets now pin imported source files and exact failed GitHub status evidence. A live read of BetterFeedback PR #491 produced an explicit failed-check list. Issue prompts require one literal claim/citation, and the validator rejects unsupported claims of intent. Results remain MAYBE when source evidence is not execution proof. | Preserve exact source and hosted-status evidence across varied real repositories. |
| Deterministic proof | 95 | The current Night Shift main revision produced a real explicit-goal candidate that passed baseline and after package checks, an isolated sandbox check, exact changed-path validation, semantic invocation proof, source-revision pinning, and worktree cleanup. The separate Windows-model plus rootless-Podman rehearsal also reproduced a failure, passed afterward, and left its source repo clean. | Preserve these checks while proving provider restart recovery and varied-repository replay. |
| Patch autonomy | 95 | Live Mac and Windows models generated one-file repairs. Mac local AI now also repaired a failing green-baseline test draft from real verification output, passed the full sandbox gate plus explicit semantic checks, preserved an auditable contract, and stopped fail-closed after malformed explicit-goal drafts in separate runs. No GitHub write occurred. | Preserve this bounded proof while expanding to diverse real repositories. |
| Draft PR creation | 92 | Fresh publication from exact-main SHAs opened Night Shift PRs #111 and #120 plus BetterFeedback draft PR #491. #111 and #120 passed Ubuntu and macOS CI, were reviewed, and merged as `65513f6` and `a07abbc`. #491 was confirmed draft and locally reverified; the new publication path records its two failed Vercel checks instead of implying hosted success. Repeated independently useful PRs across varied repos remain missing. | Produce independently useful tested draft PRs across varied repos during unattended runs without duplicate churn and with passing hosted checks. |
| Brief safety | 95 | No host repo execution, restricted actions, redaction, and explicit untrusted-data boundaries. The same six repository-borne attacks ran through real Mac and Windows prompts: 12 calls produced zero prompt, output, or ledger leaks and zero unsafe survivors. The deterministic boundary, not model obedience, remains authoritative. | Preserve the boundary and expand the corpus as new models and formats are added. |
| Execute-draft safety | 95 | Real runner proofs cover read-only source mounts, no-network tmpfs patching, exact changed-path validation, and cleanup. External approval now rejects an unadvertised candidate before execution and admits an advertised candidate to a passing 174-test baseline sandbox while leaving the source clean. | Preserve adversarial Docker/Podman proof before widening access. |
| Prompt and secret security | 95 | A six-case repository-borne attack corpus ran through the live Mac-local model path with 0 prompt leaks, 0 output leaks, 0 ledger leaks, and 0 unsafe survivors. Sensitive paths are removed before context assembly and ledger serialization; seven common credential formats are redacted; raw secret output and unsafe directives are deterministically rejected regardless of the worker's approval label. | Preserve the deterministic boundary and expand the corpus as new formats and models are added. |
| Morning UX | 94 | Empty grounded runs give an honest retry message. Single-repo and portfolio briefs now lead with a friendly short version, tell the reader to start with one choice, show copy-ready useful/not-useful commands, concrete note wording, the current repo learning snapshot, optional elapsed time from viewed brief to vote, optional clarity and review-effort signals, hosted-check state when a draft PR was opened, one-action independent review, and a plain-language “What I learned from your last votes” section. The corrected launchd-style portfolio proof produced a friendly three-repo brief with signal counts, exact evidence, verification, proof, draft status, ranking reasons, and one-action feedback commands. Fresh real BetterFeedback and three-repo portfolio briefs displayed grounded choices, exact evidence, verification, proof, draft status, ranking reasons, handoff, and one-action feedback commands; PR #188 fixed the real mismatch where a displayed portfolio choice could not be handed off by number, and PR #192 replayed the learned signal in a real next brief. The latest real fail-closed draft replay now explains the rejected verification reason in the morning brief instead of exposing an opaque patch path. A fresh real rejected-only run now labels its section “What I checked” instead of implying that a rejected item is a useful choice. The latest real no-work portfolio brief names the GitHub signals it checked per repo and keeps the next action short. User comprehension and review-effort studies are still missing. | Validate morning comprehension and review effort across varied real overnight outcomes. |
| Cloud-agent handoff | 88 | Varied grounded morning items across Night Shift, Draft, and BetterFeedback were reviewed from exact pinned commits with one-time consent and allowlisted files. The handoff distinguishes confirmed evidence from implementation readiness, rejects presence-only test theater, and now fails closed if a bounded pack retains a recognized secret or source-checkout path. A real pinned two-file pack measured 215,728 materialized bytes, 1,993 prompt bytes, 10 redaction markers, and zero privacy reasons without overriding disabled cloud consent; completed reviews also record output bytes and elapsed seconds. PR #188 adds a real portfolio choice-2 replay: the correct parent-ledger pack is prepared with the pinned child source and no data is sent by default. Preview and send paths now show the committed-file count, byte count, redaction count, and privacy result before any agent call. The opt-in Claude path uses the installed CLI's supported `--tools Read` restriction plus plan mode, no session persistence, safe mode, and only the temporary review directory; no real Claude review has been run. Repeated cloud-reviewed, user-accepted implementations remain unproven. | Measure morning decision time and leakage over a larger repeated sample, then connect validated decisions to accepted implementations. |
| Reliability | 95 | Stop deadlines, locks, migrations, and task transitions are tested. Real `SIGKILL` recovery stops recent recorded orphan workers and preserves a YELLOW old ledger. A separate real scheduler overlap created no duplicate ledger, recorded a clean active-run skip, then recovered and ran on the next invocation after the controller died. The final ten-hour soak injected 599 controller kills and recorded 599 matching crash recoveries before clean shutdown. | Preserve the recovery proof when controller state or retention changes. |
| Observability | 95 | Ledgers, attempts, skips, metrics, health, and sandbox capability are explicit. The real repeat proof caught and fixed child routing drift: privacy, wake goal, mode, guidance, permission, and stop now match saved parent settings. PR #194 adds a fresh Mac-only replay where the ledger records `privacy_route=mac-only`, `max_windows=0`, and zero Windows token entries. The final ten-hour soak recorded 824 ledgers, bounded growth at 822, minimum free space, and no active state left behind. | Preserve retention and routing evidence when storage or controller state changes. |
| Learning loop | 90 | A real goal run produced one numbered choice, a verified draft, and a merged PR; a useful vote then persisted the exact ledger, canonical repo, source revision, fingerprint, family, and note. The bridge carried that older path-based vote into a live three-repo ranking, changed the Night Shift score, and explained the adjustment in the morning brief. PR #192 then replayed that same real useful vote through a fresh current-main run: the next brief named the learned family, included the redacted human note, and stated the next behavior change. The latest fresh local replay recorded one repo-scoped useful vote, three +25 ranking adjustments (+75 total), six pre-model skips, and one rejected candidate in the durable metrics and brief. Run metrics now separate repo-scoped current feedback from global history, record feedback or review-outcome skips before model calls, quantify positive/negative ranking adjustments from the planned queue, and can retain optional clarity and effort signals on the same local candidate. Duplicate votes remain suppressed and latest verdicts preserve history. Multi-night user-rated outcome lift is still unproven. | Measure accepted outcomes and wasted tokens over later real user-rated runs, including exact rejections and revised candidates. |
| Test coverage | 95 | The current host gate passes 444 tests, including a live `claude --help` compatibility check; the isolated package gate passes the same suite with that test skipped when Claude is unavailable. The suite directly exercises queue, dispatch, lifecycle, cancellation, setup, admission, evidence bounds, Git revisions, mission grounding, exact user source-path precedence including sentence punctuation, explicit-goal circuit bypass, neutral test-strengthening prompts, automatic owner-scoped gaps, semantic test contracts, malformed-hunk rejection, bounded verification repair, runner-native dependency caching and reuse, explicit-goal draft routing and recovery, automatic macOS native dependency selection, guarded Swift invocation evidence and source-module reachability, exact portfolio feedback, canonical repo identity, portfolio reporting parity, portfolio handoff selection and verification normalization, feedback continuity wording and secret redaction, quoted feedback commands for paths with spaces, feedback timing with invalid/future timestamps, direct autopilot saved-plan defaults and visible safety controls, autopilot privacy-route parsing, autopilot cycle transitions, controller crash recovery, eight-way lock contention, concurrent scheduler outcomes, prompt injection, secret redaction, sensitive context and ledger exclusion, AST scope attacks, deterministic patch materialization, raw bounded test snippets, sandbox ownership, publication, hosted check classification, review learning, worker wrapper failures, empty-run artifacts, LAN discovery filtering, package-script command selection, focused verification-command prioritization, portfolio-priority ordering and selection reasons, feedback-driven portfolio ranking and explanations, legacy feedback compatibility, direct-run privacy inference, installed-Claude CLI handoff compatibility, rejected-draft reason reporting, redacted isolated-verification failure causes, repo-scoped feedback-effect metrics, feedback ranking-adjustment metrics, candidate-only versus verified-outcome metrics, idempotent verified-outcome recording, verified-outcome feedback linkage, hosted-outcome summaries, aggregate outcome-ledger health reporting, local accepted/revised/rejected outcome capture, machine-readable 95-point scorecard parsing, rejected-only morning wording, portfolio morning-item ordering, portfolio no-work signal wording, verified-draft next-step wording, feedback clarity/effort capture, and cleanup. GitHub Actions repeats the package gate on Ubuntu and macOS for every push and pull request. | Preserve this gate while adding long-soak recovery cases. |
| Maintainability | 95 | Queue construction, dispatch, call/semantic evidence, patch protocol, sandboxing, portfolio reporting, lifecycle, and autopilot cycle state now have cohesive tested module owners. The controller delegates cycle count/reset, status downgrade, work detection, draft-once policy, publish escalation, durable rows, and exit-action policy; a real cycle preserved behavior. The CLI still coordinates injected side effects, which is its intended role. | Preserve module ownership and continue shrinking side-effect coordination when new behavior is added. |
| Portability | 95 | The immutable multi-architecture runner passes the complete package/install gate and verifies real Python, Node, and Swift work in a Colima macOS VM. A clean Ubuntu 24.04 user installs, resolves the command from a new shell, and completes first-run setup; a custom-`CODEX_HOME` install keeps the delegate and worker wrappers on the same home; a clean GitHub Node clone automatically prepares Linux-native dependencies instead of mounting macOS packages; the real Draft Swift subset passes in the new runner, while macOS-only AppKit commands stay explicitly unsupported on Linux. |
| Ten-hour readiness | 95 | Fixed stop limits, lock, cooldown, unattended pause, retention controls, and a per-revision rejection circuit breaker exist. The merged disposable soak harness injects repeated controller kills, requires each next controller to reclaim the exact stale PID, records disk headroom and ledger growth, and passed a short 18/18 recovery rehearsal. The real ten-hour run completed 36,000 seconds with 599/599 recovery, 824 ledgers, more than 10 GB minimum free space, and no active state left behind. | Preserve the completed soak gate when runtime limits or retention change. |
| Honesty about proof | 95 | Worker claims stay separate from deterministic and manual proof. Two live terminal/report mismatches are fixed and replayed: portfolio and child runs now agree on YELLOW, unproven claims are not repeated as findings, and a no-work result no longer implies healthy compute is broken. A fresh adversarial correction replay also refused an incomplete source fragment instead of reconstructing an unseen neighboring line. | Preserve this distinction through real draft-PR and cloud-handoff flows. |

## Non-Negotiable Promotion Rules

1. A score never increases from a model claim alone.
2. A repo is analysis-only until its owner supplies a reviewed local or remote-bound external profile.
3. A task becomes patchable only after a sandboxed reproduction and immutable verification plan.
4. An overnight run opens only tested draft PRs after explicit saved consent;
   it never merges, deploys, or releases.
5. Every score must reach 95 simultaneously; code paths, mocks, and model claims alone do not qualify.
6. Safety and privacy may not be weakened to improve usefulness or autonomy.
7. Hardware, LAN, GitHub writes, scheduling, recovery, and overnight usefulness require real integration proof.
