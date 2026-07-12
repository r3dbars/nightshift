import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_selection import declared_symbols, relevant_tests_for_source, task_selection_priority
from night_shift_feedback import apply_task_feedback


class SelectionTests(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
