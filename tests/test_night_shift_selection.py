import ast
import sys
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_selection import (
    declared_symbols,
    model_ready_tasks,
    model_task_readiness_reasons,
    relevant_tests_for_source,
    requests_coverage_work,
    task_selection_priority,
    unchecked_issue_actions,
)
from night_shift_feedback import apply_task_feedback


class SelectionTests(unittest.TestCase):
    def test_owner_aware_ast_gap_outranks_textual_coverage_absence(self):
        base = {
            "slug": "changed-file-proof-01", "kind": "tests",
            "ladder_priority": 300, "proof_kind": "test",
            "files": ["src/app.py", "tests/test_app.py"],
            "verification_commands": ["python3 -m unittest"],
        }
        textual = {**base, "evidence_sources": {
            "coverage-index/app.txt": "identifier_matches=0\nscan_complete=true"
        }}
        owned = {**base, "evidence_sources": {
            "coverage-index/app.txt": "identifier_matches=0\nscan_complete=true",
            "invocation-index/app.txt": (
                "owner=Engine\nanalysis=python-ast\nsymbol=run call_matches=0\nscan_complete=true"
            ),
        }}
        self.assertGreater(task_selection_priority(owned), task_selection_priority(textual))

    def test_python_symbols_exclude_nested_helpers(self):
        symbols = declared_symbols(
            "def public_function():\n"
            "    def nested_helper():\n"
            "        return 1\n"
            "    return nested_helper()\n\n"
            "class Service:\n"
            "    def run(self):\n"
            "        return 1\n"
            "    def _private(self):\n"
            "        return 2\n"
        )
        self.assertEqual(symbols, ["public_function", "Service", "run"])

    def test_python_symbols_include_top_level_conditional_declarations(self):
        symbols = declared_symbols(
            "try:\n"
            "    def fast_parse():\n"
            "        return 1\n"
            "except ImportError:\n"
            "    def fast_parse():\n"
            "        return 2\n"
            "if True:\n"
            "    async def optional_sync():\n"
            "        return 3\n"
        )
        self.assertEqual(symbols, ["fast_parse", "optional_sync"])

    def test_non_python_source_uses_regex_fallback(self):
        self.assertEqual(
            declared_symbols("export function parseThing() { return 1; }"),
            ["parseThing"],
        )

    def test_python_symbols_traverse_non_statement_scope_containers(self):
        class BranchContainer(ast.AST):
            _fields = ("body",)

            def __init__(self, body):
                self.body = body

        function = ast.FunctionDef(
            name="case_handler", args=ast.arguments(posonlyargs=[], args=[], kwonlyargs=[], kw_defaults=[], defaults=[]),
            body=[ast.Pass()], decorator_list=[], returns=None, type_comment=None,
        )
        tree = ast.Module(body=[BranchContainer([function])], type_ignores=[])
        with patch("night_shift_selection.ast.parse", return_value=tree):
            self.assertEqual(declared_symbols("match syntax on Python 3.10+"), ["case_handler"])

    def test_complete_coverage_outranks_broad_repair(self):
        broad = {"ladder_priority": 500}
        coverage = {
            "ladder_priority": 300,
            "files": ["src/auth/session.py"],
            "verification_commands": ["pytest"],
            "evidence_sources": {"coverage-index/session.txt": "scan_complete=true\nidentifier_matches=0"},
        }
        self.assertGreater(task_selection_priority(coverage), task_selection_priority(broad))

    def test_failed_ci_requires_complete_pinning_contract(self):
        partial = {
            "slug": "failed-ci-42", "proof_kind": "test", "ladder_priority": 500,
            "files": ["src/app.py"], "verification_commands": ["pytest"],
            "evidence_sources": {"run.log": "AssertionError"},
        }
        pinned = {**partial, "source_ref": "a" * 40}
        self.assertEqual(task_selection_priority(partial), 500)
        self.assertEqual(task_selection_priority(pinned), 1500)

    def test_exact_source_reference_beats_filename_overlap(self):
        contents = {
            "tests/test_session.py": "def test_session(): pass",
            "tests/test_misc.py": "# covers src/auth/session.py\ndef test_misc(): pass",
            "tests/test_other.py": "def test_other(): pass",
        }
        ranked = relevant_tests_for_source(
            "src/auth/session.py",
            list(contents),
            lambda path, _limit: contents[path],
        )
        self.assertEqual(ranked[0], "tests/test_misc.py")
        self.assertEqual(ranked[1], "tests/test_session.py")

    def test_equal_relevance_keeps_original_order(self):
        paths = ["tests/test_first.py", "tests/test_second.py"]
        self.assertEqual(
            relevant_tests_for_source("src/app.py", paths, lambda _path, _limit: ""),
            paths,
        )

    def test_feedback_preserves_evidence_first_selection_priority(self):
        mission = {
            "slug": "mission-brief", "ladder_priority": 500, "selection_priority": 500,
        }
        coverage = {
            "slug": "changed-file-proof-01", "ladder_priority": 300, "selection_priority": 800,
        }
        ranked, skipped = apply_task_feedback(
            [coverage, mission],
            [{"repo": "/repo", "family": "mission-brief", "verdict": "useful"}],
            "/repo",
            "night-shift",
        )
        self.assertEqual([row["slug"] for row in ranked], ["changed-file-proof-01", "mission-brief"])
        self.assertEqual(skipped, [])

    def test_coverage_intent_requires_an_action_not_a_negation_or_summary(self):
        self.assertTrue(requests_coverage_work("improve regression test coverage"))
        self.assertTrue(requests_coverage_work("testing needs a focused review"))
        self.assertFalse(requests_coverage_work("do not run tests; inspect the API issue"))
        self.assertFalse(requests_coverage_work("summarize the test results"))

    def test_normal_mode_rejects_trackers_but_afterburner_admits_them(self):
        task = {
            "slug": "issue-42-next-action",
            "kind": "issue",
            "files": ["src/app.py"],
            "verification_commands": ["pytest"],
            "signal": {"body": "- [ ] first\n- [ ] second"},
        }
        self.assertEqual(unchecked_issue_actions(task["signal"]), ["first", "second"])
        self.assertIn("2-item tracker", " ".join(model_task_readiness_reasons(task, "night-shift")))
        self.assertEqual(model_task_readiness_reasons(task, "afterburner"), [])

    def test_failed_ci_requires_pinned_concrete_log_evidence(self):
        healthy = {
            "slug": "failed-ci-42",
            "kind": "tests",
            "files": ["src/app.py"],
            "verification_commands": ["pytest"],
            "source_ref": "a" * 40,
            "evidence_sources": {"run.log": "src/app.py:9 AssertionError: failed"},
        }
        self.assertEqual(model_task_readiness_reasons(healthy, "night-shift"), [])
        unpinned = {**healthy, "source_ref": ""}
        self.assertIn("failed CI is not pinned", " ".join(model_task_readiness_reasons(unpinned, "night-shift")))
        vague = {**healthy, "evidence_sources": {"run.log": "workflow completed"}}
        self.assertIn("no concrete failure marker", " ".join(model_task_readiness_reasons(vague, "night-shift")))

    def test_ready_partition_is_stable_and_malformed_signals_are_safe(self):
        ready_task = {
            "slug": "issue-1-next-action",
            "kind": "issue",
            "files": ["src/app.py"],
            "verification_commands": ["pytest"],
            "signal": "not-json",
        }
        broad_task = {
            "slug": "source-map-1",
            "kind": "map",
            "files": ["src/app.py"],
            "verification_commands": ["git status --short"],
        }
        ready, skipped = model_ready_tasks([ready_task, broad_task], "night-shift")
        self.assertEqual(ready, [ready_task])
        self.assertEqual(skipped[0]["slug"], "source-map-1")
        self.assertEqual(skipped[0]["category"], "pre-model")


if __name__ == "__main__":
    unittest.main()
