# Night Shift Progress Loop: 2026-07-13

This is a source-backed progress record for the 95/100 rebuild. It keeps live
run evidence separate from model claims and from human/manual proof.

## Merged Changes

- PR #108 merged portfolio priorities and quiet hours.
- PR #109 merged the clean temporary-home macOS install proof and Ubuntu/macOS
  package CI matrix.
- PR #110 merged the disposable 10-hour controller soak harness.
- PR #111 was generated from a verified Night Shift draft, reviewed by Codex,
  passed Ubuntu and macOS CI, and merged as `65513f6`. It added one focused
  behavioral test in `tests/test_night_shift_queue.py`.
- PR #112 merged disk-headroom and ledger-growth metrics for the soak.
- PR #113 merged clearer first-run permission copy and the updated wizard guide.
- PR #115 merged friendlier no-work morning language.
- PR #116 merged fail-closed first-run prompts, clear blank-project recovery,
  completed-brief selection, and evidence-rich portfolio choices.
- PR #117 merged fail-closed Mac/Windows worker transport handling and a
  loopback wrapper proof.
- PR #118 merged complete empty-run artifacts so no-compute and no-task runs
  retain harvest, queue, metrics, lifecycle, token, and morning files.
- The current hardware pass adds bounded, opt-in private-LAN discovery for
  Ollama and LM Studio, with explicit confirmation before saving a match.
- A second explicit goal on the current `main` produced a one-file
  `VERIFIED_DRAFT` for the missing `morning_status` regression test. Fresh
  publication verification opened PR #120, CI passed on Ubuntu and macOS, and
  the exact head merged into `main`.
- PR #154 merged the Swift-capable multi-architecture runner after both hosted
  Ubuntu and macOS package gates passed.
- PR #155 merged the friendlier rejected-suggestion explanation after hosted
  Ubuntu and macOS package gates passed.
- PR #156 merged guarded Swift/XCTest test selection after hosted Ubuntu and
  macOS package gates passed.
- PR #157 merged copy-ready useful/not-useful feedback commands and a
  repo-scoped learning snapshot into single-repo morning briefs.
- PR #158 made portfolio feedback commands safe to copy when ledger paths
  contain spaces and added a concrete not-useful note example.
- PR #159 added an optional local elapsed-time signal from viewed brief to
  feedback vote; hosted Ubuntu/macOS checks passed and the PR merged.
- PR #160 made direct `autopilot` inherit the saved plan and exposed its
  bounded draft controls; hosted Ubuntu/macOS checks passed and a real
  malformed worker patch was rejected in isolated execution. Proof:
  `docs/proofs/2026-07-13-direct-autopilot-draft-rejection.md`.
- PR #161 made isolated draft patch and evidence mounts portable on macOS;
  hosted Ubuntu/macOS checks passed and the deterministic real sandbox proof
  saw the candidate patch, reported the changed path, preserved the applied
  patch, and recorded verification rc 0. A model-driven saved-plan replay
  still rejected a citation-mismatched candidate safely. Proof:
  `docs/proofs/2026-07-13-sandbox-shared-artifacts.md`.
- A fresh two-lane analysis-only run against current `main` displayed the new
  feedback commands and repo-scoped learning snapshot in a real morning brief;
  it produced two honest `MAYBE` candidates and no source change. Proof:
  `docs/proofs/2026-07-13-feedback-brief-real-run.md`.

## Live Evidence

- The authenticated portfolio run visited three owned repos: BetterFeedback,
  Night Shift, and Transcripted. It completed three child batches with no
  duplicate ledger and honestly found no model-ready task in Normal mode.
  Parent ledger: `~/.codex/maestro/overnight/night-shift-20260713T161145Z-autopilot`.
- An explicit goal run produced one exact MAYBE with source/test evidence in
  3,204 estimated local tokens. Parent ledger:
  `~/.codex/maestro/overnight/night-shift-20260713T161529Z-autopilot`.
- The same candidate became `VERIFIED_DRAFT` after the full package gate in an
  isolated worktree, then passed fresh publication verification and opened
  draft PR #111 before merge. Publication proof:
  `~/.codex/maestro/overnight/night-shift-20260713T161529Z-autopilot/drafts/r3dbars--nightshift/manual-publish/publish.json`.
- A useful vote was recorded against the exact candidate. The feedback event
  includes its ledger, fingerprint, repo, source revision, family, and note.
- The short soak rehearsal completed with 18/18 killed controllers recovered,
  no active state remaining, and disk-headroom metrics. The full 10-hour soak
  is running separately; its final result is intentionally not claimed here.
- A disposable native `night-shift start --yes` run was started from a clean
  temporary home with an eight-hour stop. Its setup was saved, its controller
  is live, and its first completed portfolio brief is YELLOW with no unsafe
  task claimed. The run is still in progress and is not counted as complete
  repeat-use proof yet.
- The current package gate passes 396 tests, including the wrapper error proof,
  complete empty-run artifact regression, direct-test invocation scope, and
  runner routing regressions. The reporting tests cover the single-repo
  feedback commands and the quoted portfolio path.
- The current package gate now passes 397 tests, including invalid/future
  feedback-timestamp handling. A disposable CLI run recorded a `3.0` second
  feedback delay without touching the source repo. Proof:
  `docs/proofs/2026-07-13-feedback-timing.md`.
- The current package gate now passes 399 tests, including direct-autopilot
  saved-plan and visible safety-control coverage.
- The post-PR #161 real sandbox proof now passes with a temporary ledger path:
  the container reads a staged patch from the shared worktree root, writes
  changed-path, applied-patch, verification-output, and verification-rc
  evidence, and leaves the source checkout unchanged. A saved-plan model
  replay rejected a bad citation/patch and created no PR; that remains a
  safety result rather than an accepted outcome.
- The post-PR #162 read-only portfolio run visited BetterFeedback, Transcripted,
  and Night Shift in ranked order and showed a plain-language reason for each
  selection. No model tokens were spent because the evidence gate found no
  model-ready task. Proof: `docs/proofs/2026-07-13-portfolio-priority-brief.md`.
- PR #163 made the empty portfolio closeout say that Night Shift checked the
  repos and deliberately kept weak work off the user's review list, with one
  clear command to try again tonight. Hosted Ubuntu/macOS checks passed.
- The repeatable blank-home recovery proof now passes from a temporary HOME
  outside any Git repo with no GitHub credentials: it returns clear `--repo`,
  Git-repo, and `gh auth login` next steps, exits safely, and saves no config.
- The live LAN discovery proof found the real private Windows Ollama worker at
  `192.168.7.201:11434` and selected `qwen3-coder:30b-32k`; no repo context was
  sent. Proof: `docs/proofs/2026-07-13-lan-discovery.md`.
- The custom `CODEX_HOME` wrapper proof now passes when `HOME` points
  elsewhere. A fresh mixed-TypeScript BetterFeedback clone then completed
  three local calls and produced exact grounded candidates, but correctly
  rejected them because dependencies were not installed. Proof:
  `docs/proofs/2026-07-13-custom-codex-home.md`.
- The mixed-repo rehearsal also exposed and fixed a command-detector bug that
  invented `npm run test` when no such package script existed. BetterFeedback
  now receives the real `npm run test:unit:vitest` verification command, with a
  regression test in the package gate.
- The approval and scan paths now both surface that focused runner before
  umbrella, AI, e2e, or smoke scripts. This keeps the morning instruction and
  isolated preflight on the same command.
- PR #127 merged runner-native npm dependency preparation, automatic cache
  reuse, bounded local verification repair, and the BetterFeedback
  `VERIFIED_DRAFT` proof.
- PR #128 merged owner-profile command precedence, so a reviewed
  `.night-shift.json` package gate wins over filename heuristics during trust.
- PRs #129 and #130 merged explicit behavioral-test semantic contracts and
  draft routing. A malformed Python cleanup patch was rejected with the
  source checkout clean; this is recorded as a safety outcome, not a useful
  patch.
- PRs #133 through #139 merged bounded large-test evidence, safe generated-test
  imports, semantic proof wording, constructor guidance, bounded repair
  prompts, focused owner source excerpts, and local test-import recognition.
  The package gate passes 382 tests after these changes.
- A fresh install/trust/autopilot run on the current merged `main` produced a
  `VERIFIED_DRAFT` for an explicit `DraftEngine.cleanup` behavioral goal. The
  candidate passed the real package gate before and after the patch, passed the
  isolated sandbox gate with 383 tests, satisfied the semantic invocation
  contract, and removed its worktree. Proof:
  `docs/proofs/2026-07-13-explicit-goal-verified-draft.md`.
- PR #146 merged strict unified-diff hunk validation and a clearer repair
  prompt after a real malformed model patch was rejected safely. A fresh
  current-main explicit-goal run then produced a `VERIFIED_DRAFT` with the
  385-test package gate, isolated sandbox proof, semantic invocation proof,
  and worktree cleanup. Proof:
  `docs/proofs/2026-07-13-current-main-explicit-goal.md`.
- PR #148 merged automatic runner-native npm dependency preparation on macOS.
  A clean GitHub BetterFeedback clone passed `trust-repo --apply --yes`
  without the expert dependency flag; the Linux Colima preflight passed after
  the earlier host-native-binding failure was reproduced. Proof:
  `docs/proofs/2026-07-13-auto-native-dependencies.md`.
- The new provider-process fixture proof passed startup `GREEN`, stopped
  provider `YELLOW`, and same-port restart `GREEN`. It is package-gated and
  intentionally does not raise the hardware score because it is not a real
  LM Studio or Ollama restart.
- A fresh live Windows-lane run against the clean BetterFeedback clone used
  `qwen3-coder:30b` at `192.168.7.201:11434`, created a one-file behavioral
  test, passed the real `npm run test:unit:vitest` command before and after the
  patch, passed isolated sandbox verification, satisfied the invocation
  contract, and removed its temporary worktree. Proof:
  `docs/proofs/2026-07-13-windows-verified-draft.md`.
- The verified Windows draft then passed Night Shift's fresh publication
  verification and opened BetterFeedback draft PR #491 from the exact source
  SHA. GitHub kept it in draft state, but two Vercel status contexts were
  failing when captured, so it remains unmerged and does not count as a green
  hosted outcome. Proof:
  `docs/proofs/2026-07-13-windows-draft-pr.md`.
- A fresh Astro/Node portfolio run rejected a worker's false missing-export
  claim after the pinned source and `npm run check` disproved it. No patch or
  PR was created, and the morning brief now explains the rejection reason.
  Proof: `docs/proofs/2026-07-13-rejected-false-positive.md`.
- PR #151 now strips the exact bundled-worker `MAESTRO_PROOF` footer before
  validating a returned diff. PR #152 filters non-draftable side-effecting
  TypeScript test gaps before model calls. PR #153 safely materializes one
  bounded `it`/`test` block from a raw worker response when no unified diff is
  returned. The package gate passes 389 tests after these changes.

## Remaining Proof Gaps

- A real 10-hour soak must finish successfully before runtime scores move to
  95.
- Useful output, multi-repo operation, and draft-PR scores still need repeated
  accepted outcomes across varied healthy repositories.
- First-run and morning UX still need observation by a new user, not another
  automated script.
- The morning briefs now explain the feedback action directly, but no real
  comprehension or review-time measurement has been claimed.
- The new Night Shift proof raises task specificity and deterministic proof,
  but does not yet establish repeated accepted output or draft-PR volume.
- The current-main proof confirms the retry hardening works once, but it does
  not yet raise useful-output, multi-repo, or draft-PR scores because the
  morning item still needs human usefulness review.
- The Windows verified draft closes one real Windows execution path, but it
  does not by itself count as a user-accepted outcome or a published draft PR.
  Those scores remain held until the candidate is reviewed and the broader
  varied-repository evidence is complete.
- Draft PR #491 proves the GitHub publication path but has failing Vercel
  statuses, so the draft-PR and GitHub usefulness scores remain held for a
  passing hosted outcome and human review.
- A fresh isolated-home observation completed the normal first-run flow with
  one clear start question, a truthful no-work result, and no source changes.
  The immediate `--yes` repeat reused setup unchanged and asked no questions.
  Proof:
  `docs/proofs/2026-07-13-first-run-ux.md`.
- An empty temporary home also completed the copied install path: a clean shell
  resolved the installed command, a second install stayed idempotent, and the
  installed command completed setup with GitHub and Claude absent. Proof:
  `docs/proofs/2026-07-13-fresh-install.md`.
- The real LM Studio process was stopped and restarted on port 1234. Doctor
  reported local AI `YELLOW` with connection refused while it was down, then
  `GREEN` with chat recovery after restart; the Windows worker stayed healthy.
  The runner was also rebuilt from a pinned multi-architecture Swift image,
  and a real Draft Swift test subset passed 128/128 in the no-network
  sandbox. Proof:
  `docs/proofs/2026-07-13-real-provider-swift-runner.md`.
