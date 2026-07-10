import importlib.machinery
import importlib.util
import io
import json
import os
import subprocess
import sys
import tempfile
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
        output = """CLAIM: The package check does not run unit tests
EVIDENCE: scripts/check-package.sh:1 - the script only runs syntax and package checks
WHY_NOW: recent changes added scoring logic
BEST_NEXT_ACTION: run the unit suite from the package check
FILES_TO_TOUCH: scripts/check-package.sh
TESTS_TO_RUN: python3 -m unittest discover -s tests -p 'test_*.py'
EXPECTED_RESULT: all unit tests pass
ACTION_TYPE: patch-plan
SAFE_FOR_DRAFT_PR: yes
CONFIDENCE: high
"""
        self.assertEqual(night_shift.score_output(0, output, ["scripts/check-package.sh"]), "KEEP")

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
        self.assertNotEqual(score, "KEEP")

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
EVIDENCE: PACKAGE.md:1 - Confirm copyright year is right.
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


if __name__ == "__main__":
    unittest.main()
