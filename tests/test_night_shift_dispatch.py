import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from types import SimpleNamespace


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_dispatch import (
    correction_prompt,
    coverage_citation_examples,
    dispatch_one,
    has_pinned_task_evidence,
    select_best_attempt,
    should_retry_local_output,
)


# score_output can only ever return REJECT or MAYBE from a single worker
# response; KEEP is a later, deterministic promotion outside dispatch_one.
GOOD_OUTPUT = (
    "TASK_ID: task-1\n"
    "CLAIM: the helper always returns zero\n"
    "EVIDENCE: src/app.py:2 | return 0\n"
    "FILES_TO_TOUCH: src/app.py\n"
    "TESTS_TO_RUN: python -m pytest tests/test_app.py\n"
    "EXPECTED_RESULT: pytest passes\n"
    "RISK: low\n"
    "ACTION_TYPE: patch-plan\n"
    "SAFE_FOR_CODEX_TO_ATTEMPT: yes\n"
)

REJECT_OUTPUT = "ACTION_TYPE: issue\nSAFE_FOR_CODEX_TO_ATTEMPT: no\n"


def make_run_cmd(results):
    calls = []

    def run_cmd(args, timeout=None, env=None, pid_log=None):
        calls.append({"args": args, "timeout": timeout, "env": env, "pid_log": pid_log})
        return results[len(calls) - 1]

    run_cmd.calls = calls
    return run_cmd


class DispatchOneTests(unittest.TestCase):
    def _dispatch(self, results, **overrides):
        ledger = Path(tempfile.mkdtemp())
        self.addCleanup(shutil.rmtree, ledger, ignore_errors=True)
        (ledger / "artifacts").mkdir()
        run_cmd = make_run_cmd(results)
        kwargs = dict(
            lane="local",
            label="task-1",
            prompt="Inspect the gap.",
            ledger=ledger,
            mode="night-shift",
            run_cmd=run_cmd,
            delegate=Path("/usr/bin/maestro-delegate"),
            mode_defaults={
                "night-shift": {"local_max_tokens": 1536, "windows_max_tokens": 1536}
            },
            env={},
            parse_proof=lambda stderr: None,
            read_meta=lambda proof: {},
        )
        kwargs.update(overrides)
        outcome = dispatch_one(**kwargs)
        return outcome, run_cmd, ledger

    def test_retry_is_triggered_for_rejected_local_output(self):
        first = SimpleNamespace(rc=0, stdout=REJECT_OUTPUT, stderr="", timed_out=False)
        second = SimpleNamespace(rc=0, stdout=GOOD_OUTPUT, stderr="", timed_out=False)
        outcome, run_cmd, _ledger = self._dispatch([first, second])
        self.assertEqual(len(run_cmd.calls), 2)
        self.assertEqual(outcome["retry_count"], 1)
        self.assertEqual(outcome["score"], "MAYBE")
        self.assertEqual(outcome["label"], "task-1")
        self.assertIn("--label", run_cmd.calls[1]["args"])
        self.assertEqual(run_cmd.calls[1]["args"][run_cmd.calls[1]["args"].index("--label") + 1], "task-1-retry")

    def test_no_retry_when_first_attempt_already_passes(self):
        first = SimpleNamespace(rc=0, stdout=GOOD_OUTPUT, stderr="", timed_out=False)
        outcome, run_cmd, _ledger = self._dispatch([first])
        self.assertEqual(len(run_cmd.calls), 1)
        self.assertEqual(outcome["retry_count"], 0)
        self.assertEqual(outcome["score"], "MAYBE")

    def test_explicit_reject_action_never_retries(self):
        first = SimpleNamespace(rc=0, stdout="ACTION_TYPE: reject\n", stderr="", timed_out=False)
        outcome, run_cmd, _ledger = self._dispatch([first])
        self.assertEqual(len(run_cmd.calls), 1)
        self.assertEqual(outcome["retry_count"], 0)
        self.assertEqual(outcome["score"], "REJECT")

    def test_timeout_result_propagates_through_dispatch(self):
        first = SimpleNamespace(rc=124, stdout="", stderr="timed out after 900s", timed_out=True)
        outcome, run_cmd, _ledger = self._dispatch([first])
        self.assertEqual(len(run_cmd.calls), 1)
        self.assertTrue(outcome["timed_out"])
        self.assertEqual(outcome["rc"], 124)
        self.assertEqual(outcome["score"], "REJECT")
        self.assertEqual(outcome["retry_count"], 0)

    def test_artifact_files_are_written_with_preserved_names_and_keys(self):
        first = SimpleNamespace(rc=0, stdout=REJECT_OUTPUT, stderr="", timed_out=False)
        second = SimpleNamespace(rc=0, stdout=GOOD_OUTPUT, stderr="", timed_out=False)
        outcome, _run_cmd, ledger = self._dispatch([first, second])
        expected_keys = {
            "lane", "label", "rc", "timed_out", "seconds", "proof", "proofs",
            "artifact", "score", "priority", "tokens", "input_tokens", "output_tokens",
            "summary", "action_type", "evidence", "files", "tests", "expected_result",
            "quality_reasons", "source_ref", "retry_count", "output", "output_preview",
        }
        self.assertEqual(set(outcome.keys()), expected_keys)
        self.assertEqual(outcome["artifact"], str(ledger / "artifacts" / "task-1-local.md"))
        self.assertTrue((ledger / "artifacts" / "task-1-local.md").exists())
        self.assertTrue((ledger / "artifacts" / "task-1-local-attempt-1.md").exists())
        self.assertTrue((ledger / "artifacts" / "task-1-local-attempt-1.stderr.txt").exists())
        self.assertTrue((ledger / "artifacts" / "task-1-local-attempt-2.md").exists())
        self.assertTrue((ledger / "artifacts" / "task-1-local-attempt-2.stderr.txt").exists())
        self.assertEqual(
            (ledger / "artifacts" / "task-1-local.md").read_text(encoding="utf-8"),
            GOOD_OUTPUT.strip() + "\n",
        )

    def test_token_totals_are_summed_across_attempts(self):
        first = SimpleNamespace(rc=0, stdout=REJECT_OUTPUT, stderr="", timed_out=False)
        second = SimpleNamespace(rc=0, stdout=GOOD_OUTPUT, stderr="", timed_out=False)
        metas = [
            {"total_tokens_estimate": 100, "prompt_tokens_estimate": 60, "output_tokens_estimate": 40},
            {"total_tokens_estimate": 50, "prompt_tokens_estimate": 20, "output_tokens_estimate": 30},
        ]
        outcome, _run_cmd, _ledger = self._dispatch(
            [first, second], read_meta=lambda proof: metas.pop(0)
        )
        self.assertEqual(outcome["tokens"], 150)
        self.assertEqual(outcome["input_tokens"], 80)
        self.assertEqual(outcome["output_tokens"], 70)

    def test_unsafe_approval_output_is_not_retried(self):
        unsafe = (
            "ACTION_TYPE: patch-plan\n"
            "SAFE_FOR_CODEX_TO_ATTEMPT: yes\n"
            "You should push this to origin/main right away.\n"
        )
        first = SimpleNamespace(rc=0, stdout=unsafe, stderr="", timed_out=False)
        outcome, run_cmd, _ledger = self._dispatch([first])
        self.assertEqual(len(run_cmd.calls), 1)
        self.assertEqual(outcome["retry_count"], 0)
        self.assertEqual(outcome["score"], "REJECT")

    def test_env_defaults_are_set_without_overriding_existing_values(self):
        first = SimpleNamespace(rc=0, stdout=GOOD_OUTPUT, stderr="", timed_out=False)
        outcome, run_cmd, _ledger = self._dispatch(
            [first], env={"MAESTRO_LOCAL_MAX_TOKENS": "custom"}
        )
        self.assertEqual(run_cmd.calls[0]["env"]["MAESTRO_LOCAL_MAX_TOKENS"], "custom")
        self.assertEqual(run_cmd.calls[0]["env"]["MAESTRO_WINDOWS_MAX_TOKENS"], "1536")
        self.assertEqual(outcome["score"], "MAYBE")


class CorrectionPromptTests(unittest.TestCase):
    def test_correction_prompt_lists_exact_evidence_paths(self):
        prompt = correction_prompt(
            "Inspect the gap.",
            ["evidence path was not supplied to the worker"],
            ["bin/night_shift_drafts.py"],
            {"coverage-index/bin-night_shift_drafts.py-select_candidate.txt": "identifier_matches=0"},
            ["python3 -m unittest tests.test_night_shift"],
        )
        self.assertIn("- bin/night_shift_drafts.py", prompt)
        self.assertIn(
            "coverage-index/bin-night_shift_drafts.py-select_candidate.txt:1 | identifier_matches=0",
            prompt,
        )
        self.assertIn("- python3 -m unittest tests.test_night_shift", prompt)

    def test_coverage_citation_examples_only_indexes_coverage_paths(self):
        examples = coverage_citation_examples({
            "coverage-index/app.py-run.txt": "symbol=run\nidentifier_matches=0",
            "github-actions/run-1.log": "failure with a secret-looking value",
        })
        self.assertEqual(
            examples,
            ["coverage-index/app.py-run.txt:1 | symbol=run", "coverage-index/app.py-run.txt:2 | identifier_matches=0"],
        )


class RetryPolicyHelperTests(unittest.TestCase):
    def test_local_retry_only_repairs_rejected_output(self):
        valid = "ACTION_TYPE: issue\nSAFE_FOR_DRAFT_PR: no"
        self.assertFalse(should_retry_local_output("local", 0, "MAYBE", valid))
        self.assertFalse(should_retry_local_output("local", 0, "KEEP", valid))
        self.assertTrue(should_retry_local_output("local", 0, "REJECT", valid))
        self.assertFalse(should_retry_local_output("windows", 0, "REJECT", valid))
        self.assertTrue(should_retry_local_output("windows", 0, "REJECT", valid, True))
        self.assertFalse(should_retry_local_output("local", 0, "REJECT", "ACTION_TYPE: reject"))

    def test_pinned_issue_files_allow_one_windows_correction(self):
        self.assertTrue(has_pinned_task_evidence(["src/app.py"], "a" * 40, {}, True))
        self.assertTrue(has_pinned_task_evidence([], "", {"ci.log": "failed"}))
        self.assertFalse(has_pinned_task_evidence(["src/app.py"], "", {}))
        self.assertFalse(has_pinned_task_evidence(["src/app.py"], "a" * 40, {}, False))


class SelectBestAttemptTests(unittest.TestCase):
    def test_higher_score_wins_over_lower_score(self):
        attempts = [
            {"score": "REJECT", "res": SimpleNamespace(rc=0), "name": "first"},
            {"score": "KEEP", "res": SimpleNamespace(rc=0), "name": "second"},
        ]
        self.assertEqual(select_best_attempt(attempts)["name"], "second")

    def test_tie_in_score_prefers_lower_rc(self):
        attempts = [
            {"score": "MAYBE", "res": SimpleNamespace(rc=1), "name": "first"},
            {"score": "MAYBE", "res": SimpleNamespace(rc=0), "name": "second"},
        ]
        self.assertEqual(select_best_attempt(attempts)["name"], "second")

    def test_full_tie_prefers_later_corrected_attempt(self):
        attempts = [
            {"score": "REJECT", "res": SimpleNamespace(rc=0), "name": "original"},
            {"score": "REJECT", "res": SimpleNamespace(rc=0), "name": "corrected"},
        ]
        self.assertEqual(select_best_attempt(attempts)["name"], "corrected")
        attempts[0]["score"] = "MAYBE"
        self.assertEqual(select_best_attempt(attempts)["name"], "original")


if __name__ == "__main__":
    unittest.main()
