# Night Shift Test Matrix (Sanitized)

Run date: 2026-06-23
Source thread: `019e83db-1422-7f22-a28e-262717058e45`
Artifact root: shared Night Shift result root `20260623T170159` (local paths intentionally omitted).

## Summary

- Lanes expected: 10
- Lanes with artifacts found: 10
- Lane results: PASS=2, FAIL=4, YELLOW=4, PENDING=0
- Tests expected: 100
- Test results: PASS=68, FAIL=10, YELLOW=16, PENDING=6
- No merge or release was performed.

## Current Autonomy Addendum

Newer runs should also verify:

- `repo-scan.md` and `repo-scan.json` are created for `plan` and `run`.
- `planned-work-queue.json` contains repo-specific tasks before worker calls.
- `work-queue.md` and `work-queue.json` dedupe repeated worker ideas after
  scoring.
- `morning.md` shows top unique choices with action type, support count, and
  lane evidence.
- `--permission brief`, `--permission draft-local`, and `--permission draft-prs`
  change worker prompt autonomy without allowing push, merge, release, or deploy.
- Tiny repos with fewer than 10 commits still get a recent-file scan through the
  `git log --name-only` fallback.

## Evidence Inspection

- Initial polls at 17:03:24, 17:03:44, and 17:04:05 CDT found no files.
- A follow-up verification pass found the lane artifacts and this tracker was rewritten from the actual evidence.
- Evidence command: `find <run-root> -maxdepth 3 -type f` plus direct reads of lane summaries, TSVs, and logs.

## Lane Overview

| Lane | Area | Result | Test Counts | Primary Artifact | Main Finding |
|---|---|---:|---|---|---|
| 01 | Package, Install, and Doctor Smoke | YELLOW | PASS=7 FAIL=0 YELLOW=3 PENDING=0 | `artifacts/` | No confirmed code bug from lane summary; no explicit lane summary was provided. |
| 02 | CLI UX and Bad-Argument Behavior | YELLOW | PASS=8 FAIL=2 YELLOW=0 PENDING=0 | `lane-02-cli-ux.md and outputs/` | Invalid --mode for plan/run exits correctly but hint incorrectly suggests doctor instead of the active subcommand. |
| 03 | Plan/Run Ledger Behavior | PASS | PASS=10 FAIL=0 YELLOW=0 PENDING=0 | `lane-03-tests.tsv and lane-03-work/` | No confirmed bug from lane evidence. |
| 04 | Mac Local Model Lane | FAIL | PASS=9 FAIL=1 YELLOW=0 PENDING=0 | `lane-04-local-model.md and lane-04-proof/` | Local classification output was HOLD_DFS, which failed the strict allowed-label schema. |
| 05 | Windows Worker Lane | FAIL | PASS=9 FAIL=1 YELLOW=0 PENDING=0 | `lane-05-windows-worker.md` | Timeout behavior test crashed while importing bin/night-shift through importlib; dataclass module registration produced AttributeError. |
| 06 | Report and Stop Flows | PASS | PASS=10 FAIL=0 YELLOW=0 PENDING=0 | `lane-06-report-stop.md and lane-06-logs/` | No confirmed bug from lane evidence. |
| 07 | Safety and Public Readiness Scan | YELLOW | PASS=8 FAIL=0 YELLOW=2 PENDING=0 | `lane-07-safety-public.md` | Public launch hold: private/source-available license placeholder, owner naming, and old closed PR/ref/cache exposure need resolution. |
| 08 | Installed Skill and Repo Skill Sync | FAIL | PASS=1 FAIL=5 YELLOW=4 PENDING=0 | `lane-08-skill-install.md` | Installed skill and installed command are stale compared with repo source of truth; bare night-shift is not on PATH in this shell. |
| 09 | Toy Repo Quiet Lifecycle | YELLOW | PASS=1 FAIL=0 YELLOW=3 PENDING=6 | `lane-09-*.log and tmp-toy/` | Only four lane logs were present, so six expected tests are missing/pending. |
| 10 | README / Examples Command Smoke | FAIL | PASS=5 FAIL=1 YELLOW=4 PENDING=0 | `lane-10-command-logs/` | Example harvest sed commands fail because harvest.md and token-report.txt are missing after a zero-worker quiet run. |

## Detailed Matrix

### Lane 01: Package, Install, and Doctor Smoke

Lane status: `YELLOW`
Output artifact path: `artifacts/`
Bugs found:
- No confirmed code bug from lane summary; no explicit lane summary was provided.
- Doctor reports YELLOW when Windows is unconfigured; acceptable for Mac-only but needs clear expectation.
Improvement ideas:
- Add a lane-01 summary file with expected outcomes for negative-path checks.
- Separate expected RED negative tests from actual product failures.

| # | Test | Command / Run Evidence Summary | Status | Output Artifact Path | Bugs Found | Improvement Ideas |
|---:|---|---|---:|---|---|---|
| 1 | package check | scripts/check-package.sh -> package checks passed; rc=0 | PASS | `artifacts/test01-package-check.out` | none confirmed | Keep package check as release gate. |
| 2 | clone repo | git clone completed; cloned HEAD 4db07cc; rc=0 | PASS | `artifacts/test02-clone.out` | none confirmed | Record source remote and commit in lane summary. |
| 3 | install help | ./install.sh --help printed install locations/options; rc=0 | PASS | `artifacts/test03-install-help.out` | none confirmed | Good setup copy coverage. |
| 4 | temp install | ./install.sh --codex-home temp installed bin and skill files; rc=0 | PASS | `artifacts/test04-install-temp.out` | none confirmed | Keep temp install isolated. |
| 5 | installed command | installed command --version and --help succeeded; rc_version=0 rc_help=0 | PASS | `artifacts/test05-installed-command.out` | none confirmed | Good post-install smoke. |
| 6 | install --doctor | install then doctor returned NIGHTSHIFT_DOCTOR: YELLOW because Windows worker was not configured; rc=0 | YELLOW | `artifacts/test06-install-doctor.out` | Optional Windows path can make first-run doctor look partly blocked. | Clarify Mac-only success vs optional Windows warning. |
| 7 | doctor current repo | doctor returned YELLOW with local models/repo green and Windows unconfigured; rc=0 | YELLOW | `artifacts/test07-doctor-current.out` | Doctor status is conservative when optional Windows is absent. | Add expected status docs for Mac-only installs. |
| 8 | doctor missing repo | missing repo returned NIGHTSHIFT_DOCTOR: RED; rc=1 | PASS | `artifacts/test08-doctor-missing-repo.out` | none confirmed | Good negative-path behavior. |
| 9 | doctor missing install | empty CODEX_HOME reported missing tools as RED; rc=1 | PASS | `artifacts/test09-doctor-missing-install.out` | none confirmed | Good install remediation hints. |
| 10 | missing rsync | install dependency failure reported missing required command: rsync; rc=1 | YELLOW | `artifacts/test10-missing-rsync.out` | No lane summary says whether this was expected or product failure. | Have lane mark dependency-failure tests as expected PASS or product FAIL. |

### Lane 02: CLI UX and Bad-Argument Behavior

Lane status: `YELLOW`
Output artifact path: `lane-02-cli-ux.md and outputs/`
Bugs found:
- Invalid --mode for plan/run exits correctly but hint incorrectly suggests doctor instead of the active subcommand.
Improvement ideas:
- Make friendly_hint() choose by subcommand before generic --repo handling.

| # | Test | Command / Run Evidence Summary | Status | Output Artifact Path | Bugs Found | Improvement Ideas |
|---:|---|---|---:|---|---|---|
| 1 | --help | python3 bin/night-shift --help exit 0 | PASS | `outputs/t01_help.*` | none confirmed | Keep common flow visible. |
| 2 | --version | --version prints night-shift 0.1.0 exit 0 | PASS | `outputs/t02_version.*` | none confirmed | Good version smoke. |
| 3 | plan missing repo | plan without --repo exits 2 with plan --repo hint | PASS | `outputs/t03_missing_required_repo.*` | none confirmed | Good targeted hint. |
| 4 | plan invalid mode | plan --mode chaos exits 2 but hint says doctor | FAIL | `outputs/t04_invalid_plan_mode.*` | Wrong friendly hint for plan invalid mode. | Use plan-specific hint. |
| 5 | run invalid mode | run --mode chaos exits 2 but hint says doctor | FAIL | `outputs/t05_invalid_run_mode.*` | Wrong friendly hint for run invalid mode. | Use run-specific hint. |
| 6 | report missing selector | report exits 2 and asks for --latest or --ledger | PASS | `outputs/t06_report_missing_selector.*` | none confirmed | Good selector error. |
| 7 | report conflicting selectors | report --latest --ledger exits 2 with conflict message | PASS | `outputs/t07_report_conflicting_selectors.*` | none confirmed | Good selector guard. |
| 8 | stop missing selector | stop exits 2 and asks for --latest or --ledger | PASS | `outputs/t08_stop_missing_selector.*` | none confirmed | Good selector error. |
| 9 | stop conflicting selectors | stop --latest --ledger exits 2 with conflict message | PASS | `outputs/t09_stop_conflicting_selectors.*` | none confirmed | Good selector guard. |
| 10 | missing command | bare night-shift exits 2 and gives starter hint | PASS | `outputs/t10_missing_command.*` | none confirmed | Good beginner path. |

### Lane 03: Plan/Run Ledger Behavior

Lane status: `PASS`
Output artifact path: `lane-03-tests.tsv and lane-03-work/`
Bugs found:
- None confirmed from submitted evidence.
Improvement ideas:
- Keep dry-run and fake-lane checks in CI-style smoke coverage.

| # | Test | Command / Run Evidence Summary | Status | Output Artifact Path | Bugs Found | Improvement Ideas |
|---:|---|---|---:|---|---|---|
| 1 | version command | reported night-shift 0.1.0 | PASS | `lane-03-tests.tsv` | none confirmed | Good version check. |
| 2 | plan creates quiet ledger | quiet plan ledger created under lane-03-work/codex-home | PASS | `lane-03-work/codex-home/maestro/overnight/` | none confirmed | Keep ledger path in output. |
| 3 | plan ledger files | board/context/startup/mode/artifacts present | PASS | `lane-03-work/codex-home/maestro/overnight/` | none confirmed | Good ledger completeness. |
| 4 | board content | 12 safe board items plus quiet mode/safety line | PASS | `lane-03-work/codex-home/maestro/overnight/` | none confirmed | Good safety board. |
| 5 | context pack content | head/status/tracked files included | PASS | `lane-03-work/codex-home/maestro/overnight/` | none confirmed | Useful context pack. |
| 6 | plan stays dry | startup gate NOT_RUN and artifacts empty | PASS | `lane-03-work/codex-home/maestro/overnight/` | none confirmed | Good no-model plan behavior. |
| 7 | report plan ledger | report handles plan ledger | PASS | `lane-03-tests.tsv` | none confirmed | Good reporting surface. |
| 8 | bounded run with fake local lane | quiet run created ledger with fake local lane | PASS | `lane-03-work/codex-home/maestro/overnight/` | none confirmed | Good bounded run proof. |
| 9 | run ledger/token files | startup/board/context/mode/harvest/token/morning/process/artifacts present | PASS | `lane-03-work/codex-home/maestro/overnight/` | none confirmed | Good run ledger proof. |
| 10 | no repo mutation | head unchanged and status clean before/after | PASS | `lane-03-run-facts.txt` | none confirmed | Keep this as a hard invariant. |

### Lane 04: Mac Local Model Lane

Lane status: `FAIL`
Output artifact path: `lane-04-local-model.md and lane-04-proof/`
Bugs found:
- Local classification output was HOLD_DFS, which failed the strict allowed-label schema.
Improvement ideas:
- Constrain local classifier prompt or validate/retry when label is outside allowed set.

| # | Test | Command / Run Evidence Summary | Status | Output Artifact Path | Bugs Found | Improvement Ideas |
|---:|---|---|---:|---|---|---|
| 1 | LM Studio reachability | GET /models status=200 | PASS | `lane-04-proof/01-models.json` | none confirmed | Good local server check. |
| 2 | model listing | 14 models listed; preferred phi-4-mini-instruct present | PASS | `lane-04-proof/02-model-list.json` | none confirmed | Good model availability check. |
| 3 | classification prompt | local model returned a classification response | PASS | `lane-04-proof/03-classification.json` | none confirmed | Prompt reached model. |
| 4 | schema validation | classification did not match strict schema | FAIL | `lane-04-proof/04-schema-validation.json` | Allowed-label contract not enforced by model response. | Add parser validation and retry/tighter prompt. |
| 5 | timeout behavior | curl rc=28 after ~1s | PASS | `lane-04-proof/05-timeout.json` | none confirmed | Good timeout proof. |
| 6 | maestro-delegate local | delegate local rc=0 with proof path | PASS | `lane-04-proof/06-delegate-local.json` | none confirmed | Good proof artifact handoff. |
| 7 | proof artifact creation | command/meta/output/prompt/stderr files present | PASS | `lane-04-proof/07-proof-artifacts.json` | none confirmed | Good audit trail. |
| 8 | token accounting | token report captured local call | PASS | `lane-04-proof/08-token-report.json` | none confirmed | Good accounting hook. |
| 9 | private routing docs | 35 matching local/private routing lines | PASS | `lane-04-proof/09-private-routing-docs.json` | none confirmed | Good privacy docs coverage. |
| 10 | LM Studio down behavior | connection failure rc=7 without traceback | PASS | `lane-04-proof/10-lmstudio-down.json` | none confirmed | Good graceful failure. |

### Lane 05: Windows Worker Lane

Lane status: `FAIL`
Output artifact path: `lane-05-windows-worker.md`
Bugs found:
- Timeout behavior test crashed while importing bin/night-shift through importlib; dataclass module registration produced AttributeError.
Improvement ideas:
- Avoid importlib-loading CLI script in tests, or register module before exec_module; add a real timeout test path.

| # | Test | Command / Run Evidence Summary | Status | Output Artifact Path | Bugs Found | Improvement Ideas |
|---:|---|---|---:|---|---|---|
| 1 | endpoint config opt-in | DEFAULT_WINDOWS_URL empty and maestro-windows requires env/config | PASS | `lane-05-windows-worker.md` | none confirmed | Good opt-in default. |
| 2 | unconfigured failure | rc=2 with WINDOWS_WORKER_BASE_URL guidance | PASS | `lane-05-windows-worker.md` | none confirmed | Good setup error. |
| 3 | endpoint reachability | GET /models returned OpenAI-compatible JSON | PASS | `lane-05-windows-worker.md` | none confirmed | Good live endpoint proof. |
| 4 | expected model listed | qwen3-coder:30b present in model list | PASS | `lane-05-windows-worker.md` | none confirmed | Good model readiness check. |
| 5 | tiny worker prompt | Windows draft prompt returned safe JSON | PASS | `lane-05-windows-worker.md` | none confirmed | Good smoke prompt. |
| 6 | worker schema validation | parsed expected keys | PASS | `lane-05-windows-worker.md` | none confirmed | Good output contract check. |
| 7 | timeout behavior | test crashed with dataclass/importlib AttributeError | FAIL | `lane-05-windows-worker.md` | Timeout test harness bug masks actual timeout behavior. | Use subprocess CLI or proper module registration. |
| 8 | opt-in Windows docs | docs describe optional Windows and Mac-only fallback | PASS | `lane-05-windows-worker.md` | none confirmed | Good docs guardrail. |
| 9 | no raw LAN defaults | no private LAN URL hits outside examples | PASS | `lane-05-windows-worker.md` | none confirmed | Good public-safety posture. |
| 10 | delegate windows proof | maestro-delegate windows rc=0 and artifacts_ok=True | PASS | `lane-05-windows-worker.md` | none confirmed | Good proof path. |

### Lane 06: Report and Stop Flows

Lane status: `PASS`
Output artifact path: `lane-06-report-stop.md and lane-06-logs/`
Bugs found:
- None confirmed from submitted evidence.
Improvement ideas:
- Consider making malformed/minimal ledger report YELLOW instead of GREEN.

| # | Test | Command / Run Evidence Summary | Status | Output Artifact Path | Bugs Found | Improvement Ideas |
|---:|---|---|---:|---|---|---|
| 1 | report --latest | selects newest ledger and prints morning/token report | PASS | `lane-06-logs/01-report-latest.txt` | none confirmed | Good latest selection. |
| 2 | report explicit ledger | honors requested ledger path | PASS | `lane-06-logs/02-report-explicit-ledger.txt` | none confirmed | Good explicit selector. |
| 3 | report missing ledger | returns RED and non-zero | PASS | `lane-06-logs/03-report-missing-ledger.txt` | none confirmed | Good missing-ledger behavior. |
| 4 | report malformed ledger | does not crash and reports artifact count | PASS | `lane-06-logs/04-report-malformed-ledger.txt` | none confirmed | Maybe downgrade status to YELLOW. |
| 5 | stop --latest | writes STOP on newest ledger | PASS | `lane-06-logs/05-stop-latest.txt` | none confirmed | Good stop path. |
| 6 | stop explicit ledger | writes STOP on requested path | PASS | `lane-06-logs/06-stop-explicit-ledger.txt` | none confirmed | Good explicit stop. |
| 7 | stop no processes | reports zero signaled/already gone | PASS | `lane-06-logs/07-stop-no-active-processes.txt` | none confirmed | Good no-op handling. |
| 8 | idempotent stop | repeated stop succeeds and refreshes STOP | PASS | `lane-06-logs/08b-stop-idempotent-second.txt` | none confirmed | Good idempotency. |
| 9 | morning brief clarity | first action/totals/review needs/unknowns visible | PASS | `lane-06-logs/09-morning-brief-clarity.txt` | none confirmed | Good coordinator output. |
| 10 | live process cleanup | recorded sleep process terminated | PASS | `lane-06-logs/10-stop-live-process-cleanup.txt` | none confirmed | Good cleanup proof. |

### Lane 07: Safety and Public Readiness Scan

Lane status: `YELLOW`
Output artifact path: `lane-07-safety-public.md`
Bugs found:
- Public launch hold: private/source-available license placeholder, owner naming, and old closed PR/ref/cache exposure need resolution.
Improvement ideas:
- Use a clean public repo or GitHub-supported purge before public visibility; replace license before external contribution.

| # | Test | Command / Run Evidence Summary | Status | Output Artifact Path | Bugs Found | Improvement Ideas |
|---:|---|---|---:|---|---|---|
| 1 | private path scan | only expected example paths found; no real local paths in tracked content | PASS | `lane-07-safety-public.md` | none confirmed | Keep tracked docs path-safe. |
| 2 | Transcripted/private scan | no Transcripted hits in tracked files | PASS | `lane-07-safety-public.md` | none confirmed | Good product-data separation. |
| 3 | raw LAN/IP scan | localhost defaults only; no private LAN IPs in tracked content | PASS | `lane-07-safety-public.md` | none confirmed | Good public docs posture. |
| 4 | token/secret scan | no credential-looking literal tokens found | PASS | `lane-07-safety-public.md` | none confirmed | Keep secret scan in release checklist. |
| 5 | personal name scan | r3dbars owner only; no personal/family/address references | PASS | `lane-07-safety-public.md` | none confirmed | Decide public owner wording. |
| 6 | old product name scan | former-name/tokenmaxx/afterburner remnants are deliberate but need copy decision | PASS | `lane-07-safety-public.md` | none confirmed | Decide launch vocabulary. |
| 7 | dangerous claim scan | no guarantee/risk-free/fully autonomous claims | PASS | `lane-07-safety-public.md` | none confirmed | Strong safety posture. |
| 8 | unsafe autonomy scan | hits are negative safety boundaries, not positive claims | PASS | `lane-07-safety-public.md` | none confirmed | Keep no-release/no-deploy language. |
| 9 | stale PR/public blocker scan | README/SAFETY/CONTRIBUTING contain explicit blockers | YELLOW | `lane-07-safety-public.md` | Repo should not be made public yet. | Resolve old PR/ref/cache exposure path. |
| 10 | license/readiness docs | private/proprietary placeholder license present | YELLOW | `lane-07-safety-public.md` | License is not public/open-source ready. | Replace license before public distribution. |

### Lane 08: Installed Skill and Repo Skill Sync

Lane status: `FAIL`
Output artifact path: `lane-08-skill-install.md`
Bugs found:
- Installed skill and installed command are stale compared with repo source of truth; bare night-shift is not on PATH in this shell.
Improvement ideas:
- Rerun install.sh or sync repo skill/bin into real CODEX_HOME, then recheck PATH.

| # | Test | Command / Run Evidence Summary | Status | Output Artifact Path | Bugs Found | Improvement Ideas |
|---:|---|---|---:|---|---|---|
| 1 | installed SKILL metadata | installed description stale vs repo wording | FAIL | `lane-08-skill-install.md` | Installed skill uses stale wording. | Rerun installer. |
| 2 | repo SKILL sync | installed and repo SKILL.md differ | FAIL | `lane-08-skill-install.md` | Installed skill missing newer safety language. | Sync installed skill from repo. |
| 3 | examples README sync | installed skill lacks examples folder and expanded README | FAIL | `lane-08-skill-install.md` | Installed docs are stale/incomplete. | Install examples folder. |
| 4 | installed command availability | direct command exists but bare command not on PATH; direct command stale | FAIL | `lane-08-skill-install.md` | Installed command does not match repo behavior. | Update ~/.codex/bin and PATH. |
| 5 | install.sh temp update | temp install matched repo SKILL and executable command | PASS | `lane-08-skill-install.md` | none confirmed | Installer path is probably healthy. |
| 6 | old-name leakage | installed tree has 31 stale/old term matches | FAIL | `lane-08-skill-install.md` | Installed copy leaks stale terms. | Refresh installed skill tree. |
| 7 | skill trigger wording | repo trigger good, installed trigger stale | YELLOW | `lane-08-skill-install.md` | Runtime trigger may not match repo source. | Sync trigger wording. |
| 8 | closeout examples | repo examples present; installed examples stale | YELLOW | `lane-08-skill-install.md` | Installed closeouts are less user-generic. | Sync examples. |
| 9 | launcher paths | repo docs consistent; installed bare command unavailable on PATH | YELLOW | `lane-08-skill-install.md` | PATH setup may confuse normal use. | Add/update PATH setup. |
| 10 | normal-user understandability | repo README stronger than installed README | YELLOW | `lane-08-skill-install.md` | Installed docs lag onboarding quality. | Install current README/examples. |

### Lane 09: Toy Repo Quiet Lifecycle

Lane status: `YELLOW`
Output artifact path: `lane-09-*.log and tmp-toy/`
Bugs found:
- Only four lane logs were present, so six expected tests are missing/pending.
- Quiet run produced YELLOW with one local loop, zero Windows loops, zero tokens, and rejected artifact.
Improvement ideas:
- Emit a 10-row status file for lane 09; make quiet toy-repo no-remote behavior explicitly expected or remediated.

| # | Test | Command / Run Evidence Summary | Status | Output Artifact Path | Bugs Found | Improvement Ideas |
|---:|---|---|---:|---|---|---|
| 1 | doctor toy repo | doctor returned YELLOW: toy repo clean, local models reachable, Windows unconfigured, repo-fetch failed due no origin | YELLOW | `lane-09-doctor.log` | Toy repo without origin makes fetch warning visible. | Document no-origin toy behavior or skip fetch for local-only repos. |
| 2 | plan quiet | NIGHTSHIFT_PLAN: GREEN and created quiet ledger | PASS | `lane-09-plan.log` | none confirmed | Good planning path. |
| 3 | run quiet | NIGHTSHIFT_RUN: YELLOW local=1 windows=0 tokens=0; no delegate proofs | YELLOW | `lane-09-run.log` | Run did not produce useful token/proof output. | Improve local delegate capture or mark no-compute toy run expected. |
| 4 | report quiet run | NIGHTSHIFT_REPORT: GREEN but morning brief status YELLOW and artifact rejected | YELLOW | `lane-09-report.log` | Report command is green while run result is yellow. | Consider surfacing inner run status in report headline. |
| 5 | lane test 05 | No lane-09 evidence submitted for this expected test. | PENDING | `none found` | Missing lane evidence. | Emit complete 10-test status table. |
| 6 | lane test 06 | No lane-09 evidence submitted for this expected test. | PENDING | `none found` | Missing lane evidence. | Emit complete 10-test status table. |
| 7 | lane test 07 | No lane-09 evidence submitted for this expected test. | PENDING | `none found` | Missing lane evidence. | Emit complete 10-test status table. |
| 8 | lane test 08 | No lane-09 evidence submitted for this expected test. | PENDING | `none found` | Missing lane evidence. | Emit complete 10-test status table. |
| 9 | lane test 09 | No lane-09 evidence submitted for this expected test. | PENDING | `none found` | Missing lane evidence. | Emit complete 10-test status table. |
| 10 | lane test 10 | No lane-09 evidence submitted for this expected test. | PENDING | `none found` | Missing lane evidence. | Emit complete 10-test status table. |

### Lane 10: README / Examples Command Smoke

Lane status: `FAIL`
Output artifact path: `lane-10-command-logs/`
Bugs found:
- Example harvest sed commands fail because harvest.md and token-report.txt are missing after a zero-worker quiet run.
Improvement ideas:
- Either always create empty harvest/token-report files or update examples to tolerate no-compute ledgers.

| # | Test | Command / Run Evidence Summary | Status | Output Artifact Path | Bugs Found | Improvement Ideas |
|---:|---|---|---:|---|---|---|
| 1 | package check | scripts/check-package.sh exit 0 | PASS | `lane-10-command-logs/test-01.log` | none confirmed | Good package smoke. |
| 2 | temp install | ./install.sh --codex-home temp exit 0 | PASS | `lane-10-command-logs/test-02.log` | none confirmed | Good install smoke. |
| 3 | version after install | installed night-shift --version exit 0 | PASS | `lane-10-command-logs/test-03.log` | none confirmed | Good version path. |
| 4 | README doctor | doctor exit 0 but NIGHTSHIFT_DOCTOR: YELLOW for optional Windows unconfigured | YELLOW | `lane-10-command-logs/test-04.log` | Mac-only doctor returns yellow. | Clarify examples for Mac-only users. |
| 5 | README plan night-shift | plan --mode night-shift exit 0 | PASS | `lane-10-command-logs/test-05.log` | none confirmed | Good plan example. |
| 6 | zero-worker quiet run | run exit 0 but NIGHTSHIFT_RUN: YELLOW no cheap compute lanes reachable | YELLOW | `lane-10-command-logs/test-06.log` | Zero-worker run creates yellow ledger. | Explain expected yellow in examples. |
| 7 | report latest | report exit 0; morning brief status YELLOW | YELLOW | `lane-10-command-logs/test-07.log` | Report succeeds while brief is yellow. | Make report examples status-aware. |
| 8 | stop latest | stop --latest exit 0 and wrote stop file | PASS | `lane-10-command-logs/test-08.log` | none confirmed | Good stop example. |
| 9 | direct path fallback | direct command doctor exit 0 but status YELLOW for optional Windows | YELLOW | `lane-10-command-logs/test-09.log` | Mac-only doctor is yellow. | Document yellow as acceptable when Windows is optional. |
| 10 | morning harvest sed commands | sed failed: harvest.md and token-report.txt missing; exit 1 | FAIL | `lane-10-command-logs/test-10.log` | Example assumes files exist after zero-worker run. | Create placeholder files or update command to test file existence. |

## Bugs Found

- Lane 01: No confirmed code bug from lane summary; no explicit lane summary was provided.
- Lane 01: Doctor reports YELLOW when Windows is unconfigured; acceptable for Mac-only but needs clear expectation.
- Lane 02: Invalid --mode for plan/run exits correctly but hint incorrectly suggests doctor instead of the active subcommand.
- Lane 04: Local classification output was HOLD_DFS, which failed the strict allowed-label schema.
- Lane 05: Timeout behavior test crashed while importing bin/night-shift through importlib; dataclass module registration produced AttributeError.
- Lane 07: Public launch hold: private/source-available license placeholder, owner naming, and old closed PR/ref/cache exposure need resolution.
- Lane 08: Installed skill and installed command are stale compared with repo source of truth; bare night-shift is not on PATH in this shell.
- Lane 09: Only four lane logs were present, so six expected tests are missing/pending.
- Lane 09: Quiet run produced YELLOW with one local loop, zero Windows loops, zero tokens, and rejected artifact.
- Lane 10: Example harvest sed commands fail because harvest.md and token-report.txt are missing after a zero-worker quiet run.

## Ranked Next Fixes

1. Sync the installed skill and command from repo source: lane 08 is the biggest user-facing drift and install.sh already passes in a temp CODEX_HOME.
2. Fix CLI friendly hints for invalid plan/run modes so bad-argument guidance points to the active subcommand instead of doctor.
3. Fix the local classifier schema contract by constraining labels and retrying or rejecting non-allowed labels such as HOLD_DFS.
4. Fix the Windows timeout test harness/import path so it measures timeout behavior instead of crashing inside dataclass importlib loading.
5. Make zero-worker/no-compute ledgers always include harvest.md and token-report.txt placeholders, or update examples/report output to avoid promising missing files.
6. Resolve public-readiness blockers before visibility changes: license, owner wording, old PR/ref/cache exposure, and launch vocabulary.
7. Standardize every lane artifact with a 10-test status table; lane 09 only submitted four usable test logs.

## PR Decision

This sanitized tracker is safe to keep in repo docs because it omits raw local machine paths, secrets, and private endpoint values.

## Lanes Used

lanes used: Codex=aggregated lane artifacts, classified evidence, wrote tracker, and prepared sanitized docs PR; Claude=skipped; Local=skipped; Windows=skipped
