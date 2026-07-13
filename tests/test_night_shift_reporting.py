import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "bin"))

from night_shift_reporting import ReportEngine


def result(label="tests-001", score="KEEP", lane="local", summary="Add focused test"):
    return {
        "label": label, "score": score, "lane": lane, "summary": summary,
        "output": "ACTION_TYPE: patch-plan\nTESTS_TO_RUN: python3 -m unittest",
        "artifact": f"/tmp/{label}.md", "tokens": 100, "input_tokens": 60,
        "output_tokens": 40, "rc": 0, "timed_out": False,
        "evidence": "src/app.py:1 | def app():", "files": ["src/app.py"],
        "tests": "python3 -m unittest", "expected_result": "tests pass",
    }


class ReportingTests(unittest.TestCase):
    def engine(self, feedback=None, states=None):
        return ReportEngine(
            load_feedback=lambda: feedback or [],
            run_cmd=lambda *args, **kwargs: None,
            token_reporter=Path("/bin/token-report"),
            narrow_task_files=lambda files: sorted(files),
            latest_states=lambda path: states or {},
        )

    def test_status_contract(self):
        engine = self.engine()
        self.assertEqual(engine.run_status([], 0, "GREEN"), "YELLOW")
        self.assertEqual(engine.run_status([result()], 100, "GREEN"), "GREEN")
        self.assertEqual(engine.run_status([result(score="MAYBE")], 100, "GREEN"), "YELLOW")
        self.assertEqual(engine.run_status([result()], 101, "GREEN", "afterburner"), "YELLOW")
        self.assertEqual(engine.run_status([result()], 0, "RED"), "RED")

    def test_metrics_and_lifecycle_use_injected_sources(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            engine = self.engine(
                feedback=[{"verdict": "useful"}],
                states={"a": {"state": "VERIFIED"}, "b": {"state": "REJECTED"}},
            )
            engine.write_outcome_metrics(ledger, [result()], [{"category": "pre-model"}, {"category": "repeat"}])
            engine.write_task_lifecycle_summary(ledger)
            metrics = json.loads((ledger / "outcome-metrics.json").read_text())
            self.assertEqual(metrics["accepted_candidates"], 1)
            self.assertEqual(metrics["human_feedback_events"], 1)
            self.assertEqual(metrics["cooldown_or_repeat_skips"], 1)
            lifecycle = (ledger / "task-lifecycle.md").read_text()
            self.assertIn("- VERIFIED: 1", lifecycle)
            self.assertIn("- REJECTED: 1", lifecycle)

    def test_harvest_and_work_queue_rank_and_dedupe(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            rows = [result("tests-001", lane="local"), result("tests-002", lane="windows")]
            engine = self.engine()
            engine.write_harvest(ledger, rows)
            items = engine.write_work_queue(ledger, rows)
            self.assertEqual(len(items), 1)
            self.assertEqual(items[0]["lanes"], ["local", "windows"])
            self.assertIn("KEEP: 2", (ledger / "harvest.md").read_text())
            queue = json.loads((ledger / "work-queue.json").read_text())
            self.assertEqual(queue[0]["supporting_artifacts"], 2)

    def test_morning_lists_keep_and_maybe(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            self.engine().write_morning(
                ledger, "quiet",
                [result("tests-001", "KEEP", summary="Keep this"), result("docs-001", "MAYBE", summary="Maybe this")],
                200, "GREEN",
            )
            brief = (ledger / "morning.md").read_text()
            self.assertIn("Keep this [KEEP]", brief)
            self.assertIn("Maybe this [MAYBE]", brief)
            self.assertIn("Deterministically proven worker findings:", brief)
            self.assertIn("Evidence-backed candidates that still need deterministic proof:", brief)

    def test_morning_falls_back_to_factual_scan(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            self.engine().write_morning(
                ledger, "quiet", [result(score="REJECT")], 100, "GREEN",
                {"status": "ok", "recent_files": ["README.md", "bin/night-shift"], "test_commands": ["python3 -m unittest"], "branch": "main", "head": "abc"},
            )
            brief = (ledger / "morning.md").read_text()
            self.assertIn("Recent code/test surface: README.md, bin/night-shift", brief)
            self.assertIn("Detected verification command", brief)

    def test_empty_grounded_run_does_not_blame_compute_setup(self):
        with tempfile.TemporaryDirectory() as tmp:
            ledger = Path(tmp)
            self.engine().write_morning(
                ledger, "night-shift", [], 100, "GREEN", {"status": "ok"}
            )
            brief = (ledger / "morning.md").read_text()
            self.assertIn("Status: YELLOW", brief)
            self.assertIn("Nothing had enough evidence", brief)
            self.assertNotIn("Fix the startup gate", brief)


if __name__ == "__main__":
    unittest.main()
