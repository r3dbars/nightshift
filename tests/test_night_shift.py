import importlib.machinery
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
LOADER = importlib.machinery.SourceFileLoader("night_shift_cli", str(ROOT / "bin" / "night-shift"))
SPEC = importlib.util.spec_from_loader(LOADER.name, LOADER)
night_shift = importlib.util.module_from_spec(SPEC)
sys.modules[LOADER.name] = night_shift
LOADER.exec_module(night_shift)


class NightShiftQualityTests(unittest.TestCase):
    def test_ten_hour_stop_option(self):
        self.assertEqual(night_shift.STOP_SECONDS["10h"], 10 * 60 * 60)
        self.assertEqual(night_shift.stop_label("10h"), "Stop after 10 hours")

    def test_deadline_cancels_recorded_worker_process(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            process = subprocess.Popen(["sleep", "30"], start_new_session=True)
            (ledger / "processes.tsv").write_text(f"{process.pid}\t0\tsleep 30\n", encoding="utf-8")
            started = night_shift.time.time()
            night_shift.cancel_pending_workers(ledger, [])
            process.wait(timeout=2)
            self.assertLess(night_shift.time.time() - started, 2)
            self.assertNotEqual(process.returncode, 0)

    def test_old_config_keeps_single_repo_scope(self):
        self.assertEqual(night_shift.configured_scope({"schema_version": 2, "preferences": {}}), "current")
        self.assertEqual(night_shift.configured_scope({}), "github-recent")
        self.assertEqual(
            night_shift.configured_scope({"schema_version": 3, "preferences": {"scope": "github-recent"}}),
            "github-recent",
        )

    def test_generic_safe_output_is_rejected(self):
        output = """CLAIM: Improve test coverage
BEST_NEXT_ACTION: Add more tests
ACTION_TYPE: patch-plan
SAFE_FOR_DRAFT_PR: yes
CONFIDENCE: high
"""
        self.assertEqual(night_shift.score_output(0, output, ["bin/night-shift"]), "REJECT")
        self.assertIn("missing repo evidence", night_shift.output_quality_reasons(0, output, ["bin/night-shift"]))

    def test_grounded_output_can_be_kept(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
            output = """CLAIM: The answer function returns the stable value 42
EVIDENCE: app.py:2 |     return 42
WHY_NOW: app.py changed recently
BEST_NEXT_ACTION: preserve this behavior with a focused regression test
FILES_TO_TOUCH: app.py
TESTS_TO_RUN: python -m pytest
EXPECTED_RESULT: the focused test passes
ACTION_TYPE: patch-plan
SAFE_FOR_DRAFT_PR: yes
CONFIDENCE: high
"""
            self.assertEqual(
                night_shift.score_output(0, output, ["app.py"], ["python -m pytest"], repo),
                "MAYBE",
            )

    def test_old_observed_fact_evidence_format_is_rejected(self):
        output = """CLAIM: A grounded-looking claim
EVIDENCE: app.py:2 - an interpretation rather than an exact quote
FILES_TO_TOUCH: app.py
TESTS_TO_RUN: python -m pytest
EXPECTED_RESULT: pass
ACTION_TYPE: patch-plan
SAFE_FOR_DRAFT_PR: yes
"""
        self.assertEqual(night_shift.score_output(0, output, ["app.py"], ["python -m pytest"]), "REJECT")

    def test_test_backed_negative_claim_can_become_candidate_not_proof(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
            output = """CLAIM: The answer path does not return 42 for the failing case
EVIDENCE: app.py:2 |     return 42
WHY_NOW: CI names this path
PROPOSED_CHANGE: add the failing case and repair the branch
FILES_TO_TOUCH: app.py
TESTS_TO_RUN: python -m pytest
EXPECTED_RESULT: the failing case passes
ACTION_TYPE: patch-plan
SAFE_FOR_DRAFT_PR: yes
"""
            score = night_shift.score_output(
                0,
                output,
                ["app.py"],
                ["python -m pytest"],
                repo,
                proof_kind="test",
            )
            self.assertEqual(score, "MAYBE")

    def test_invented_verification_command_is_not_kept(self):
        output = """CLAIM: A focused test gap exists
EVIDENCE: app.py:2 - the branch has no matching assertion
WHY_NOW: app.py changed recently
BEST_NEXT_ACTION: add one regression test
FILES_TO_TOUCH: app.py
TESTS_TO_RUN: imaginary-test-command
EXPECTED_RESULT: regression test passes
ACTION_TYPE: patch-plan
SAFE_FOR_DRAFT_PR: yes
CONFIDENCE: high
"""
        score = night_shift.score_output(0, output, ["app.py"], ["python -m pytest"])
        self.assertEqual(score, "REJECT")

    def test_model_cannot_approve_an_unsupplied_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "app.py").write_text("value = 1\n", encoding="utf-8")
            (repo / "invented.py").write_text("value = 2\n", encoding="utf-8")
            output = """CLAIM: The supplied app value is 1
EVIDENCE: app.py:1 | value = 1
WHY_NOW: app.py changed
PROPOSED_CHANGE: edit a different file
FILES_TO_TOUCH: invented.py
TESTS_TO_RUN: python -m pytest
EXPECTED_RESULT: tests pass
ACTION_TYPE: patch-plan
SAFE_FOR_DRAFT_PR: yes
"""
            self.assertEqual(
                night_shift.score_output(0, output, ["app.py"], ["python -m pytest"], repo),
                "REJECT",
            )

    def test_real_but_irrelevant_source_line_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
            output = """CLAIM: Config fallback has no regression test
EVIDENCE: app.py:2 - this line runs a TODO scanner
WHY_NOW: config changed recently
BEST_NEXT_ACTION: add a fallback test
FILES_TO_TOUCH: app.py
TESTS_TO_RUN: python -m pytest
EXPECTED_RESULT: fallback test passes
ACTION_TYPE: patch-plan
SAFE_FOR_DRAFT_PR: yes
CONFIDENCE: high
"""
            score = night_shift.score_output(
                0,
                output,
                ["app.py"],
                ["python -m pytest"],
                repo,
            )
            self.assertNotEqual(score, "KEEP")

    def test_negative_file_claim_must_cite_that_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "scripts").mkdir()
            (repo / "scripts" / "check.sh").write_text("echo checks\n", encoding="utf-8")
            (repo / "PACKAGE.md").write_text("Confirm copyright year is right.\n", encoding="utf-8")
            output = """CLAIM: `scripts/check.sh` does not validate the copyright year
EVIDENCE: PACKAGE.md:1 | Confirm copyright year is right.
WHY_NOW: packaging changed
BEST_NEXT_ACTION: add a year check
FILES_TO_TOUCH: scripts/check.sh
TESTS_TO_RUN: bash scripts/check.sh
EXPECTED_RESULT: check passes
ACTION_TYPE: patch-plan
SAFE_FOR_DRAFT_PR: yes
CONFIDENCE: high
"""
            score = night_shift.score_output(
                0,
                output,
                ["scripts/check.sh", "PACKAGE.md"],
                ["bash scripts/check.sh"],
                repo,
            )
            self.assertEqual(score, "REJECT")
            reasons = night_shift.output_quality_reasons(
                0,
                output,
                ["scripts/check.sh", "PACKAGE.md"],
                ["bash scripts/check.sh"],
                repo,
            )
            self.assertIn("negative claim requires deterministic repository proof", reasons)

    def test_queue_has_no_generic_work_without_repo_signals(self):
        scan = {
            "recent_files": [],
            "test_files": [],
            "doc_files": [],
            "todo_sample": [],
            "test_commands": [],
            "github_open_prs_raw": "[]",
            "github_open_issues_raw": "[]",
            "github_failed_runs_raw": "[]",
        }
        queue = night_shift.build_repo_work_queue(None, scan, "night-shift", "draft-local")
        self.assertEqual(queue, [])

    def test_task_evidence_pack_contains_real_numbered_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Night Shift Test"], cwd=repo, check=True)
            (repo / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
            subprocess.run(["git", "add", "app.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
            task = {"files": ["app.py"]}
            pack = night_shift.task_evidence_pack(repo, task, "base context")
            self.assertIn("## file-excerpt: app.py", pack)
            self.assertIn("    2 |     return 42", pack)

    def test_task_evidence_pack_numbers_live_ci_evidence(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            task = {
                "files": [],
                "evidence_sources": {
                    "github-actions/run-42.log": "setup complete\nError: expected 42 but received 41\n"
                },
            }
            pack = night_shift.task_evidence_pack(repo, task, "base context")
            self.assertIn("## live-evidence: github-actions/run-42.log", pack)
            self.assertIn("    2 | Error: expected 42 but received 41", pack)
            context = night_shift.task_context_block(task)
            self.assertIn("EVIDENCE must cite one supplied live-evidence path exactly", context)

    def test_task_evidence_pack_reads_pinned_source_ref(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Night Shift Test"], cwd=repo, check=True)
            (repo / "app.py").write_text("def answer():\n    return 41\n", encoding="utf-8")
            subprocess.run(["git", "add", "app.py"], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "old"], cwd=repo, check=True)
            old_ref = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            (repo / "app.py").write_text("def answer():\n    return 42\n", encoding="utf-8")
            subprocess.run(["git", "commit", "-qam", "new"], cwd=repo, check=True)
            new_ref = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            subprocess.run(["git", "checkout", "-q", old_ref], cwd=repo, check=True)
            task = {"files": ["app.py"], "source_ref": new_ref}
            pack = night_shift.task_evidence_pack(repo, task, "base context")
            self.assertIn("    2 |     return 42", pack)
            self.assertNotIn("    2 |     return 41", pack)

            output = """CLAIM: The pinned answer function returns 42
EVIDENCE: app.py:2 |     return 42
WHY_NOW: the failed branch changed this path
PROPOSED_CHANGE: preserve the pinned behavior
FILES_TO_TOUCH: app.py
TESTS_TO_RUN: python -m pytest
EXPECTED_RESULT: the pinned branch test passes
ACTION_TYPE: patch-plan
SAFE_FOR_DRAFT_PR: yes
"""
            self.assertEqual(
                night_shift.score_output(
                    0,
                    output,
                    ["app.py"],
                    ["python -m pytest"],
                    repo,
                    "test",
                    {},
                    new_ref,
                ),
                "MAYBE",
            )

    def test_live_ci_evidence_can_create_a_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "app.py").write_text("def answer():\n    return 41\n", encoding="utf-8")
            live_sources = {"github-actions/run-42.log": "Error: expected 42 but received 41\n"}
            output = """CLAIM: CI received 41 where the test expected 42
EVIDENCE: github-actions/run-42.log:1 | Error: expected 42 but received 41
WHY_NOW: the latest CI run failed
PROPOSED_CHANGE: inspect and repair the answer path
FILES_TO_TOUCH: app.py
TESTS_TO_RUN: python -m pytest
EXPECTED_RESULT: CI receives 42 and the test passes
ACTION_TYPE: patch-plan
SAFE_FOR_DRAFT_PR: yes
CONFIDENCE: high
"""
            score = night_shift.score_output(
                0,
                output,
                ["app.py"],
                ["python -m pytest"],
                repo,
                proof_kind="test",
                evidence_sources=live_sources,
            )
            self.assertEqual(score, "MAYBE")

    def test_failed_ci_queue_starts_with_newest_run(self):
        scan = {
            "recent_files": ["app.py"],
            "tracked_files": ["app.py", ".github/workflows/ci.yml"],
            "test_files": [],
            "doc_files": [],
            "todo_sample": [],
            "test_commands": ["python -m pytest"],
            "github_open_prs_raw": "[]",
            "github_open_issues_raw": "[]",
            "github_failed_runs_raw": json.dumps([
                {"databaseId": 10, "updatedAt": "2026-07-10T01:00:00Z"},
                {"databaseId": 20, "updatedAt": "2026-07-10T02:00:00Z"},
            ]),
            "github_failed_logs_raw": json.dumps([
                {"run": {"databaseId": 10}, "log": "old failure"},
                {"run": {"databaseId": 20}, "log": "new failure"},
            ]),
        }
        queue = night_shift.build_repo_work_queue(Path("/tmp/repo"), scan, "quiet", "brief")
        failed = [item for item in queue if item["slug"].startswith("failed-ci-")]
        self.assertEqual(failed[0]["slug"], "failed-ci-20")
        self.assertEqual(failed[0]["evidence_sources"]["github-actions/run-20.log"], "new failure")

    def test_failed_ci_queue_pins_branch_sha_and_new_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Night Shift Test"], cwd=repo, check=True)
            (repo / "README.md").write_text("base\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "base"], cwd=repo, check=True)
            base_ref = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            path = repo / "app" / "api" / "new" / "route.ts"
            path.parent.mkdir(parents=True)
            path.write_text("export const GET = rawHandler\n", encoding="utf-8")
            (repo / "package.json").write_text(
                json.dumps({"scripts": {"check:routes": "tsx scripts/check-routes.ts"}}),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "branch route"], cwd=repo, check=True)
            branch_ref = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=repo, text=True).strip()
            subprocess.run(["git", "checkout", "-q", base_ref], cwd=repo, check=True)
            run = {"databaseId": 42, "headBranch": "feature", "headSha": branch_ref, "updatedAt": "2026-07-10T02:00:00Z"}
            scan = {
                "recent_files": ["README.md"],
                "tracked_files": ["README.md"],
                "test_files": [],
                "doc_files": ["README.md"],
                "todo_sample": [],
                "test_commands": ["npm run check:routes"],
                "github_open_prs_raw": "[]",
                "github_open_issues_raw": "[]",
                "github_failed_runs_raw": json.dumps([run]),
                "github_failed_logs_raw": json.dumps([{
                    "run": run,
                    "log": "/home/runner/work/repo/repo/app/api/new/route.ts:1\nAssertionError: wrapper required",
                }]),
            }
            queue = night_shift.build_repo_work_queue(repo, scan, "quiet", "brief")
            failed = next(item for item in queue if item["slug"] == "failed-ci-42")
            self.assertEqual(failed["source_ref"], branch_ref)
            self.assertIn("app/api/new/route.ts", failed["files"])
            self.assertIn("npm run check:routes", failed["verification_commands"])

    def test_github_actions_log_transport_prefix_is_removed(self):
        raw = (
            "verify / tests\tUNKNOWN STEP\t2026-07-10T09:40:29.3485837Z AssertionError: expected 42\n"
            "plain local line\n"
        )
        self.assertEqual(
            night_shift.normalize_github_actions_log(raw),
            "AssertionError: expected 42\nplain local line",
        )

    def test_github_actions_failure_evidence_excludes_passing_test_noise(self):
        raw = "\n".join([
            "job\tstep\t2026-07-10T09:40:29Z AssertionError: wrapper required",
            "job\tstep\t2026-07-10T09:40:30Z app/api/new/route.ts",
            *[f"job\tstep\t2026-07-10T09:41:{index:02d}Z filler {index}" for index in range(20)],
            "job\tstep\t2026-07-10T09:42:00Z prisma:error expected policy rejection",
        ])
        evidence = night_shift.extract_github_actions_failure_evidence(raw)
        self.assertIn("AssertionError: wrapper required", evidence)
        self.assertIn("app/api/new/route.ts", evidence)
        self.assertNotIn("expected policy rejection", evidence)

    def test_local_feedback_changes_ranking(self):
        with tempfile.TemporaryDirectory() as tmp:
            original = night_shift.FEEDBACK_PATH
            night_shift.FEEDBACK_PATH = Path(tmp) / "feedback.jsonl"
            try:
                night_shift.FEEDBACK_PATH.write_text(
                    json.dumps({"key": "task:tests:patch-plan", "verdict": "not-useful"}) + "\n",
                    encoding="utf-8",
                )
                self.assertLess(night_shift.feedback_adjustment("task:tests:patch-plan"), 0)
                self.assertEqual(night_shift.feedback_adjustment("another:key"), 0)
            finally:
                night_shift.FEEDBACK_PATH = original

    def test_feedback_rejects_zero_rank(self):
        args = SimpleNamespace(useful=True, not_useful=False, item=0)
        with redirect_stdout(io.StringIO()):
            self.assertEqual(night_shift.command_feedback(args), 2)

    def test_inline_code_is_cleaned_for_morning_output(self):
        self.assertEqual(night_shift.clean_inline_code("`bash scripts/check-package.sh`"), "bash scripts/check-package.sh")

    def test_saved_compute_settings_are_default_fallback(self):
        with tempfile.TemporaryDirectory() as tmp:
            original_path = night_shift.CONFIG_PATH
            original_env = {key: os.environ.get(key) for key in (
                "MAESTRO_LOCAL_BASE_URL", "MAESTRO_LOCAL_MODEL", "WINDOWS_WORKER_BASE_URL", "WINDOWS_WORKER_MODEL"
            )}
            night_shift.CONFIG_PATH = Path(tmp) / "config.json"
            night_shift.CONFIG_PATH.write_text(json.dumps({
                "legacy": {
                    "local_url": "http://mac.test/v1",
                    "local_model": "mac-coder",
                    "windows_url": "http://windows.test/v1",
                    "windows_model": "windows-coder",
                }
            }), encoding="utf-8")
            try:
                for key in original_env:
                    os.environ.pop(key, None)
                args = SimpleNamespace(local_url=None, local_model=None, windows_url=None, windows_model=None)
                night_shift.apply_compute_overrides(args)
                self.assertEqual(os.environ["MAESTRO_LOCAL_MODEL"], "mac-coder")
                self.assertEqual(os.environ["WINDOWS_WORKER_MODEL"], "windows-coder")
            finally:
                night_shift.CONFIG_PATH = original_path
                for key, value in original_env.items():
                    if value is None:
                        os.environ.pop(key, None)
                    else:
                        os.environ[key] = value

    def test_task_fingerprint_changes_with_repo_revision(self):
        task = {"slug": "source-map-01", "kind": "map", "files": ["app.py"]}
        first = night_shift.task_fingerprint("owner/repo", "abc123", task)
        self.assertEqual(first, night_shift.task_fingerprint("owner/repo", "abc123", task))
        self.assertNotEqual(first, night_shift.task_fingerprint("owner/repo", "def456", task))

    def test_compounding_queue_uses_unique_ladder_tasks(self):
        scan = {
            "recent_files": ["src/app.ts"],
            "source_files": ["src/app.ts", "src/util.ts"],
            "test_files": ["tests/app.test.ts"],
            "doc_files": ["README.md"],
            "todo_sample": [],
            "test_commands": ["npm test"],
            "github_open_prs_raw": "[]",
            "github_open_issues_raw": "[]",
            "github_failed_runs_raw": "[]",
        }
        queue = night_shift.build_repo_work_queue(Path("/tmp/repo"), scan, "night-shift", "draft-local")
        slugs = [item["slug"] for item in queue]
        self.assertEqual(len(slugs), len(set(slugs)))
        self.assertIn("changed-file-proof-01-src-app-ts", slugs)
        self.assertIn("test-contract-map-01", slugs)
        self.assertIn("source-map-01", slugs)
        self.assertTrue(all(item["ladder"] in night_shift.TASK_LADDER for item in queue))

    def test_live_work_creates_specific_tasks_not_generic_drafts(self):
        scan = {
            "recent_files": ["src/app.ts"],
            "source_files": ["src/app.ts"],
            "test_files": ["tests/app.test.ts"],
            "doc_files": [],
            "todo_sample": [],
            "test_commands": ["npm test"],
            "github_open_prs_raw": json.dumps([{"number": 12, "files": [{"path": "src/app.ts"}], "statusCheckRollup": []}]),
            "github_open_issues_raw": json.dumps([{"number": 34, "title": "Fix app"}]),
            "github_failed_runs_raw": json.dumps([{"databaseId": 56}]),
            "github_failed_logs_raw": json.dumps([{"run": {"databaseId": 56}, "log": "app test failed"}]),
        }
        queue = night_shift.build_repo_work_queue(Path("/tmp/repo"), scan, "night-shift", "draft-prs")
        slugs = {item["slug"] for item in queue}
        self.assertIn("pr-12-review", slugs)
        self.assertIn("issue-34-next-action", slugs)
        self.assertIn("failed-ci-56", slugs)
        self.assertNotIn("draft-pr-candidate", slugs)
        self.assertNotIn("small-safe-fix-candidate", slugs)

    def test_detect_test_commands_supports_common_repo_types(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            tracked = ["Cargo.toml", "go.mod", "Package.swift", "tests/test_app.py", "run-tests.sh"]
            commands = night_shift.detect_test_commands(repo, tracked)
        self.assertIn("cargo test", commands)
        self.assertIn("go test ./...", commands)
        self.assertIn("swift test", commands)
        self.assertIn("python3 -m unittest discover -s tests -p 'test_*.py'", commands)
        self.assertIn("bash run-tests.sh", commands)

    def test_hostile_package_script_never_becomes_a_command_suggestion(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "package.json").write_text(
                json.dumps({"scripts": {"test:unit; echo NIGHT_SHIFT_INJECTION": "echo nope"}}),
                encoding="utf-8",
            )
            commands = night_shift.detect_test_commands(repo, ["package.json"])
            self.assertFalse(any("NIGHT_SHIFT_INJECTION" in command for command in commands))

    def test_repo_profile_requires_owned_sandbox_and_argv(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".night-shift.json").write_text(
                json.dumps({
                    "version": 1,
                    "trust": "fork",
                    "execution": "sandbox-only",
                    "image": "runner@sha256:" + "0" * 64,
                    "commands": [["python3", "-m", "pytest"]],
                }),
                encoding="utf-8",
            )
            profile, detail = night_shift.load_repo_profile(repo)
            self.assertEqual(detail, "profile loaded")
            self.assertFalse(profile.may_execute)
            (repo / ".night-shift.json").write_text(
                json.dumps({"version": 1, "trust": "owned", "execution": "sandbox-only", "image": "runner@sha256:" + "0" * 64, "commands": ["python3 -m pytest"]}),
                encoding="utf-8",
            )
            profile, detail = night_shift.load_repo_profile(repo)
            self.assertIsNone(profile)
            self.assertIn("argv", detail)

    def test_rejected_task_cooldown_and_new_head_behavior(self):
        previous = {"head": "abc", "state": "REJECTED", "epoch": 1000, "rejections": 2}
        self.assertFalse(night_shift.may_attempt(previous, "task", "abc", now=1001)[0])
        self.assertTrue(night_shift.may_attempt(previous, "task", "def", now=1001)[0])
        self.assertTrue(night_shift.may_attempt(previous, "task", "abc", now=3000)[0])

    def test_active_autopilot_ignores_stale_pid_state(self):
        previous = night_shift.AUTOPILOT_STATE_PATH
        with tempfile.TemporaryDirectory() as tmp:
            night_shift.AUTOPILOT_STATE_PATH = Path(tmp) / "active.json"
            night_shift.AUTOPILOT_STATE_PATH.write_text('{"pid": 99999999}\n', encoding="utf-8")
            self.assertEqual(night_shift.active_autopilot(), {})
        night_shift.AUTOPILOT_STATE_PATH = previous

    def test_cleanup_only_selects_old_reviewed_completed_ledgers(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            old = root / "night-shift-old"
            old.mkdir()
            (old / "morning.md").write_text("done\n", encoding="utf-8")
            (old / "REVIEWED").write_text("yes\n", encoding="utf-8")
            recent = root / "night-shift-recent"
            recent.mkdir()
            (recent / "morning.md").write_text("done\n", encoding="utf-8")
            (recent / "REVIEWED").write_text("yes\n", encoding="utf-8")
            unreviewed = root / "night-shift-unreviewed"
            unreviewed.mkdir()
            (unreviewed / "morning.md").write_text("done\n", encoding="utf-8")
            now = time.time()
            os.utime(old, (now - 30 * 86400, now - 30 * 86400))
            self.assertEqual(night_shift.cleanup_candidates(root, 21, now=now), [old])

    def test_profile_protects_verifier_and_dependency_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Night Shift Test"], cwd=repo, check=True)
            (repo / "package.json").write_text("{}\n", encoding="utf-8")
            (repo / ".night-shift.json").write_text(
                json.dumps({"version": 1, "trust": "owned", "execution": "sandbox-only", "image": "runner@sha256:" + "0" * 64, "commands": [["true"]]}),
                encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
            (repo / "package.json").write_text('{"scripts":{"test":"true"}}\n', encoding="utf-8")
            profile, _ = night_shift.load_repo_profile(repo)
            self.assertIn("patch touched an immutable verifier, dependency, or policy file", night_shift.DraftEngine(night_shift.run_cmd, Path(tmp) / "w", lambda: "x").guard_reasons(repo, ["package.json"], profile))

    def test_patch_protocol_rejects_protected_and_unapproved_paths(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".night-shift.json").write_text(
                json.dumps({
                    "version": 1, "trust": "owned", "execution": "sandbox-only",
                    "image": "runner@sha256:" + "0" * 64,
                    "commands": [["true"]], "allowed_paths": ["src", "tests"],
                }), encoding="utf-8",
            )
            profile, _ = night_shift.load_repo_profile(repo)
            output = """diff --git a/package.json b/package.json
--- a/package.json
+++ b/package.json
@@ -1 +1 @@
-{}
+{"scripts":{"test":"true"}}
"""
            check = night_shift.validate_patch(output, ["package.json"], profile)
            self.assertFalse(check.valid)
            self.assertTrue(any("immutable" in reason for reason in check.reasons))

    def test_patch_protocol_rejects_model_prose_and_renames(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / ".night-shift.json").write_text(
                json.dumps({
                    "version": 1, "trust": "owned", "execution": "sandbox-only",
                    "image": "runner@sha256:" + "0" * 64,
                    "commands": [["true"]], "allowed_paths": ["src"],
                }), encoding="utf-8",
            )
            profile, _ = night_shift.load_repo_profile(repo)
            prose = night_shift.validate_patch("I would change src/app.py", ["src/app.py"], profile)
            self.assertFalse(prose.valid)
            rename = night_shift.validate_patch(
                "diff --git a/src/app.py b/src/other.py\n--- a/src/app.py\n+++ b/src/other.py\n@@ -1 +1 @@\n-a\n+b\n",
                ["src/app.py"], profile,
            )
            self.assertFalse(rename.valid)

    def test_patch_runner_is_no_network_and_never_writes_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / ".night-shift.json").write_text(
                json.dumps({
                    "version": 1, "trust": "owned", "execution": "sandbox-only",
                    "image": "runner@sha256:" + "0" * 64, "commands": [["true"]],
                }), encoding="utf-8",
            )
            profile, _ = night_shift.load_repo_profile(root)
            command = __import__("night_shift_sandbox").sandbox_patch_command(
                root, root / "candidate.patch", root / "artifacts", ("true",), profile
            )
            self.assertIn("--network", command)
            self.assertEqual(command[command.index("--network") + 1], "none")
            self.assertIn("--pull", command)
            self.assertEqual(command[command.index("--pull") + 1], "never")
            self.assertIn(f"{root.resolve()}:/source:ro", command)

    def test_reproduced_failure_can_only_become_proven_after_isolated_patch_verification(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            ledger = Path(tmp) / "ledger"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Night Shift Test"], cwd=repo, check=True)
            (repo / "src").mkdir()
            (repo / "src" / "app.py").write_text("value = 1\n", encoding="utf-8")
            (repo / ".night-shift.json").write_text(
                json.dumps({
                    "version": 1, "trust": "owned", "execution": "sandbox-only",
                    "image": "runner@sha256:" + "0" * 64, "commands": [["true"]],
                    "allowed_paths": ["src"],
                }), encoding="utf-8",
            )
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
            profile, _ = night_shift.load_repo_profile(repo)
            patch = "diff --git a/src/app.py b/src/app.py\n--- a/src/app.py\n+++ b/src/app.py\n@@ -1 +1 @@\n-value = 1\n+value = 2\n"

            def fake_run(args, cwd=None, timeout=60, env=None, pid_log=None):
                args = [str(part) for part in args]
                if args[0] == "git":
                    result = subprocess.run(args, cwd=cwd, text=True, capture_output=True, timeout=timeout)
                    return night_shift.CmdResult(" ".join(args), result.returncode, result.stdout, result.stderr)
                if "maestro-delegate" in args[0]:
                    return night_shift.CmdResult(" ".join(args), 0, patch, "")
                if args[0] == "docker":
                    volumes = [args[index + 1] for index, value in enumerate(args) if value == "--volume"]
                    if any(value.endswith(":/input/candidate.patch:ro") for value in volumes):
                        artifact_volume = next(value for value in volumes if value.endswith(":/artifacts:rw"))
                        artifact_dir = Path(artifact_volume.removesuffix(":/artifacts:rw"))
                        artifact_dir.mkdir(parents=True, exist_ok=True)
                        (artifact_dir / "changed-paths.txt").write_text("src/app.py\n", encoding="utf-8")
                        (artifact_dir / "applied.patch").write_text(patch, encoding="utf-8")
                        (artifact_dir / "verification.rc").write_text("0\n", encoding="utf-8")
                        (artifact_dir / "verification.txt").write_text("passed\n", encoding="utf-8")
                        return night_shift.CmdResult("docker patch", 0, "", "")
                    return night_shift.CmdResult("docker baseline", 1, "", "failing baseline")
                raise AssertionError(f"unexpected command: {args}")

            engine = night_shift.DraftEngine(fake_run, Path(tmp) / "worktrees", lambda: "now")
            result = engine.run_draft(
                repo, "owner/repo", {
                    "key": "repair", "summary": "repair value", "evidence": "src/app.py:1",
                    "expected_result": "true passes", "files": ["src/app.py"],
                    "verification_argv": ["true"],
                }, ledger, 900, "http://windows:11434/v1", "coder", profile=profile,
            )
            self.assertEqual(result["status"], "PROVEN_REPAIR")
            self.assertEqual(result["baseline_rc"], 1)
            self.assertEqual(result["after_rc"], 0)
            self.assertTrue(Path(result["patch"]).is_file())

    def test_detect_test_commands_includes_named_package_checks(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            (repo / "package.json").write_text(
                json.dumps({"scripts": {"test": "vitest", "test:rls": "vitest rls", "check:routes": "tsx check.ts"}}),
                encoding="utf-8",
            )
            commands = night_shift.detect_test_commands(repo, ["package.json"])
            self.assertIn("npm run test:rls", commands)
            self.assertIn("npm run check:routes", commands)

    def test_github_portfolio_prioritizes_failed_runs(self):
        original_run_cmd = night_shift.run_cmd
        now = night_shift.datetime.now(night_shift.timezone.utc).isoformat().replace("+00:00", "Z")

        def fake_run(cmd, **kwargs):
            command = [str(part) for part in cmd]
            if command[:3] == ["gh", "api", "user"]:
                return night_shift.CmdResult("", 0, "owner\n", "")
            if command[:3] == ["gh", "repo", "list"]:
                payload = [
                    {"nameWithOwner": "owner/calm", "pushedAt": now, "isPrivate": False, "isArchived": False, "isFork": False, "defaultBranchRef": {"name": "main"}, "url": ""},
                    {"nameWithOwner": "owner/broken", "pushedAt": now, "isPrivate": True, "isArchived": False, "isFork": False, "defaultBranchRef": {"name": "main"}, "url": ""},
                ]
                return night_shift.CmdResult("", 0, json.dumps(payload), "")
            if command[:3] == ["gh", "run", "list"] and "owner/broken" in command:
                return night_shift.CmdResult(
                    "",
                    0,
                    json.dumps([{"databaseId": 1, "workflowName": "CI", "headBranch": "main", "status": "completed", "conclusion": "failure", "updatedAt": now}]),
                    "",
                )
            if command and command[0] == "gh":
                return night_shift.CmdResult("", 0, "[]", "")
            return night_shift.CmdResult("", 1, "", "unsupported")

        night_shift.run_cmd = fake_run
        try:
            portfolio = night_shift.discover_github_portfolio(None, active_days=14, max_repos=2)
        finally:
            night_shift.run_cmd = original_run_cmd
        self.assertEqual(portfolio[0]["slug"], "owner/broken")
        self.assertGreater(portfolio[0]["score"], portfolio[1]["score"])

    def test_draft_guard_rejects_unapproved_files(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Night Shift Test"], cwd=repo, check=True)
            (repo / "app.py").write_text("value = 1\n", encoding="utf-8")
            (repo / "other.py").write_text("other = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
            (repo / "other.py").write_text("other = 2\n", encoding="utf-8")
            reasons = night_shift.draft_guard_reasons(repo, ["app.py"])
            self.assertIn("patch touched a file outside the approved candidate set", reasons)

    def test_draft_guard_rejects_policy_bypass(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp)
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Night Shift Test"], cwd=repo, check=True)
            (repo / "checks.ts").write_text("const allowlist = []\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
            (repo / "checks.ts").write_text("const allowlist = ['skip-security-check']\n", encoding="utf-8")
            reasons = night_shift.draft_guard_reasons(repo, ["checks.ts"])
            self.assertIn("patch appears to bypass a test, check, or security policy", reasons)

    def test_draft_proof_distinguishes_repairs_from_clean_drafts(self):
        self.assertEqual(
            night_shift.draft_proof_status(1, 0, []),
            ("PROVEN_REPAIR", "failing-before and passing-after"),
        )
        self.assertEqual(
            night_shift.draft_proof_status(0, 0, []),
            ("VERIFIED_DRAFT", "passing repository check after a bounded patch"),
        )
        self.assertEqual(night_shift.draft_proof_status(1, 1, ["verification failed"])[0], "REJECT")

    def test_draft_timeout_obeys_absolute_deadline_and_stop_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            stop_file = Path(tmp) / "STOP"
            self.assertLessEqual(
                night_shift.remaining_draft_timeout(900, night_shift.time.time() + 2, stop_file),
                2,
            )
            self.assertEqual(
                night_shift.remaining_draft_timeout(900, night_shift.time.time() - 1, stop_file),
                0,
            )
            stop_file.write_text("stop\n", encoding="utf-8")
            self.assertEqual(night_shift.remaining_draft_timeout(900, None, stop_file), 0)

    def test_expired_draft_deadline_starts_no_subprocess(self):
        with tempfile.TemporaryDirectory() as tmp:
            calls = []

            def fake_run(*args, **kwargs):
                calls.append((args, kwargs))
                return night_shift.CmdResult("", 0, "", "")

            engine = night_shift.DraftEngine(fake_run, Path(tmp) / "worktrees", lambda: "now")
            result = engine.run_draft(
                Path(tmp),
                "owner/repo",
                {"key": "candidate", "verification": "true", "files": [], "summary": "test"},
                Path(tmp) / "ledger",
                900,
                "http://windows",
                "coder",
                deadline=night_shift.time.time() - 1,
                stop_file=Path(tmp) / "STOP",
            )
            self.assertEqual(result["status"], "REJECT")
            self.assertEqual(calls, [])

    def test_disposable_worktree_is_removed(self):
        with tempfile.TemporaryDirectory() as tmp:
            repo = Path(tmp) / "repo"
            worktree = Path(tmp) / "worktree"
            repo.mkdir()
            subprocess.run(["git", "init", "-q"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.email", "test@example.com"], cwd=repo, check=True)
            subprocess.run(["git", "config", "user.name", "Night Shift Test"], cwd=repo, check=True)
            (repo / "app.py").write_text("value = 1\n", encoding="utf-8")
            subprocess.run(["git", "add", "."], cwd=repo, check=True)
            subprocess.run(["git", "commit", "-qm", "initial"], cwd=repo, check=True)
            subprocess.run(["git", "worktree", "add", "--detach", str(worktree), "HEAD"], cwd=repo, check=True, stdout=subprocess.DEVNULL)
            self.assertTrue(night_shift.cleanup_isolated_worktree(repo, worktree))
            self.assertFalse(worktree.exists())


if __name__ == "__main__":
    unittest.main()
